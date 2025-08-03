"""
Freqtrade Pair Analyzer Pro
Version: 2.2.3
Features:
- Loads credentials from config-private.json (v1.0)
- Parallel processing (v2.0)
- Comprehensive logging (v2.1)
- Version control system (v2.1)
- Fixed load_pair_history API compatibility (v2.1.1)
- Added missing methods (v2.1.2)
- Auto-download feature (v2.2.0)
- Configurable quote currency (v2.2.0)
- Fixed data download implementation (v2.2.1)
- Fixed initialization order (v2.2.2)
- Fixed parenthesis syntax in download method (v2.2.3)
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
from freqtrade.data.history import load_pair_history
from freqtrade.data.history import get_datahandler

# Version control setup
VERSION = "2.2.3"
CHANGELOG = {
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

class VersionedAnalyzer:
    def __init__(self, quote_currency: str = None, max_workers: int = 8, download_data: bool = False):
        # Initialize attributes first
        self.quote_currency = quote_currency or self._get_default_quote_currency()
        self.max_workers = max_workers
        self.download_data = download_data
        
        # Then print banner
        self._print_banner()
        
        # Rest of initialization
        self.config = self._load_config()
        self.exchange = self._init_exchange()
        self.dataprovider = DataProvider(self.config, self.exchange)
        self.data_handler = get_datahandler(self.config['datadir'], self.config['dataformat'])
        
        # Analysis parameters
        self.timeframe = '1d'
        self.days_to_analyze = 90
        self.extra_days = 2  # Buffer for analysis
        self.start_time = time.time()

        # Download data if requested
        if self.download_data:
            self._download_all_pair_data()

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

    def _get_default_quote_currency(self) -> str:
        """Get default quote currency from config or use USDT"""
        try:
            with open('user_data/private/config-private.json') as f:
                config = json.load(f)
            return config.get('stake_currency', 'USDT')
        except:
            return 'USDT'

    def _download_all_pair_data(self):
        """Download data for all pairs using correct method"""
        pairs = [p for p in self.exchange.get_markets() 
                if p.endswith(f"/{self.quote_currency}")]
        
        logger.info(f"Downloading data for {len(pairs)} pairs...")
        
        for pair in pairs:
            try:
                # Calculate timestamp with properly closed parentheses
                days = self.days_to_analyze + self.extra_days
                since_ms = int((time.time() - (days * 86400)) * 1000)
                
                self.exchange.get_historic_ohlcv(
                    pair=pair,
                    timeframe=self.timeframe,
                    since_ms=since_ms
                )
                logger.info(f"Downloaded data for {pair}")
            except Exception as e:
                logger.warning(f"Failed to download {pair}: {str(e)}")

        logger.info("Data download completed")

    # [Rest of the methods remain unchanged...]
    # ... (keep all other existing methods exactly as they were)

# [Rest of the file remains unchanged...]

    def _load_config(self) -> Dict:
        """Load configuration from private file (v1.0 feature)"""
        config_path = Path('user_data/private/config-private.json')
        try:
            with open(config_path) as f:
                private_config = json.load(f)
            
            return {
                'runmode': 'dry_run',
                'exchange': {
                    'name': private_config['exchange']['name'],
                    'key': private_config['exchange']['key'],
                    'secret': private_config['exchange']['secret'],
                    'ccxt_config': {
                        'enableRateLimit': True,
                        **private_config['exchange'].get('ccxt_config', {})
                    },
                    'ccxt_async_config': private_config['exchange'].get('ccxt_async_config', {})
                },
                'telegram': private_config.get('telegram', {}),
                'stake_currency': self.quote_currency,
                'dry_run': True,
                'dataformat': 'json',
                'datadir': 'user_data/data',
                'user_data_dir': 'user_data',
                'strategy_path': 'user_data/strategies'
            }
        except Exception as e:
            logger.error(f"Config loading failed: {e}")
            raise

    # [Rest of the methods remain unchanged...]
    # ... (keep all other existing methods exactly as they were)

# [Rest of the file remains unchanged...]

    def _init_exchange(self):
        """Initialize exchange connection (v1.0)"""
        logger.info("Initializing exchange connection...")
        exchange = ExchangeResolver.load_exchange(self.config, validate=False)
        markets = exchange.get_markets()
        logger.info(f"Connected to {exchange.name}. Available pairs: {len(markets)}")
        return exchange

    def _calculate_volatility(self, dataframe: pd.DataFrame) -> float:
        """Calculate annualized volatility"""
        returns = np.log(dataframe['close'] / dataframe['close'].shift(1))
        return returns.rolling(window=14).std().mean() * np.sqrt(365)

    def _calculate_coral_score(self, dataframe: pd.DataFrame) -> float:
        """Calculate Coral Trend effectiveness"""
        length = 20
        diff = dataframe['close'].diff(length)
        std = dataframe['close'].rolling(length).std()
        coral = diff / (std * np.sqrt(length))
        return (coral.abs() > 1.0).mean()

    def _calculate_stc_score(self, dataframe: pd.DataFrame) -> float:
        """Calculate Schaff Trend Cycle effectiveness"""
        macd = ta.EMA(dataframe, timeperiod=23) - ta.EMA(dataframe, timeperiod=50)
        stoch = 100 * (macd - macd.rolling(10).min()) / (macd.rolling(10).max() - macd.rolling(10).min())
        return stoch.diff().abs().mean()

    def analyze_pair(self, pair: str) -> Dict:
        """Analyze single pair with all indicators (v2.0 parallel)"""
        try:
            start_time = time.time()
            logger.info(f"Starting analysis for {pair}")
            
            dataframe = load_pair_history(
                datadir=Path(self.config['datadir']),
                pair=pair,
                timeframe=self.timeframe,
                timerange=f"{(self.days_to_analyze + self.extra_days)}d",
                data_format=self.config['dataformat']
            )

            if len(dataframe) < self.days_to_analyze:
                logger.warning(f"Insufficient data for {pair}")
                return None

            results = {
                'pair': pair,
                'volatility': self._calculate_volatility(dataframe),
                'trend_strength': ta.ADX(dataframe, timeperiod=14).mean(),
                'volume_score': np.log1p(dataframe['volume'].mean()),
                'coral_score': self._calculate_coral_score(dataframe),
                'stc_score': self._calculate_stc_score(dataframe),
                'processing_time': time.time() - start_time
            }
            
            logger.info(f"Completed {pair} in {results['processing_time']:.1f}s")
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing {pair}: {str(e)}")
            return None

    def run_analysis(self) -> List[Dict]:
        """Execute parallel analysis (v2.0)"""
        pairs = [p for p in self.exchange.get_markets() 
                if p.endswith(f"/{self.quote_currency}")]
        
        logger.info(f"Starting analysis of {len(pairs)} pairs")
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.analyze_pair, pair): pair for pair in pairs}
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)
        
        # Calculate composite score
        for res in results:
            res['composite_score'] = (
                0.2 * res['volatility'] +
                0.3 * res['trend_strength'] +
                0.2 * res['volume_score'] +
                0.15 * res['coral_score'] +
                0.15 * res['stc_score']
            )
        
        results.sort(key=lambda x: x['composite_score'], reverse=True)
        logger.info(f"Analysis completed in {(time.time()-self.start_time)/60:.1f} minutes")
        return results

    def save_results(self, results: List[Dict]):
        """Save results with version tracking"""
        output_dir = Path('user_data/analysis_results')
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pair_analysis_v{VERSION}_{timestamp}.json"
        
        with open(output_dir / filename, 'w') as f:
            json.dump({
                'metadata': {
                    'version': VERSION,
                    'quote_currency': self.quote_currency,
                    'analysis_date': timestamp,
                    'timeframe': self.timeframe,
                    'days_analyzed': self.days_to_analyze
                },
                'results': results
            }, f, indent=2)
        
        logger.info(f"Saved versioned results to {filename}")

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