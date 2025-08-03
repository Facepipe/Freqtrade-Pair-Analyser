"""
Freqtrade Pair Analyzer Pro
Version: 2.2.0
Features:
- Loads credentials from config-private.json (v1.0)
- Parallel processing (v2.0)
- Comprehensive logging (v2.1)
- Version control system (v2.1)
- Fixed load_pair_history API compatibility (v2.1.1)
- Added missing methods (v2.1.2)
- Auto-download feature (v2.2.0)
- Configurable quote currency (v2.2.0)
"""
import os
import json
import time
import logging
import argparse
import numpy as np
import pandas as pd
import talib.abstract as ta
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from freqtrade.resolvers import ExchangeResolver
from freqtrade.data.dataprovider import DataProvider
from freqtrade.data.history import load_pair_history, download_pair_history

# Version control setup
VERSION = "2.2.0"
CHANGELOG = {
    "2.2.0": "Added auto-download feature and quote currency configuration",
    "2.1.2": "Added missing analysis methods",
    "2.1.1": "Fixed load_pair_history API compatibility",
    "2.1.0": "Added version control system and change logging",
    "2.0.0": "Implemented parallel processing and enhanced logging",
    "1.0.0": "Initial version with config file loading"
}

class VersionedAnalyzer:
    def __init__(self, quote_currency: str = None, max_workers: int = 8, download_data: bool = False):
        self._print_banner()
        
        # Initialize with config or default
        self.quote_currency = quote_currency or self._get_default_quote_currency()
        self.max_workers = max_workers
        self.download_data = download_data
        self.config = self._load_config()
        self.exchange = self._init_exchange()
        self.dataprovider = DataProvider(self.config, self.exchange)
        
        # Analysis parameters
        self.timeframe = '1d'
        self.days_to_analyze = 90
        self.extra_days = 2  # Buffer for analysis
        self.start_time = time.time()

        # Download data if requested
        if self.download_data:
            self._download_all_pair_data()

    def _get_default_quote_currency(self) -> str:
        """Get default quote currency from config or use USDT"""
        try:
            with open('user_data/private/config-private.json') as f:
                config = json.load(f)
            return config.get('stake_currency', 'USDT')
        except:
            return 'USDT'

    def _print_banner(self):
        """Display version information"""
        print(f"\n{'='*50}")
        print(f"Freqtrade Pair Analyzer Pro v{VERSION}")
        print(f"Quote Currency: {self.quote_currency}")
        print(f"{'='*50}")
        print("Feature History:")
        for ver, desc in CHANGELOG.items():
            print(f"• v{ver}: {desc}")
        print(f"{'='*50}\n")

    def _download_all_pair_data(self):
        """Download data for all pairs"""
        pairs = [p for p in self.exchange.get_markets() 
                if p.endswith(f"/{self.quote_currency}")]
        
        logger.info(f"Downloading data for {len(pairs)} pairs...")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for pair in pairs:
                futures.append(executor.submit(
                    download_pair_history,
                    datadir=Path(self.config['datadir']),
                    pair=pair,
                    timeframe=self.timeframe,
                    timerange=f"{(self.days_to_analyze + self.extra_days)}d",
                    exchange=self.exchange
                ))
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.warning(f"Download failed: {str(e)}")

        logger.info("Data download completed")

    # [Previous methods remain unchanged...]
    # _load_config(), _init_exchange(), _calculate_volatility(), etc.
    # analyze_pair(), run_analysis(), save_results()

# Configure argument parser
def parse_args():
    parser = argparse.ArgumentParser(description='Freqtrade Pair Analyzer')
    parser.add_argument('--quote', type=str, help='Quote currency to analyze (e.g. USDT, BTC)')
    parser.add_argument('--download', action='store_true', help='Download all pair data before analysis')
    parser.add_argument('--workers', type=int, default=8, help='Number of parallel workers')
    return parser.parse_args()

# Configure logging
log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.FileHandler('pair_analyzer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    try:
        args = parse_args()
        
        analyzer = VersionedAnalyzer(
            quote_currency=args.quote,
            max_workers=args.workers,
            download_data=args.download
        )
        
        results = analyzer.run_analysis()
        analyzer.save_results(results)
        
        print("\nTop 10 Pairs:")
        for i, pair in enumerate([r['pair'] for r in results[:10]], 1):
            print(f"{i}. {pair}")
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)