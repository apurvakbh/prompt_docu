"""
Helper functions for file operations

This module contains utility functions for handling file I/O operations.
"""

import csv
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Tuple


def save_prompt_to_file(file_path: Path, message: str, file_names: List[str]) -> str:
    """
    Save prompt message and file names to a log file.
    
    Args:
        file_path: Path object pointing to the file where data should be saved
        message: The prompt/message text to save
        file_names: List of file names/paths in context
        
    Returns:
        Success message with file count
    """
    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'a', encoding='utf-8') as f:
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        
        f.write(f"[{timestamp}]\n")
        f.write(f"Prompt: {message}\n")
        
        if file_names:
            f.write(f"\nFiles in context:\n")
            for idx, file_name in enumerate(file_names, 1):
                f.write(f"  {idx}. {file_name}\n")
        else:
            f.write(f"\nFiles in context: None\n")
        
        f.write(f"{'='*80}\n\n")
    
    file_count = len(file_names) if file_names else 0
    return f"Your text has been saved to {file_path.name}! (Captured {file_count} file(s) in context)"


def get_daily_folder_path(base_path: Path) -> Path:
    """
    Get the daily folder path based on current UTC date.
    
    Args:
        base_path: Base directory path
        
    Returns:
        Path to the daily folder (YYYY-MM-DD format)
    """
    date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    daily_path = base_path / date_str
    daily_path.mkdir(parents=True, exist_ok=True)
    return daily_path


def aggregate_prompts(temp_logs_dir: Path, aggregate_logs_dir: Path) -> str:
    """
    Aggregate all un-aggregated prompt files from temp logs directory.
    
    Reads all .txt files from temp_logs that haven't been aggregated yet
    (tracked via CSV), parses each file to extract prompts and file references,
    creates detailed aggregate points per file, and saves to aggregate_logs.
    
    Args:
        temp_logs_dir: Path to temp logs directory
        aggregate_logs_dir: Path to aggregate logs directory
        
    Returns:
        Success message with details
    """
    aggregate_logs_dir.mkdir(parents=True, exist_ok=True)
    csv_file = aggregate_logs_dir / "aggregation_tracker.csv"
    
    # Step 1: Read CSV to find already-aggregated files
    already_aggregated = _get_aggregated_files(csv_file)
    
    # Step 2: Find all .txt files in temp_logs that are NOT yet aggregated
    all_txt_files = sorted(temp_logs_dir.rglob('*.txt'))
    new_files = [
        f for f in all_txt_files
        if str(f.relative_to(temp_logs_dir)) not in already_aggregated
    ]
    
    if not new_files:
        return "No new (un-aggregated) prompt files found in temp logs directory."
    
    # Step 3: Parse each file to extract structured prompt entries
    all_entries: List[Dict] = []
    for txt_file in new_files:
        entries = _parse_prompt_file(txt_file, temp_logs_dir)
        all_entries.extend(entries)
    
    # Step 4: Group entries by files_in_context to build per-file aggregate points
    file_points = _build_aggregate_points(all_entries)
    
    # Step 5: Write the aggregate report
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    aggregate_file = aggregate_logs_dir / f"aggregate_{timestamp}.txt"
    _write_aggregate_report(aggregate_file, new_files, all_entries, file_points, temp_logs_dir)
    
    # Step 6: Update CSV tracker with newly aggregated files
    _update_csv_tracker(csv_file, new_files, aggregate_file, temp_logs_dir)
    
    return (
        f"Successfully aggregated {len(new_files)} new file(s) "
        f"({len(all_entries)} prompt entries) into {aggregate_file.name}. "
        f"CSV tracker updated in aggregation_tracker.csv."
    )


def _get_aggregated_files(csv_file: Path) -> set:
    """
    Read the aggregation tracker CSV and return a set of
    already-aggregated temp file relative paths.
    
    Args:
        csv_file: Path to the aggregation_tracker.csv
        
    Returns:
        Set of relative path strings that have been aggregated
    """
    aggregated = set()
    if not csv_file.exists():
        return aggregated
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('aggregated', '').lower() == 'true':
                aggregated.add(row.get('temp_file_path', ''))
    
    return aggregated


def _parse_prompt_file(file_path: Path, temp_logs_dir: Path) -> List[Dict]:
    """
    Parse a single prompt log file into structured entries.
    
    Each entry in the file is delimited by a line of '=' characters.
    Format per entry:
        [YYYY-MM-DD HH:MM:SS UTC]
        Prompt: <text>
        
        Files in context:
          - file1.py
          - file2.py
        ====...====
    
    Args:
        file_path: Path to the prompt file
        temp_logs_dir: Base temp logs directory (for relative path calculation)
        
    Returns:
        List of dicts with keys: timestamp, prompt, files, source_file
    """
    entries = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return entries
    
    # Split by the separator line (80+ '=' chars)
    raw_blocks = re.split(r'={40,}\s*', content)
    
    for block in raw_blocks:
        block = block.strip()
        if not block:
            continue
        
        entry = {
            'timestamp': '',
            'prompt': '',
            'files': [],
            'source_file': str(file_path.relative_to(temp_logs_dir))
        }
        
        # Extract timestamp
        ts_match = re.search(r'\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*UTC?)\]', block)
        if ts_match:
            entry['timestamp'] = ts_match.group(1).strip()
        
        # Extract prompt text
        prompt_match = re.search(r'Prompt:\s*(.*?)(?=\nFiles in context:|\Z)', block, re.DOTALL)
        if prompt_match:
            entry['prompt'] = prompt_match.group(1).strip()
        
        # Extract files in context
        files_section = re.search(r'Files in context:\s*(.*)', block, re.DOTALL)
        if files_section:
            file_text = files_section.group(1).strip()
            if file_text.lower() != 'none':
                file_lines = re.findall(r'-\s+(.+)', file_text)
                entry['files'] = [f.strip() for f in file_lines]
        
        # Only add if there's actual content
        if entry['prompt'] or entry['files']:
            entries.append(entry)
    
    return entries


def _build_aggregate_points(entries: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Build aggregate points grouped by each file referenced in context.
    
    For each unique file mentioned across all prompt entries, creates
    a chronological list of aggregate points describing what was requested
    regarding that file and what changes were implied.
    
    Args:
        entries: List of parsed prompt entries
        
    Returns:
        Dict mapping file_path -> list of aggregate point dicts
    """
    file_points: Dict[str, List[Dict]] = {}
    
    for entry in entries:
        # For each file referenced in this prompt entry
        if entry['files']:
            for file_ref in entry['files']:
                if file_ref not in file_points:
                    file_points[file_ref] = []
                
                file_points[file_ref].append({
                    'timestamp': entry['timestamp'],
                    'action': _extract_action_summary(entry['prompt'], file_ref),
                    'full_prompt': entry['prompt'],
                    'source_file': entry['source_file'],
                    'other_files_in_context': [
                        f for f in entry['files'] if f != file_ref
                    ]
                })
        else:
            # Prompts with no file context go under a general bucket
            general_key = '[NO FILES IN CONTEXT]'
            if general_key not in file_points:
                file_points[general_key] = []
            file_points[general_key].append({
                'timestamp': entry['timestamp'],
                'action': _extract_action_summary(entry['prompt'], ''),
                'full_prompt': entry['prompt'],
                'source_file': entry['source_file'],
                'other_files_in_context': []
            })
    
    return file_points


def _extract_action_summary(prompt: str, file_ref: str) -> str:
    """
    Extract a concise action summary from the prompt text
    that describes what was requested regarding the given file.
    
    Args:
        prompt: The full prompt text
        file_ref: The file being referenced
        
    Returns:
        A summary string describing the action
    """
    # Truncate very long prompts for the summary line
    # but keep enough for context
    max_summary_len = 300
    
    # Try to find sentences that mention the file
    if file_ref:
        file_name = Path(file_ref).name
        # Look for sentences containing the file name
        sentences = re.split(r'[.!?\n]', prompt)
        relevant = [s.strip() for s in sentences if file_name.lower() in s.lower()]
        if relevant:
            summary = '. '.join(relevant[:3])
            if len(summary) > max_summary_len:
                return summary[:max_summary_len] + '...'
            return summary
    
    # Fallback: use first N characters of prompt
    if len(prompt) > max_summary_len:
        return prompt[:max_summary_len] + '...'
    return prompt


def _write_aggregate_report(
    aggregate_file: Path,
    source_files: List[Path],
    all_entries: List[Dict],
    file_points: Dict[str, List[Dict]],
    temp_logs_dir: Path
) -> None:
    """
    Write the full aggregate report to a file.
    
    Args:
        aggregate_file: Output file path
        source_files: List of source temp files processed
        all_entries: All parsed prompt entries
        file_points: Aggregate points grouped by file
        temp_logs_dir: Base temp logs directory
    """
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    
    with open(aggregate_file, 'w', encoding='utf-8') as f:
        # Header
        f.write(f"{'#'*100}\n")
        f.write(f"#  AGGREGATED PROMPTS REPORT\n")
        f.write(f"#  Generated: {now_str}\n")
        f.write(f"#  Source files processed: {len(source_files)}\n")
        f.write(f"#  Total prompt entries: {len(all_entries)}\n")
        f.write(f"#  Unique files referenced: {len(file_points)}\n")
        f.write(f"{'#'*100}\n\n")
        
        # Section 1: Source files summary
        f.write(f"{'='*100}\n")
        f.write(f"SECTION 1: SOURCE FILES PROCESSED\n")
        f.write(f"{'='*100}\n\n")
        for idx, src_file in enumerate(source_files, 1):
            rel_path = src_file.relative_to(temp_logs_dir)
            size = src_file.stat().st_size
            f.write(f"  {idx}. {rel_path}  ({size} bytes)\n")
        f.write(f"\n")
        
        # Section 2: Detailed aggregate points per file
        f.write(f"{'='*100}\n")
        f.write(f"SECTION 2: AGGREGATE POINTS PER FILE\n")
        f.write(f"{'='*100}\n\n")
        f.write(f"Below is a detailed breakdown of every file referenced in the\n")
        f.write(f"prompts, along with chronological aggregate points describing\n")
        f.write(f"what was requested and what changes were made.\n\n")
        
        for file_ref, points in sorted(file_points.items()):
            f.write(f"\n{'─'*100}\n")
            f.write(f"FILE: {file_ref}\n")
            f.write(f"Total references: {len(points)}\n")
            f.write(f"{'─'*100}\n\n")
            
            for pt_idx, point in enumerate(points, 1):
                f.write(f"  Point {pt_idx}:\n")
                f.write(f"    Timestamp  : {point['timestamp']}\n")
                f.write(f"    Source     : {point['source_file']}\n")
                f.write(f"    Action     : {point['action']}\n")
                if point['other_files_in_context']:
                    f.write(f"    Also with  : {', '.join(point['other_files_in_context'])}\n")
                f.write(f"    Full prompt:\n")
                # Indent the full prompt for readability
                for line in point['full_prompt'].split('\n'):
                    f.write(f"      | {line}\n")
                f.write(f"\n")
        
        # Section 3: Full raw content of each source file
        f.write(f"\n{'='*100}\n")
        f.write(f"SECTION 3: RAW CONTENT OF SOURCE FILES\n")
        f.write(f"{'='*100}\n\n")
        
        for idx, src_file in enumerate(source_files, 1):
            try:
                with open(src_file, 'r', encoding='utf-8') as src_f:
                    content = src_f.read()
                
                rel_path = src_file.relative_to(temp_logs_dir)
                f.write(f"\n{'─'*100}\n")
                f.write(f"RAW FILE {idx}/{len(source_files)}: {rel_path}\n")
                f.write(f"Size: {src_file.stat().st_size} bytes\n")
                f.write(f"{'─'*100}\n\n")
                f.write(content)
                f.write(f"\n")
            except Exception as e:
                f.write(f"  Error reading {src_file.name}: {str(e)}\n\n")


def _update_csv_tracker(
    csv_file: Path,
    source_files: List[Path],
    aggregate_file: Path,
    temp_logs_dir: Path
) -> None:
    """
    Update the aggregation tracker CSV with newly aggregated files.
    
    CSV columns:
        temp_file_path, file_size_bytes, aggregated, aggregation_timestamp, aggregate_output_file
    
    Args:
        csv_file: Path to aggregation_tracker.csv
        source_files: List of temp files that were aggregated
        aggregate_file: The output aggregate file
        temp_logs_dir: Base temp logs directory
    """
    csv_exists = csv_file.exists()
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    
    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header if file is new
        if not csv_exists:
            writer.writerow([
                'temp_file_path',
                'file_size_bytes',
                'aggregated',
                'aggregation_timestamp',
                'aggregate_output_file'
            ])
        
        # Write one row per source file
        for src_file in source_files:
            rel_path = str(src_file.relative_to(temp_logs_dir))
            size = src_file.stat().st_size
            writer.writerow([
                rel_path,
                size,
                'True',
                now_str,
                aggregate_file.name
            ])
