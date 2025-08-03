#!/bin/bash

# Script to create README and essential files (preserving existing .gitignore)
# Run this from your pair_analyzer directory

echo "🚀 Creating project documentation (preserving existing .gitignore)..."

# Create comprehensive README.md
echo "📖 Creating README.md..."
cat > README.md << 'EOF'
# 🚀 Freqtrade Pair Analyzer Pro

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![Freqtrade](https://img.shields.io/badge/freqtrade-2024%2B-green.svg)](https://freqtrade.io)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.0.0-brightgreen.svg)](CHANGELOG.md)

> Advanced cryptocurrency pair analysis and ranking tool for Freqtrade trading bot

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [Configuration](#-configuration)
- [Output](#-output)
- [Troubleshooting](#-troubleshooting)
- [Development](#-development)
- [Contributing](#-contributing)

## 🎯 Overview

Freqtrade Pair Analyzer Pro is a sophisticated analysis tool that evaluates cryptocurrency trading pairs using multiple technical indicators and market metrics. It helps traders identify the most promising pairs for their Freqtrade strategies by analyzing:

- **Volatility patterns** - Risk and opportunity assessment
- **Trend strength** - Market momentum analysis using ADX
- **Volume characteristics** - Liquidity and market interest
- **Technical indicators** - Coral Trend and Schaff Trend Cycle
- **Composite scoring** - Weighted ranking system

## ✨ Features

### 🔍 **Advanced Analysis**
- Multi-timeframe support (1m to 1w)
- Parallel processing for fast analysis
- Comprehensive technical indicator calculations
- Data quality validation and filtering

### 📊 **Intelligent Scoring**
- Weighted composite scoring system
- Customizable ranking criteria
- Top performers and least volatile pairs identification
- Statistical summary reports

### 🛠 **Robust Architecture**
- Automatic data downloading via Freqtrade
- Intelligent configuration detection
- Comprehensive error handling and logging
- Modular, extensible design

### 📈 **Rich Output**
- Detailed JSON reports with metadata
- Terminal-based results summary
- Historical analysis tracking
- Export capabilities

## 🚀 Installation

### Prerequisites

- **Python 3.8+** (recommended: 3.10+)
- **Freqtrade** installed and configured
- **TA-Lib** for technical analysis

### 1. Install Freqtrade (if not already installed)

```bash
# Using pip
pip install freqtrade[all]

# Or using conda
conda install -c conda-forge freqtrade
```

### 2. Install TA-Lib

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install build-essential
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
pip install TA-Lib
```

**macOS:**
```bash
brew install ta-lib
pip install TA-Lib
```

### 3. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/Facepipe/Freqtrade-Pair-Analyser.git
cd Freqtrade-Pair-Analyser

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python test_analyzer.py
```

## 🏃‍♂️ Quick Start

### 1. **Basic Analysis**

```bash
# Analyze USDT pairs with default settings
python pair_analyzer.py --quote USDT

# Analyze with specific timeframe
python pair_analyzer.py --quote USDT --timeframe 1h --workers 4
```

### 2. **Advanced Analysis**

```bash
# Comprehensive analysis with custom parameters
python pair_analyzer.py \
  --quote USDT \
  --timeframe 15m \
  --top-pairs 20 \
  --least-pairs 10 \
  --workers 8 \
  --days 30 \
  --verbose
```

### 3. **Quick Test**

```bash
# Test your setup
python test_analyzer.py

# Debug configuration issues
python debug_script.py
```

## 📖 Usage

### Command Line Options

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--quote` | Quote currency (REQUIRED) | - | `USDT`, `BTC`, `ETH` |
| `--timeframe` | Analysis timeframe | `1d` | `1m`, `5m`, `15m`, `1h`, `4h`, `1d` |
| `--workers` | Parallel workers (1-16) | `4` | `8` |
| `--top-pairs` | Top pairs to show | `10` | `20` |
| `--least-pairs` | Least volatile pairs | `10` | `5` |
| `--days` | Days of data to analyze | `90` | `30`, `180` |
| `--verbose` | Enable debug logging | `False` | - |

### Usage Examples

```bash
# 🎯 Day trading analysis (high frequency)
python pair_analyzer.py --quote USDT --timeframe 5m --days 7 --workers 8

# 📈 Swing trading analysis (medium term)
python pair_analyzer.py --quote USDT --timeframe 1h --days 30 --top-pairs 15

# 💰 Long-term analysis (position trading)
python pair_analyzer.py --quote USDT --timeframe 1d --days 180 --workers 4

# 🔍 Comprehensive BTC pairs analysis
python pair_analyzer.py --quote BTC --timeframe 4h --top-pairs 25 --verbose
```

## ⚙️ Configuration

### Freqtrade Configuration

The analyzer automatically detects your Freqtrade configuration from:

1. `user_data/private/config-private.json` (preferred)
2. `user_data/config.json`
3. `config.json`
4. `~/.freqtrade/config.json`

### Minimal Configuration

If no config is found, create a basic one:

```json
{
  "dry_run": true,
  "stake_currency": "USDT",
  "exchange": {
    "name": "binance",
    "ccxt_config": {
      "enableRateLimit": true
    }
  },
  "dataformat": "json"
}
```

### Directory Structure

```
freqtrade/
├── pair_analyzer/          # Analyzer code
│   ├── pair_analyzer.py    # Main script
│   ├── utils/              # Utility modules
│   └── outputs/            # Analysis results
├── user_data/
│   ├── data/              # OHLCV data files
│   ├── config.json        # Main configuration
│   └── private/           # Private configurations
└── strategies/            # Trading strategies
```

## 📊 Output

### Terminal Output

```
╔══════════════════════════════════════════════════════════════╗
║                FREQTRADE PAIR ANALYZER PRO                  ║
║                         Version 2.0.0                       ║
╠══════════════════════════════════════════════════════════════╣
║  Advanced cryptocurrency pair analysis and ranking tool     ║
║  Quote Currency: USDT                                       ║
╚══════════════════════════════════════════════════════════════╝

Configuration:
  Quote Currency: USDT
  Timeframe: 15m
  Days Analyzed: 90
  Workers Used: 8

Analysis Results:
  Total Pairs Processed: 847
  Successful Analyses: 823
  Failed Analyses: 24

Top 15 Pairs by Composite Score:
   1. BTC/USDT        Score: 0.847 | Vol: 0.234 | Trend: 45.2 | Volume: 18.3
   2. ETH/USDT        Score: 0.823 | Vol: 0.267 | Trend: 41.8 | Volume: 17.9
   3. ADA/USDT        Score: 0.791 | Vol: 0.312 | Trend: 38.4 | Volume: 16.2
   ...
```

### JSON Reports

Detailed analysis reports are saved to:
- `user_data/analysis_results/pair_analysis_v2.0.0_YYYYMMDD_HHMMSS.json`
- `outputs/pair_analysis_v2.0.0_YYYYMMDD_HHMMSS.json`

## 🔧 Troubleshooting

### Common Issues

**❌ "No valid pairs found"**
```bash
# Check your configuration and data
python debug_script.py

# Verify exchange connection
python test_analyzer.py
```

**❌ "Import errors"**
```bash
# Install missing dependencies
pip install freqtrade[all] TA-Lib pandas numpy

# Check Python path
export PYTHONPATH="/path/to/freqtrade:$PYTHONPATH"
```

**❌ "Permission denied"**
```bash
# Fix directory permissions
chmod -R 755 user_data/
mkdir -p user_data/data user_data/analysis_results
```

### Performance Tips

- **Reduce workers** if you have memory issues
- **Use shorter timeframes** for recent data analysis
- **Limit days** for faster processing
- **Close other applications** during analysis

## 🛠 Development

### Project Structure

```
pair_analyzer/
├── pair_analyzer.py           # Main entry point
├── utils/
│   ├── __init__.py           # Package initialization
│   ├── data_handler.py       # Core analyzer logic
│   ├── data_manager.py       # Data downloading/management
│   ├── analysis_engine.py    # Technical analysis calculations
│   └── config_handler.py     # Configuration management
├── test_analyzer.py          # Test suite
├── debug_script.py          # Debug utilities
├── version_info.py          # Version management
└── outputs/                 # Analysis results
```

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Freqtrade Team** - For the excellent trading framework
- **TA-Lib** - For technical analysis indicators
- **Community Contributors** - For feedback and improvements

---

**⭐ If this tool helps your trading, please star the repository!**

EOF

# Create requirements.txt
echo "📦 Creating requirements.txt..."
cat > requirements.txt << 'EOF'
# Freqtrade Pair Analyzer Requirements
freqtrade>=2023.1
TA-Lib>=0.4.25
pandas>=1.5.0
numpy>=1.21.0
scipy>=1.9.0
ccxt>=4.0.0
requests>=2.28.0
python-dateutil>=2.8.0
pytz>=2022.1
EOF

# Create LICENSE (only if it doesn't exist)
if [ ! -f "LICENSE" ]; then
    echo "📄 Creating LICENSE..."
    cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2025 Freqtrade Pair Analyzer Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
else
    echo "📄 LICENSE already exists, skipping..."
fi

# Create CHANGELOG.md
echo "📝 Creating CHANGELOG.md..."
cat > CHANGELOG.md << 'EOF'
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
EOF

# Create sample config (only if it doesn't exist)
if [ ! -f "config-sample.json" ]; then
    echo "⚙️ Creating config-sample.json..."
    cat > config-sample.json << 'EOF'
{
  "dry_run": true,
  "stake_currency": "USDT",
  "exchange": {
    "name": "binance",
    "key": "your_api_key_here",
    "secret": "your_api_secret_here",
    "ccxt_config": {
      "enableRateLimit": true,
      "rateLimit": 50
    }
  },
  "dataformat": "json"
}
EOF
else
    echo "⚙️ config-sample.json already exists, skipping..."
fi

# Create directories if they don't exist
echo "📁 Creating directory structure..."
mkdir -p outputs
mkdir -p user_data/analysis_results

# Create quick run script
echo "🏃‍♂️ Creating run.sh..."
cat > run.sh << 'EOF'
#!/bin/bash

# Quick run script with common parameters
echo "🚀 Running Freqtrade Pair Analyzer..."

# Default parameters
QUOTE_CURRENCY="USDT"
TIMEFRAME="1h"
WORKERS="4"
TOP_PAIRS="10"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -q|--quote)
            QUOTE_CURRENCY="$2"
            shift 2
            ;;
        -t|--timeframe)
            TIMEFRAME="$2"
            shift 2
            ;;
        -w|--workers)
            WORKERS="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -q, --quote CURRENCY    Quote currency (default: USDT)"
            echo "  -t, --timeframe TF      Timeframe (default: 1h)"
            echo "  -w, --workers N         Number of workers (default: 4)"
            echo "  -h, --help             Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "Configuration:"
echo "  Quote Currency: $QUOTE_CURRENCY"
echo "  Timeframe: $TIMEFRAME"
echo "  Workers: $WORKERS"
echo ""

python pair_analyzer.py \
    --quote "$QUOTE_CURRENCY" \
    --timeframe "$TIMEFRAME" \
    --workers "$WORKERS" \
    --top-pairs "$TOP_PAIRS" \
    --verbose
EOF

chmod +x run.sh

# Final summary
echo ""
echo "✅ Project documentation created successfully!"
echo ""
echo "📁 Files created/updated:"
echo "   ✓ README.md           - Comprehensive documentation"
echo "   ✓ requirements.txt    - Python dependencies"
echo "   ✓ CHANGELOG.md        - Version history"
echo "   ✓ config-sample.json  - Sample configuration"
echo "   ✓ run.sh             - Quick run script"
echo "   ✓ LICENSE            - MIT license (if not existing)"
echo "   ⚠ .gitignore         - PRESERVED (not overwritten)"
echo ""
echo "📂 Directories created:"
echo "   ✓ outputs/                     - Analysis outputs"
echo "   ✓ user_data/analysis_results/  - Analysis reports"
echo ""
echo "🚀 Next steps:"
echo "   1. Review README.md"  
echo "   2. Test: python test_analyzer.py"
echo "   3. Quick run: ./run.sh --quote USDT"
echo "   4. Commit: git add . && git commit -m 'Add comprehensive project documentation'"
echo ""