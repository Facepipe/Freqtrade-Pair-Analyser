# Changelog

All notable changes to Freqtrade Pair Analyzer will be documented in this file.

## [2.0.0] - 2025-01-03

### 🔧 Fixed
- **MAJOR:** Resolved "no valid pairs found" issue that prevented analysis
- Fixed import path inconsistencies causing module not found errors  
- Fixed missing version attribute errors in save_results method
- Corrected config handler path resolution for subdirectory structure

### ✨ Added
- Comprehensive error handling and data validation throughout codebase
- Multi-timeframe volatility calculations with proper annualization
- Enhanced debug and testing utilities (debug_script.py, test_analyzer.py)
- Detailed results display with volatility, trend, and volume metrics
- Automatic directory creation and permission checking
- Version management system with centralized version info

### 📈 Improved
- Enhanced AnalysisEngine with robust error handling for all indicators
- Better data quality validation and filtering
- More informative logging and progress reporting  
- Improved JSON report structure with comprehensive metadata

### 🏗️ Changed
- Consolidated duplicate VersionedAnalyzer implementations
- Moved from placeholder analyzer_core to working data_handler implementation
- Restructured utils package with proper __init__.py

## [1.4.0] - 2024-12-15

### ✨ Added
- Configurable number of top and least volatile pairs to display
- Timeframe support via command line interface
- Enhanced CLI with more granular control options

## [1.3.0] - 2024-12-01

### ✨ Added
- Automatic data downloading capability through freqtrade
- Enhanced market data retrieval and validation

## [1.0.0] - 2024-10-15

### ✨ Added
- Initial release of Freqtrade Pair Analyzer
- Basic pair analysis functionality
- Technical indicator calculations (ADX, Volatility, Volume)
- JSON report generation
- Command line interface
