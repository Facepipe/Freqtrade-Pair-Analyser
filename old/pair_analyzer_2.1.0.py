"""
Freqtrade Pair Analyzer Pro
Version: 2.1.0
Features:
- Loads credentials from config-private.json (v1.0)
- Parallel processing (v2.0)
- Comprehensive logging (v2.1)
- Version control system (v2.1)
"""
import os
import json
import time
import logging
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

# Version control setup
VERSION = "2.1.0"
CHANGELOG = {
    "2.1.0": "Added version control system and change logging",
    "2.0.0": "Implemented parallel processing and enhanced logging",
    "1.0.0": "Initial version with config file loading"
}

class VersionedAnalyzer:
    def __init__(self, quote_currency: str = 'BTC', max_workers: int = 8):
        self._print_banner()
        logger.info(f"Initializing PairAnalyzer v{VERSION}")
        
        self.quote_currency = quote_currency
        self.max_workers = max_workers
        self.config = self._load_config()
        self.exchange = self._init_exchange()
        self.dataprovider = DataProvider(self.config, self.exchange)
        
        # Analysis parameters
        self.timeframe = '1d'
        self.days_to_analyze = 90
        self.start_time = time.time()

    def _print_banner(self):
        """Display version information"""
        print(f"\n{'='*50}")
        print(f"Freqtrade Pair Analyzer Pro v{VERSION}")
        print(f"{'='*50}")
        print("Feature History:")
        for ver, desc in CHANGELOG.items():
            print(f"• v{ver}: {desc}")
        print(f"{'='*50}\n")

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

    def _init_exchange(self):
        """Initialize exchange connection (v1.0)"""
        logger.info("Initializing exchange connection...")
        exchange = ExchangeResolver.load_exchange(self.config, validate=False)
        markets = exchange.get_markets()
        logger.info(f"Connected to {exchange.name}. Available pairs: {len(markets)}")
        return exchange

    def analyze_pair(self, pair: str) -> Dict:
        """Analyze single pair with all indicators (v2.0 parallel)"""
        try:
            start_time = time.time()
            logger.info(f"Starting analysis for {pair}")
            
            dataframe = load_pair_history(
                pair=pair,
                timeframe=self.timeframe,
                dataprovider=self.dataprovider,
                timerange=f"{(self.days_to_analyze+10)}d"
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
        analyzer = VersionedAnalyzer(
            quote_currency='USDT',
            max_workers=16
        )
        results = analyzer.run_analysis()
        analyzer.save_results(results)
        
        print("\nTop 10 Pairs:")
        for i, pair in enumerate([r['pair'] for r in results[:10]], 1):
            print(f"{i}. {pair}")
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)