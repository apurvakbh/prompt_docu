"""
Helper functions for file operations — Sequential Thinking Pattern

This module contains utility functions for handling file I/O operations.
The primary entry-point is ``save_prompt_sequential`` which persists each
prompt/thought first (documentation before execution) — mirroring how
the ``sequentialthinking`` MCP tool works.
"""

import csv
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


# ═════════════════════════════════════════════════════════════════════════════
#  Sequential prompt save  (the core "save first" function)
# ═════════════════════════════════════════════════════════════════════════════

def save_prompt_sequential(
    file_path: Path,
    message: str,
    file_names: List[str],
    prompt_number: int,
    total_prompts: int,
    next_prompt_needed: bool,
    is_revision: bool = False,
    revises_prompt: Optional[int] = None,
    branch_from_prompt: Optional[int] = None,
    branch_id: Optional[str] = None,
    needs_more_prompts: bool = False,
) -> str:
    """
    Save a single sequential prompt entry to disk.

    This is the *first* thing executed on every ``document_prompt`` call —
    the documentation is persisted **before** any pipeline logic runs.

    The file format includes full sequential-thinking metadata so that
    later aggregation can reconstruct the entire thought chain.

    Args:
        file_path:           Destination path for the log entry.
        message:             The prompt / thinking-step text.
        file_names:          Files in context for this prompt.
        prompt_number:       Current 1-based sequence number.
        total_prompts:       Estimated total prompts (adjustable).
        next_prompt_needed:  Whether the chain continues after this.
        is_revision:         True if this revises a prior prompt.
        revises_prompt:      The prompt number being revised (if any).
        branch_from_prompt:  Branching-point prompt number (if any).
        branch_id:           Branch identifier string (if any).
        needs_more_prompts:  Dynamic extension flag.

    Returns:
        Human-readable confirmation string.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

    with open(file_path, 'w', encoding='utf-8') as f:
        # ── Header with sequence metadata ────────────────────────────────
        f.write(f"{'#' * 80}\n")
        f.write(f"#  SEQUENTIAL PROMPT  #{prompt_number} / {total_prompts}\n")
        f.write(f"#  Timestamp   : {timestamp}\n")
        f.write(f"#  Next needed : {next_prompt_needed}\n")
        if is_revision:
            f.write(f"#  Revision of : Prompt #{revises_prompt}\n")
        if branch_from_prompt:
            f.write(f"#  Branch from : Prompt #{branch_from_prompt}  (branch: {branch_id})\n")
        if needs_more_prompts:
            f.write(f"#  Extension   : More prompts requested beyond estimate\n")
        f.write(f"{'#' * 80}\n\n")

        # ── Prompt body ──────────────────────────────────────────────────
        f.write(f"[{timestamp}]\n")
        f.write(f"Prompt #{prompt_number}:\n")
        f.write(f"{message}\n\n")

        # ── Files in context ─────────────────────────────────────────────
        if file_names:
            f.write("Files in context:\n")
            for idx, name in enumerate(file_names, 1):
                f.write(f"  {idx}. {name}\n")
        else:
            f.write("Files in context: None\n")

        f.write(f"\n{'=' * 80}\n")

        # ── Machine-readable JSON block (for aggregation) ────────────────
        meta = {
            "promptNumber": prompt_number,
            "totalPrompts": total_prompts,
            "nextPromptNeeded": next_prompt_needed,
            "isRevision": is_revision,
            "revisesPrompt": revises_prompt,
            "branchFromPrompt": branch_from_prompt,
            "branchId": branch_id,
            "needsMorePrompts": needs_more_prompts,
            "timestamp": timestamp,
            "fileCount": len(file_names) if file_names else 0,
        }
        f.write(f"\n<!-- META: {json.dumps(meta)} -->\n")

    file_count = len(file_names) if file_names else 0
    return (
        f"Prompt #{prompt_number}/{total_prompts} saved to {file_path.name} "
        f"({file_count} file(s) in context)"
    )


# ═════════════════════════════════════════════════════════════════════════════
#  Legacy bulk-save  (used by the `save_all_prompts` utility tool)
# ═════════════════════════════════════════════════════════════════════════════

def save_prompt_to_file(file_path: Path, message: str, file_names: List[str]) -> str:
    """
    Save prompt message and file names to a log file (append mode).

    This is the simpler, non-sequential save used by ``save_all_prompts``
    to dump an entire session's worth of text into ``final_logs``.

    Args:
        file_path: Destination path.
        message:   The prompt / message text to save.
        file_names: List of file names / paths in context.

    Returns:
        Human-readable confirmation string.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'a', encoding='utf-8') as f:
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        f.write(f"[{timestamp}]\n")
        f.write(f"Prompt: {message}\n")
        if file_names:
            f.write("\nFiles in context:\n")
            for idx, file_name in enumerate(file_names, 1):
                f.write(f"  {idx}. {file_name}\n")
        else:
            f.write("\nFiles in context: None\n")
        f.write(f"{'=' * 80}\n\n")

    file_count = len(file_names) if file_names else 0
    return f"Your text has been saved to {file_path.name}! (Captured {file_count} file(s) in context)"


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


def clear_temp_logs_folder(temp_logs_dir: Path) -> str:
    """
    Clear all .txt files from the temp logs folder.
    
    Args:
        temp_logs_dir: Path to temp logs directory
        
    Returns:
        Success message with count of files deleted
    """
    if not temp_logs_dir.exists():
        return "Temp logs directory does not exist."
    
    txt_files = list(temp_logs_dir.rglob('*.txt'))
    
    if not txt_files:
        return "No .txt files found in temp logs folder."
    
    deleted_count = 0
    errors = []
    
    for txt_file in txt_files:
        try:
            os.remove(txt_file)
            deleted_count += 1
        except Exception as e:
            errors.append(f"Error deleting {txt_file.name}: {str(e)}")
    
    result_msg = f"Successfully deleted {deleted_count} file(s) from temp logs."
    if errors:
        result_msg += f"\n\nErrors encountered:\n" + "\n".join(errors)
    
    return result_msg


def clear_aggregate_logs_folder(aggregate_logs_dir: Path) -> str:
    """
    Clear all .txt files from the aggregate logs folder while preserving the CSV tracker.
    
    Args:
        aggregate_logs_dir: Path to aggregate logs directory
        
    Returns:
        Success message with count of files deleted
    """
    if not aggregate_logs_dir.exists():
        return "Aggregate logs directory does not exist."
    
    txt_files = list(aggregate_logs_dir.rglob('*.txt'))
    
    if not txt_files:
        return "No .txt files found in aggregate logs folder."
    
    deleted_count = 0
    errors = []
    
    for txt_file in txt_files:
        try:
            os.remove(txt_file)
            deleted_count += 1
        except Exception as e:
            errors.append(f"Error deleting {txt_file.name}: {str(e)}")
    
    result_msg = f"Successfully deleted {deleted_count} aggregate file(s). CSV tracker preserved."
    if errors:
        result_msg += f"\n\nErrors encountered:\n" + "\n".join(errors)
    
    return result_msg


def summarize_aggregate_files(aggregate_logs_dir: Path, final_logs_dir: Path) -> str:
    """
    Create a comprehensive summary of all aggregate files and save to final logs.
    
    Reads all aggregate .txt files, extracts key information about modified files,
    timestamps, and changes, then creates a summary document in final_logs.
    
    Args:
        aggregate_logs_dir: Path to aggregate logs directory
        final_logs_dir: Path to final logs directory
        
    Returns:
        Success message with summary details
    """
    if not aggregate_logs_dir.exists():
        return "Aggregate logs directory does not exist."
    
    aggregate_files = sorted(aggregate_logs_dir.glob('aggregate_*.txt'))
    
    if not aggregate_files:
        return "No aggregate files found to summarize."
    
    # Create summary
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    summary_file = final_logs_dir / f"aggregate_summary_{timestamp}.txt"
    
    all_modified_files = set()
    total_entries = 0
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        
        # Header
        f.write(f"{'#'*100}\n")
        f.write(f"#  AGGREGATE FILES SUMMARY\n")
        f.write(f"#  Generated: {now_str}\n")
        f.write(f"#  Total aggregate files processed: {len(aggregate_files)}\n")
        f.write(f"{'#'*100}\n\n")
        
        # Section 1: Overview of aggregate files
        f.write(f"{'='*100}\n")
        f.write(f"SECTION 1: AGGREGATE FILES OVERVIEW\n")
        f.write(f"{'='*100}\n\n")
        
        for idx, agg_file in enumerate(aggregate_files, 1):
            size = agg_file.stat().st_size
            mod_time = datetime.fromtimestamp(agg_file.stat().st_mtime, tz=timezone.utc)
            f.write(f"{idx}. {agg_file.name}\n")
            f.write(f"   Size: {size:,} bytes\n")
            f.write(f"   Created: {mod_time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
        
        # Section 2: Extract modified files from each aggregate
        f.write(f"\n{'='*100}\n")
        f.write(f"SECTION 2: FILES MODIFIED/REFERENCED ACROSS ALL AGGREGATES\n")
        f.write(f"{'='*100}\n\n")
        
        for agg_file in aggregate_files:
            f.write(f"\n{'-'*80}\n")
            f.write(f"From: {agg_file.name}\n")
            f.write(f"{'-'*80}\n\n")
            
            try:
                with open(agg_file, 'r', encoding='utf-8') as af:
                    content = af.read()
                    
                    # Extract files mentioned in "FILE:" sections
                    file_matches = re.findall(r'^FILE:\s*(.+)$', content, re.MULTILINE)
                    local_files = set(file_matches)
                    all_modified_files.update(local_files)
                    
                    # Count entries
                    entry_count = content.count('Point ')
                    total_entries += entry_count
                    
                    if local_files:
                        f.write(f"Files referenced ({len(local_files)}):\n")
                        for file_ref in sorted(local_files):
                            f.write(f"  - {file_ref}\n")
                    else:
                        f.write(f"No specific files referenced.\n")
                    
                    f.write(f"\nTotal prompt entries: {entry_count}\n")
            except Exception as e:
                f.write(f"Error reading {agg_file.name}: {str(e)}\n")
        
        # Section 3: Unique files summary
        f.write(f"\n\n{'='*100}\n")
        f.write(f"SECTION 3: ALL UNIQUE FILES MODIFIED/REFERENCED\n")
        f.write(f"{'='*100}\n\n")
        f.write(f"Total unique files: {len(all_modified_files)}\n\n")
        
        for file_ref in sorted(all_modified_files):
            f.write(f"  - {file_ref}\n")
        
        # Section 4: Statistics
        f.write(f"\n\n{'='*100}\n")
        f.write(f"SECTION 4: SUMMARY STATISTICS\n")
        f.write(f"{'='*100}\n\n")
        f.write(f"Total aggregate files: {len(aggregate_files)}\n")
        f.write(f"Total unique files referenced: {len(all_modified_files)}\n")
        f.write(f"Total prompt entries across all aggregates: {total_entries}\n")
        
        # Section 5: Modified files list for tracking
        f.write(f"\n\n{'='*100}\n")
        f.write(f"SECTION 5: AGGREGATE FILES INCLUDED IN THIS SUMMARY\n")
        f.write(f"{'='*100}\n\n")
        
        for agg_file in aggregate_files:
            f.write(f"  - {agg_file.name}\n")
    
    return (
        f"Successfully created summary of {len(aggregate_files)} aggregate file(s). "
        f"Found {len(all_modified_files)} unique file(s) referenced across {total_entries} prompt entries. "
        f"Summary saved to {summary_file.name}"
    )


def create_readme_from_final(final_logs_dir: Path, prompt_logs_dir: Path) -> str:
    """
    Create a comprehensive README.md file using all data from final logs folder.
    
    Reads all files in final_logs and creates a structured README with:
    - Project overview
    - File descriptions
    - Usage statistics
    - Workflow documentation
    
    Args:
        final_logs_dir: Path to final logs directory
        prompt_logs_dir: Path to base prompt logs directory (for context)
        
    Returns:
        Success message with README details
    """
    if not final_logs_dir.exists():
        return "Final logs directory does not exist."
    
    final_files = sorted(final_logs_dir.glob('*.txt'))
    
    if not final_files:
        return "No final log files found to create README from."
    
    # Create README
    readme_file = prompt_logs_dir / "README.md"
    
    with open(readme_file, 'w', encoding='utf-8') as f:
        now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        
        # Title and intro
        f.write(f"# Prompt Documentation - Project README\n\n")
        f.write(f"**Generated:** {now_str}\n\n")
        f.write(f"---\n\n")
        
        # Overview
        f.write(f"## 📋 Overview\n\n")
        f.write(f"This README was automatically generated from the prompt documentation system. ")
        f.write(f"It provides a comprehensive overview of all logged prompts, aggregations, and summaries.\n\n")
        
        # Directory structure
        f.write(f"## 📂 Directory Structure\n\n")
        f.write(f"```\n")
        f.write(f"prompt_logs/\n")
        f.write(f"├── temp_logs/        # Temporary prompt logs (cleared after aggregation)\n")
        f.write(f"├── final_logs/       # Finalized prompt logs and summaries\n")
        f.write(f"├── aggregate_logs/   # Aggregated reports with detailed analysis\n")
        f.write(f"└── README.md         # This file\n")
        f.write(f"```\n\n")
        
        # Final logs overview
        f.write(f"## 📊 Final Logs Summary\n\n")
        f.write(f"Total files in final_logs: **{len(final_files)}**\n\n")
        
        # List each file with details
        f.write(f"### Files in final_logs:\n\n")
        
        for idx, final_file in enumerate(final_files, 1):
            size = final_file.stat().st_size
            mod_time = datetime.fromtimestamp(final_file.stat().st_mtime, tz=timezone.utc)
            
            f.write(f"{idx}. **{final_file.name}**\n")
            f.write(f"   - Size: {size:,} bytes\n")
            f.write(f"   - Created: {mod_time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
            
            # Try to extract some context from the file
            try:
                with open(final_file, 'r', encoding='utf-8') as ff:
                    content = ff.read(500)  # Read first 500 chars
                    if 'SUMMARY' in content or 'Summary' in content:
                        f.write(f"   - Type: Summary Report\n")
                    elif 'all_prompts' in final_file.name:
                        f.write(f"   - Type: Complete Prompt Log\n")
                    else:
                        f.write(f"   - Type: Log File\n")
            except:
                pass
            
            f.write(f"\n")
        
        # Workflow documentation
        f.write(f"## 🔄 Workflow\n\n")
        f.write(f"1. **Save Current Prompt**: Individual prompts are saved to `temp_logs/`\n")
        f.write(f"2. **Save All Prompts**: Complete session logs are saved to `final_logs/`\n")
        f.write(f"3. **Aggregate Prompts**: Temp logs are analyzed and aggregated into `aggregate_logs/`\n")
        f.write(f"4. **Summarize Aggregates**: Summaries are created from aggregates and saved to `final_logs/`\n")
        f.write(f"5. **Generate README**: This README is created from final logs\n\n")
        
        # Tools available
        f.write(f"## 🛠️ Available Tools\n\n")
        f.write(f"- `save_current_prompt` - Save current prompt to temp logs\n")
        f.write(f"- `save_all_prompts` - Save all session prompts to final logs\n")
        f.write(f"- `aggregate_prompts` - Aggregate temp logs into structured reports\n")
        f.write(f"- `clear_temp_logs` - Clear all temporary log files\n")
        f.write(f"- `clear_aggregate_logs` - Clear all aggregate log files\n")
        f.write(f"- `summarize_aggregates` - Create summary from aggregate files\n")
        f.write(f"- `create_readme` - Generate this README file\n\n")
        
        # Statistics
        f.write(f"## 📈 Statistics\n\n")
        total_size = sum(f.stat().st_size for f in final_files)
        f.write(f"- Total files in final_logs: {len(final_files)}\n")
        f.write(f"- Total storage used: {total_size:,} bytes ({total_size/1024:.2f} KB)\n")
        
        # Footer
        f.write(f"\n---\n\n")
        f.write(f"*This README was automatically generated by the Prompt Documentation MCP Server.*\n")
    
    return f"Successfully created README.md with information from {len(final_files)} final log file(s). README saved to {readme_file}"

