"""
Core Analyzer - Versioned Implementation
Version History:
• v2.12.0 - Enhanced pair filtering and analysis reliability
• v2.11.4 - Added missing run_analysis method
"""
from typing import Dict, Optional, List, Tuple
import time
import json
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from freqtrade.resolvers import ExchangeResolver
from freqtrade.data.dataprovider import DataProvider
from version_info import VERSION, print_banner
import logging
from analysis_engine import AnalysisEngine
from data_manager import DataManager
from config_handler import load_config, check_directory_permissions

logger = logging.getLogger(__name__)

class VersionedAnalyzer:
    CURRENT_VERSION = "2.12.0"
    
    def __init__(self, quote_currency: Optional[str] = None, max_workers: int = 8):
        self._version = self.CURRENT_VERSION
        logger.info(f"Initializing Analyzer v{self._version}")
        
        # Initialize configuration
        self.quote_currency = quote_currency or self._get_default_quote_currency()
        self.max_workers = max_workers
        
        print_banner(VERSION, self.quote_currency)
        self.config = load_config(self.quote_currency)
        self._ensure_directories_exist()
        
        # Analysis parameters
        self.timeframe = '1d'
        self.days_to_analyze = 90
        self.extra_days = 7
        self.min_data_points = 30
        
        # Initialize components
        self.exchange = self._initialize_exchange()
        self.dataprovider = DataProvider(self.config, self.exchange)
        self.data_manager = DataManager(self.config, self.exchange, self.timeframe)
        self.analysis_engine = AnalysisEngine()
        
        self.start_time = time.time()

    def _ensure_directories_exist(self) -> None:
        """Create required analysis directories"""
        required_dirs = [
            Path(self.config.get('datadir', 'user_data/data')),
            Path('user_data/analysis_results'),
            Path(self.config['user_data_dir']),
            Path(self.config['user_data_dir']) / 'private',
            Path(self.config['strategy_path'])
        ]
        
        for directory in required_dirs:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                if not check_directory_permissions(directory):
                    raise PermissionError(f"Cannot write to {directory}")
            except Exception as e:
                logger.error(f"Directory error: {str(e)}")
                raise

    def _initialize_exchange(self):
        """Initialize and validate exchange connection"""
        logger.info("Initializing exchange connection...")
        exchange = ExchangeResolver.load_exchange(self.config, validate=False)
        markets = exchange.get_markets()
        if not markets:
            raise ConnectionError("No markets returned from exchange")
        logger.info(f"Connected to {exchange.name} with {len(markets)} pairs")
        return exchange

    def _get_default_quote_currency(self) -> str:
        """Get default quote currency from config"""
        try:
            from config_handler import get_project_root
            config_path = get_project_root() / 'user_data' / 'private' / 'config-private.json'
            with open(config_path) as f:
                config = json.load(f)
            return config.get('stake_currency', 'USDT')
        except Exception as e:
            logger.warning(f"Using default USDT: {str(e)}")
            return 'USDT'

    def _get_valid_pairs(self) -> List[str]:
        """Get valid trading pairs with proper filtering"""
        markets = self.exchange.get_markets()
        return [p for p in markets 
               if (p.endswith(f"/{self.quote_currency}") and 
                   markets[p].get('active', False) and
                   markets[p].get('spot', True))]

    def analyze_pair(self, pair: str) -> Optional[Dict[str, float]]:
        """Execute full analysis for a single pair"""
        try:
            dataframe = self.data_manager.ensure_pair_data(
                pair,
                self.days_to_analyze + self.extra_days
            )
            
            if dataframe is None or len(dataframe) < self.min_data_points:
                logger.warning(f"Insufficient data for {pair}")
                return None
                
            result = self.analysis_engine.analyze_dataframe(dataframe, pair)
            if result:
                result['processing_time'] = time.time() - self.start_time
                result['analyzer_version'] = self._version
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed for {pair}: {str(e)}")
            return None

    def run_analysis(self) -> Tuple[List[Dict[str, float]], List[str]]:
        """Execute parallel analysis across all pairs"""
        pairs = self._get_valid_pairs()
        logger.info(f"Starting analysis of {len(pairs)} {self.quote_currency} pairs")
        
        results = []
        failed_pairs = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.analyze_pair, pair): pair for pair in pairs}
            
            for future in as_completed(futures):
                pair = futures[future]
                result = future.result()
                if result:
                    results.append(result)
                else:
                    failed_pairs.append(pair)
        
        # Calculate composite scores if we have results
        if results:
            for res in results:
                res['composite_score'] = (
                    0.3 * res['trend_strength'] +
                    0.25 * res['volatility'] +
                    0.2 * res['volume_score'] +
                    0.15 * res['coral_score'] +
                    0.1 * res['stc_score']
                )
            results.sort(key=lambda x: x['composite_score'], reverse=True)
        
        elapsed = (time.time() - self.start_time)/60
        logger.info(f"Analysis completed in {elapsed:.1f} minutes")
        return results, failed_pairs

    def save_results(self, results: List[Dict[str, float]], failed_pairs: List[str] = None) -> Dict:
        """Save analysis results with comprehensive metadata"""
        try:
            output_dir = Path('user_data/analysis_results')
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pair_analysis_v{self._version}_{timestamp}.json"
            
            report = {
                'metadata': {
                    'version': self._version,
                    'quote_currency': self.quote_currency,
                    'timeframe': self.timeframe,
                    'days_analyzed': self.days_to_analyze,
                    'analysis_date': timestamp,
                    'successful_pairs': len(results),
                    'failed_pairs': len(failed_pairs) if failed_pairs else 0,
                    'components': {
                        'analysis_engine': self.analysis_engine.version,
                        'data_manager': self.data_manager.version
                    }
                },
                'results': results,
                'failed_pairs': failed_pairs if failed_pairs else [],
                'top_pairs': [r['pair'] for r in results[:50]] if results else []
            }
            
            with open(output_dir / filename, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Results saved to {filename}")
            return report
        except Exception as e:
            logger.error(f"Failed to save results: {str(e)}")
            raise

    @property
    def version(self) -> str:
        """Get current analyzer version"""
        return self._version