# Changelog

<!--next-version-placeholder-->

## v0.1.4 (20/10/2025)

### Changed
- **Documentation**: Updated mkdocs navigation to include new examples
- **Documentation**: Complete documentation site structure with all v0.1.2+ features

### Fixed  
- **Documentation**: Missing navigation entries for task replication and workflow examples

## v0.1.3 (20/10/2025)

### Added
- **Documentation**: Added comprehensive examples for task replication functionality
- **Documentation**: Added workflow classes usage examples with business process patterns
- **Documentation**: Enhanced Result module examples with new error handling methods

### Changed
- **Documentation**: Updated existing examples to showcase v0.1.2 features

## v0.1.2 (20/10/2025)

### Added
- **Missing Result methods**: Added `unwrap_err()`, `expect_err()`, `err_or()`, and `err_or_else()` methods to complete Rust-like Result API
- **Workflow classes**: Added `SyncWorkflow` and `AsyncWorkflow` as alternative namespaces inheriting from pipeline classes
- **Refactored pipeline structure**: Created separate `sync_pipeline.py` module for better code organization

### Changed
- **Import consistency**: Standardized all imports to use library-level imports (`neopipe.module`) instead of relative imports
- **Enhanced documentation**: Updated `CLAUDE.md` with comprehensive AI agent guidelines and import standards

### Fixed
- **Export completeness**: Added workflow classes to main package exports for consistent API access

## v0.1.0 (22/06/2024)

- First release of `neopipe`!