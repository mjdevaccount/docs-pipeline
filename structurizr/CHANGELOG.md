# Changelog - Structurizr Tools

All notable changes to the Structurizr CLI Python wrapper will be documented in this file.

---

## [2.0.0] - November 2025

### Added - Production Polish

- **Output directory creation** - Automatically creates missing output directories
- **Config file validation** - Validates structure, required fields, and file existence
- **Init command** - Generates template configuration files
- **Verbose mode** - `--verbose` / `-v` flag for debugging output
- **Dry run mode** - `--dry-run` flag to preview actions without executing
- **Enhanced export summary** - Shows file counts and sizes for each format
- **Parallel export** - Configurable concurrent export for multiple formats
- **Enhanced error messages** - Suggests similar files when workspace not found
- **Docker image version pinning** - Supports and validates version tags

### Changed

- Improved error handling throughout
- Better path resolution for edge cases
- Enhanced validation with helpful suggestions

---

## [1.0.0] - November 2025

### Added

- **Initial release** with comprehensive code review improvements
- **Critical fixes:**
  - Windows path normalization for Docker volume mounts
  - Workspace directory extraction from DSL file path
  - Proper Structurizr Lite environment variable configuration
  - Output directory relative path handling
  
- **Enhancements:**
  - Progress indication with animated spinner
  - Batch export with error recovery
  - Validation before export (configurable)
  - Watch mode for live updates (requires watchdog package)
  - Improved config file schema with options

- **Features:**
  - Cross-platform support (Windows, Linux, macOS)
  - Docker-based execution (no local install required)
  - Configuration file support
  - Colored terminal output (with graceful fallback)
  - Comprehensive error handling

### Fixed

- Volume mount path resolution for Windows
- Workspace path extraction from DSL file location
- Structurizr Lite environment variable setup
- Output directory path handling in containers
- Import errors when optional packages missing

---

## Future Enhancements

- [ ] Integration with Pandoc workflow
- [ ] Diagram diffing to detect changes
- [ ] Auto-generate table of contents
- [ ] Parallel export for multiple formats
- [ ] Cleanup old export files
- [ ] Auto-open browser for serve command

---

**Version:** 1.0.0  
**Status:** Production-ready

