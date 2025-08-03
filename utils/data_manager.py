"""
Data Manager - Versioned Implementation
Version History:
• v1.6.3 - Fixed filename format handling (both _ and -)
• v1.6.2 - Enhanced download verification
"""
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd
import logging
from freqtrade.data.history import load_pair_history
import time
import json
import os

logger = logging.getLogger(__name__)

class DataManager:
    CURRENT_VERSION = "1.6.3"
    
    def __init__(self, config: Dict, exchange, timeframe: str = '1d', max_retries: int = 3):
        self._version = self.CURRENT_VERSION
        self.config = config
        self.timeframe = timeframe
        self.max_retries = max_retries
        self.datadir = Path(config['datadir'])
        self._ensure_data_directory()
        logger.info(f"Initialized DataManager v{self._version}")

    def _ensure_data_directory(self):
        """Ensure data directory exists with proper permissions"""
        try:
            self.datadir.mkdir(parents=True, exist_ok=True)
            test_file = self.datadir / '.permission_test'
            test_file.touch()
            test_file.unlink()
        except (PermissionError, OSError) as e:
            logger.error(f"Data directory {self.datadir} not accessible: {str(e)}")
            raise

    def _get_data_filenames(self, pair: str) -> list:
        """Return all possible filename variations for a pair"""
        pair_safe1 = pair.replace('/', '_')  # ADA_BTC
        pair_safe2 = pair.replace('/', '-')  # ADA-BTC
        return [
            self.datadir / f"{pair_safe1}-{self.timeframe}.json",
            self.datadir / f"{pair_safe2}-{self.timeframe}.json"
        ]

    def _find_data_file(self, pair: str) -> Optional[Path]:
        """Find the actual data file regardless of naming convention"""
        for filename in self._get_data_filenames(pair):
            if filename.exists():
                return filename
        return None

    def _verify_downloaded_file(self, pair: str) -> bool:
        """Verify the downloaded file exists and has valid content"""
        datafile = self._find_data_file(pair)
        if not datafile:
            return False
            
        try:
            # Check file size
            if os.path.getsize(datafile) < 100:  # Minimum expected file size
                return False
                
            # Check file content
            with open(datafile) as f:
                data = json.load(f)
                if not isinstance(data, list) or len(data) < 1:
                    return False
                    
            return True
        except Exception:
            return False

    def _download_with_freqtrade(self, pair: str, days: int) -> bool:
        """Use Freqtrade's built-in downloader"""
        try:
            cmd = [sys.executable, '-m', 'freqtrade'] + [
                "download-data",
                "--pairs", pair,
                "--timeframe", self.timeframe,
                "--days", str(days),
                "--datadir", str(self.datadir),
                "--exchange", self.config['exchange']['name'],
                "--data-format-ohlcv", "json",
                "--trading-mode", "spot"
            ]
            
            logger.info(f"Downloading {pair} data...")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # Add delay to allow filesystem to sync
            time.sleep(1)
            
            # Verify the download was actually successful
            if not self._verify_downloaded_file(pair):
                logger.warning(f"Download verification failed for {pair}")
                return False
                
            logger.debug(f"Download successful for {pair}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Download failed for {pair}: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Unexpected download error for {pair}: {str(e)}")
            return False

    def _load_data_safely(self, pair: str) -> Optional[pd.DataFrame]:
        """Safe wrapper around data loading"""
        datafile = self._find_data_file(pair)
        if not datafile:
            return None
            
        try:
            # Try standard load_pair_history first
            try:
                df = load_pair_history(
                    datadir=self.datadir,
                    pair=pair,
                    timeframe=self.timeframe,
                    data_format="json"
                )
                if df is not None and not df.empty:
                    return df
            except Exception as e:
                logger.debug(f"Standard load failed, trying direct load: {str(e)}")

            # Fallback to direct JSON loading
            with open(datafile) as f:
                data = json.load(f)
                
            if isinstance(data, list):
                df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
                df['date'] = pd.to_datetime(df['date'], unit='ms')
                df.set_index('date', inplace=True)
                return df
                
            return None
            
        except Exception as e:
            logger.warning(f"Data load failed for {pair}: {str(e)}")
            return None

    def ensure_pair_data(self, pair: str, days: int) -> Optional[pd.DataFrame]:
        """Ensure data exists with robust retry logic"""
        for attempt in range(1, self.max_retries + 1):
            logger.info(f"Processing {pair} (attempt {attempt}/{self.max_retries})")
            
            try:
                # Try loading existing data first
                df = self._load_data_safely(pair)
                if df is not None and len(df) >= days:
                    return df
                    
                # Download if needed
                if self._download_with_freqtrade(pair, days):
                    time.sleep(2)  # Allow time for file system sync
                    df = self._load_data_safely(pair)
                    if df is not None:
                        return df
                        
            except Exception as e:
                logger.warning(f"Attempt {attempt} failed for {pair}: {str(e)}")
                if attempt < self.max_retries:
                    wait_time = min(10 * attempt, 30)
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)

        logger.error(f"Failed to get valid data for {pair} after {self.max_retries} attempts")
        return None

    @property
    def version(self) -> str:
        """Get current manager version"""
        return self._version