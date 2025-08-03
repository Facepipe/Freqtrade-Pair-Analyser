"""
Core Analyzer - Versioned Implementation
Version History:
• v2.12.2 - Fixed import paths for new structure
• v2.12.1 - Updated for fixed DataManager
• v2.12.0 - Enhanced pair filtering
"""
from typing import Dict, Optional, List, Tuple
import time
import json
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from freqtrade.resolvers import ExchangeResolver
from freqtrade.data.dataprovider import DataProvider

# Import our local modules with proper paths
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from version_info import VERSION, print_banner
except ImportError:
    # Fallback if version_info is not available
    VERSION = "2.12.2"
    def print_banner(version, quote_currency):
        print(f"Freqtrade Pair Analyzer v{version} - Quote: {quote_currency}")

import logging
from .analysis_engine import AnalysisEngine
from .data_manager import DataManager
from .config_handler import load_config, check_directory_permissions

logger = logging.getLogger(__name__)

class VersionedAnalyzer:
    """
    Main analyzer class that orchestrates the entire analysis process
    """
    CURRENT_VERSION = "2.12.2"
    
    def __init__(self, quote_currency: Optional[str] = None, max_workers: int = 8):
        self._version = self.CURRENT_VERSION
        logger.info(f"Initializing Analyzer v{self._version}")
        
        # Initialize configuration
        self.quote_currency = quote_currency or self._get_default_quote_currency()
        self.max_workers = max_workers
        
        try:
            print_banner(VERSION, self.quote_currency)
        except:
            print(f"Freqtrade Pair Analyzer v{self._version} - Quote: {self.quote_currency}")
            
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
            Path('outputs'),  # Add outputs directory
            Path(self.config['user_data_dir']),
            Path(self.config['user_data_dir']) / 'private',
            Path(self.config['strategy_path'])
        ]
        
        for directory in required_dirs:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                if not check_directory_permissions(directory):
                    logger.warning(f"Limited permissions for {directory}")
            except Exception as e:
                logger.error(f"Directory error: {directory} - {str(e)}")

    def _initialize_exchange(self):
        """Initialize and validate exchange connection"""
        logger.info("Initializing exchange connection...")
        try:
            exchange = ExchangeResolver.load_exchange(self.config, validate=False)
            markets = exchange.get_markets()
            if not markets:
                raise ConnectionError("No markets returned from exchange")
            logger.info(f"Connected to {exchange.name} with {len(markets)} pairs")
            return exchange
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {str(e)}")
            raise

    def _get_default_quote_currency(self) -> str:
        """Get default quote currency from config"""
        try:
            from .config_handler import get_project_root
            config_path = get_project_root() / 'user_data' / 'private' / 'config-private.json'
            if config_path.exists():
                with open(config_path) as f:
                    config = json.load(f)
                return config.get('stake_currency', 'USDT')
        except Exception as e:
            logger.warning(f"Using default USDT: {str(e)}")
        return 'USDT'

    def _get_valid_pairs(self) -> List[str]:
        """Get valid trading pairs with proper filtering"""
        try:
            markets = self.exchange.get_markets()
            valid_pairs = []
            
            for pair, info in markets.items():
                if (pair.endswith(f"/{self.quote_currency}") and 
                    info.get('active', False) and
                    info.get('spot', True) and
                    not info.get('margin', False) and  # Exclude margin pairs
                    not info.get('future', False)):    # Exclude futures
                    valid_pairs.append(pair)
            
            logger.info(f"Found {len(valid_pairs)} valid {self.quote_currency} pairs")
            return valid_pairs
        except Exception as e:
            logger.error(f"Error getting valid pairs: {str(e)}")
            return []

    def analyze_pair(self, pair: str) -> Optional[Dict[str, float]]:
        """Execute full analysis for a single pair"""
        try:
            logger.debug(f"Analyzing {pair}")
            dataframe = self.data_manager.ensure_pair_data(
                pair,
                self.days_to_analyze + self.extra_days
            )
            
            if dataframe is None or len(dataframe) < self.min_data_points:
                logger.warning(f"Insufficient data for {pair}: {len(dataframe) if dataframe is not None else 0} points")
                return None
                
            result = self.analysis_engine.analyze_dataframe(dataframe, pair)
            if result:
                result['processing_time'] = time.time() - self.start_time
                result['analyzer_version'] = self._version
                logger.debug(f"Analysis completed for {pair}")
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed for {pair}: {str(e)}")
            return None

    def run_analysis(self) -> Tuple[List[Dict[str, float]], List[str]]:
        """Execute parallel analysis across all pairs"""
        pairs = self._get_valid_pairs()
        if not pairs:
            logger.error("No valid pairs found for analysis")
            return [], []
            
        logger.info(f"Starting analysis of {len(pairs)} {self.quote_currency} pairs")
        
        results = []
        failed_pairs = []
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_pair = {executor.submit(self.analyze_pair, pair): pair for pair in pairs}
            
            # Collect results as they complete
            for future in as_completed(future_to_pair):
                pair = future_to_pair[future]
                try:
                    result = future.result(timeout=120)  # 2 minute timeout per pair
                    if result:
                        results.append(result)
                        logger.info(f"✓ {pair} - Score: {result.get('composite_score', 0):.3f}")
                    else:
                        failed_pairs.append(pair)
                        logger.warning(f"✗ {pair} - Analysis failed")
                except Exception as e:
                    failed_pairs.append(pair)
                    logger.error(f"✗ {pair} - Exception: {str(e)}")
        
        # Calculate composite scores if we have results
        if results:
            logger.info("Calculating composite scores...")
            for res in results:
                # Weighted composite score calculation
                res['composite_score'] = (
                    0.3 * min(res.get('trend_strength', 0), 100) / 100 +
                    0.25 * min(res.get('volatility', 0), 5) / 5 +
                    0.2 * min(res.get('volume_score', 0), 20) / 20 +
                    0.15 * min(res.get('coral_score', 0), 1) +
                    0.1 * min(res.get('stc_score', 0), 100) / 100
                )
            
            # Sort by composite score
            results.sort(key=lambda x: x['composite_score'], reverse=True)
        
        elapsed = (time.time() - self.start_time) / 60
        logger.info(f"Analysis completed in {elapsed:.1f} minutes")
        logger.info(f"Results: {len(results)} successful, {len(failed_pairs)} failed")
        
        return results, failed_pairs

    def save_results(self, results: List[Dict[str, float]], failed_pairs: List[str] = None) -> Dict:
        """Save analysis results with comprehensive metadata"""
        try:
            # Create both output directories
            output_dirs = [
                Path('user_data/analysis_results'),
                Path('outputs')
            ]
            
            for output_dir in output_dirs:
                output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pair_analysis_v{self._version}_{self.quote_currency}_{timestamp}.json"
            
            # Prepare comprehensive report
            report = {
                'metadata': {
                    'version': self._version,
                    'quote_currency': self.quote_currency,
                    'timeframe': self.timeframe,
                    'days_analyzed': self.days_to_analyze,
                    'analysis_date': timestamp,
                    'analysis_timestamp': datetime.now().isoformat(),
                    'successful_pairs': len(results),
                    'failed_pairs': len(failed_pairs) if failed_pairs else 0,
                    'total_processing_time_minutes': (time.time() - self.start_time) / 60,
                    'components': {
                        'analysis_engine': getattr(self.analysis_engine, 'version', self.analysis_engine.CURRENT_VERSION),
                        'data_manager': getattr(self.data_manager, 'version', self.data_manager.CURRENT_VERSION)
                    },
                    'parameters': {
                        'max_workers': self.max_workers,
                        'min_data_points': self.min_data_points,
                        'extra_days': self.extra_days
                    }
                },
                'results': results,
                'failed_pairs': failed_pairs if failed_pairs else [],
                'top_pairs': [r['pair'] for r in results[:10]] if results else [],
                'summary_statistics': self._calculate_summary_stats(results) if results else {}
            }
            
            # Save to both directories
            for output_dir in output_dirs:
                filepath = output_dir / filename
                with open(filepath, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
                logger.info(f"Results saved to {filepath}")
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to save results: {str(e)}")
            raise

    def _calculate_summary_stats(self, results: List[Dict]) -> Dict:
        """Calculate summary statistics for the results"""
        if not results:
            return {}
        
        import statistics
        
        try:
            scores = [r.get('composite_score', 0) for r in results]
            volatilities = [r.get('volatility', 0) for r in results]
            trends = [r.get('trend_strength', 0) for r in results]
            
            return {
                'composite_score': {
                    'mean': statistics.mean(scores),
                    'median': statistics.median(scores),
                    'max': max(scores),
                    'min': min(scores),
                    'stdev': statistics.stdev(scores) if len(scores) > 1 else 0
                },
                'volatility': {
                    'mean': statistics.mean(volatilities),
                    'median': statistics.median(volatilities),
                    'max': max(volatilities),
                    'min': min(volatilities)
                },
                'trend_strength': {
                    'mean': statistics.mean(trends),
                    'median': statistics.median(trends),
                    'max': max(trends),
                    'min': min(trends)
                }
            }
        except Exception as e:
            logger.warning(f"Error calculating summary stats: {str(e)}")
            return {}

    @property
    def version(self) -> str:
        """Get current analyzer version"""
        return self._version