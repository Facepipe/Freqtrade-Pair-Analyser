"""
Data Downloader - Versioned Implementation
Version History:
• v1.3.1 - Fixed missing timeframe reference and improved validation
• v1.3.0 - Added exchange API validation
• v1.2.0 - Added missing data handling
"""
import time
from pathlib import Path
import logging
from typing import List, Dict, Optional
import pandas as pd
from freqtrade.data.history import load_pair_history

logger = logging.getLogger(__name__)

class DataDownloader:
    CURRENT_VERSION = "1.3.1"
    
    def __init__(self, config, exchange, timeframe: str = '1d'):
        self._version = self.CURRENT_VERSION
        self.config = config
        self.exchange = exchange
        self.timeframe = timeframe  # Now properly initialized
        
        # Download configuration
        self.retries = 2
        self.retry_wait = 3
        self.min_data_points = 0.5
        self.required_history_days = 30
        
        logger.info(f"Initialized DataDownloader v{self._version} for {self.timeframe} timeframe")

    def _validate_pair_availability(self, pair: str) -> bool:
        """Check if pair is available for download"""
        markets = self.exchange.get_markets()
        if pair not in markets:
            return False
            
        market = markets[pair]
        return (market.get('active', False) and 
                market.get('spot', False) and
                self.timeframe in market.get('timeframes', []))

    def download_pair_data(self, pair: str, days: int) -> Dict:
        """Download data for a single pair"""
        start_time = time.time()
        result = {
            'pair': pair,
            'status': 'failed',
            'attempts': 0,
            'message': '',
            'duration': 0
        }

        if not self._validate_pair_availability(pair):
            result.update({
                'status': 'skipped',
                'message': 'Pair not available'
            })
            return result

        for attempt in range(1, self.retries + 1):
            result['attempts'] = attempt
            try:
                since_ms = int((time.time() - (days * 86400)) * 1000)
                
                self.exchange.get_historic_ohlcv(
                    pair=pair,
                    timeframe=self.timeframe,
                    since_ms=since_ms,
                    candle_type='spot'
                )
                
                data = self._verify_download(pair, days)
                if data is not None:
                    result.update({
                        'status': 'success',
                        'message': f"Downloaded {len(data)} candles"
                    })
                    break
                    
            except Exception as e:
                result['message'] = str(e)
                if attempt < self.retries:
                    time.sleep(attempt * self.retry_wait)

        result['duration'] = time.time() - start_time
        return result

    def _verify_download(self, pair: str, days: int) -> Optional[pd.DataFrame]:
        """Verify downloaded data meets requirements"""
        try:
            data = load_pair_history(
                datadir=Path(self.config['datadir']),
                pair=pair,
                timeframe=self.timeframe,
                timerange=f"{days}d",
                data_format=self.config['dataformat']
            )
            
            if len(data) < self.required_history_days:
                logger.warning(f"Insufficient history for {pair}")
                return None
                
            return data.fillna(method='ffill').fillna(method='bfill')
            
        except Exception as e:
            logger.debug(f"Verification failed for {pair}: {str(e)}")
            return None

    def download_all_pairs(self, pairs: List[str], days: int) -> Dict:
        """Download data for multiple pairs"""
        valid_pairs = [p for p in pairs if self._validate_pair_availability(p)]
        logger.info(f"Found {len(valid_pairs)} valid pairs out of {len(pairs)}")
        
        results = []
        for pair in valid_pairs:
            result = self.download_pair_data(pair, days)
            results.append(result)
            time.sleep(0.5)  # Rate limiting
            
        success = sum(1 for r in results if r['status'] == 'success')
        
        return {
            'version': self._version,
            'timeframe': self.timeframe,
            'total_pairs': len(pairs),
            'valid_pairs': len(valid_pairs),
            'successful': success,
            'failed': len(valid_pairs) - success,
            'results': results
        }

    @property
    def version(self) -> str:
        return self._version