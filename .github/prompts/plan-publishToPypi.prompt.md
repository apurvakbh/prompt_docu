# Plan: Publish prompt_docu to PyPI

This plan will set up all necessary packaging infrastructure to publish the prompt_docu MCP server to PyPI, making it installable via `pip install prompt-docu`. The package currently lacks all PyPI packaging files (pyproject.toml, MANIFEST.in, versioning) but has excellent documentation and a clean structure.

**Key Decisions:**
- PyPI name: `prompt-docu` (hyphenated, import as `prompt_docu`)
- Python support: 3.8+ (broader compatibility using tomli fallback)  
- Build backend: setuptools (standard, well-supported)
- Initial version: 0.1.0
- Author: Apurva Bhatt <response2apurva@yahoo.com>

**Steps**

1. **Create [pyproject.toml](pyproject.toml)** at project root
   - Define build system (setuptools, wheel)
   - Add project metadata: name `prompt-docu`, version `0.1.0`, author, description, license (GPL-3.0)
   - Specify dependencies: `mcp` and `tomli` for Python <3.11
   - Set Python requirement: `>=3.8`
   - Add console script entry point: `prompt-docu = "prompt_docu.main:main"`
   - Include classifiers for PyPI (GPL license, Python versions, development status Alpha)
   - Use README.md as long_description
   - Add project URLs (if repository exists on GitHub)

2. **Create [MANIFEST.in](MANIFEST.in)** at project root
   - Include [config.toml](config.toml) in distribution
   - Include [LICENSE](LICENSE) and [README.md](README.md)
   - Ensure non-Python files are bundled

3. **Update [src/\_\_init\_\_.py](src/__init__.py)**
   - Add `__version__ = "0.1.0"` at top
   - Verify `__all__` exports include necessary symbols

4. **Update [main.py](main.py#L54)** for production readiness
   - Change server name from `"example-mcp-server"` to `"prompt-docu-server"`
   - Optionally improve config loading to handle packaged installation (use importlib.resources for fallback)

5. **Update [README.md](README.md)** with installation section
   - Add "Installation" section with `pip install prompt-docu`
   - Include MCP client configuration example (Claude Desktop config snippet)
   - Show how to run: `prompt-docu` command

6. **Build the package locally**
   - Install build tools: `pip install build twine`
   - Run: `python -m build` (creates dist/ with .whl and .tar.gz)
   - Verify package contents with `tar -tzf dist/prompt-docu-0.1.0.tar.gz`

7. **Test on TestPyPI** (recommended before production)
   - Create account at test.pypi.org
   - Upload: `python -m twine upload --repository testpypi dist/*`
   - Test install: `pip install --index-url https://test.pypi.org/simple/ prompt-docu`
   - Verify the tool runs and config.toml is included

8. **Publish to production PyPI**
   - Create account at pypi.org
   - Upload: `python -m twine upload dist/*`
   - Verify package appears at pypi.org/project/prompt-docu

9. **Post-publication verification**
   - Install in fresh environment: `pip install prompt-docu`
   - Test running: `prompt-docu` command
   - Verify MCP server starts without errors
   - Check config.toml is accessible and directories are created

**Verification**

- Local build succeeds without errors
- Package includes config.toml when extracted (`tar -tzf`)
- TestPyPI installation works and server runs
- Production PyPI page shows correct metadata and README
- Fresh pip install creates working `prompt-docu` command

**Notes**
- Consider creating a GitHub tag/release for v0.1.0 after publication
- Future updates require version bumps in [src/\_\_init\_\_.py](src/__init__.py) and rebuilding
- MCP dependency version should be pinned or ranged based on compatibility testing
