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

