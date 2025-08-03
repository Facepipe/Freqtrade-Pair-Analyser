"""
Version Information
Version: 2.2.6
"""
VERSION = "2.2.6"
CHANGELOG = {
    "2.2.6": "Fixed data download sequence and warnings",
    "2.2.5": "Improved handling of missing data",
    "2.2.4": "Added candle_type parameter for Binance API",
    "2.2.3": "Fixed parenthesis syntax in download method",
    "2.2.2": "Fixed initialization order",
    "2.2.1": "Fixed data download implementation",
    "2.2.0": "Added auto-download feature and quote currency configuration",
    "2.1.2": "Added missing analysis methods",
    "2.1.1": "Fixed load_pair_history API compatibility",
    "2.1.0": "Added version control system and change logging",
    "2.0.0": "Implemented parallel processing and enhanced logging",
    "1.0.0": "Initial version with config file loading"
}

def print_banner(version, quote_currency):
    """Display version information"""
    print(f"\n{'='*50}")
    print(f"Freqtrade Pair Analyzer Pro v{version}")
    print(f"Quote Currency: {quote_currency}")
    print(f"{'='*50}")
    print("Feature History:")
    for ver, desc in CHANGELOG.items():
        print(f"• v{ver}: {desc}")
    print(f"{'='*50}\n")