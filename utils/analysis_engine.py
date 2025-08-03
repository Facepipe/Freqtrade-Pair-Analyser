"""
Analysis Engine - Versioned Implementation
Version History:
• v1.0.4 - Added version property for compatibility
• v1.0.3 - Enhanced type hints and documentation
• v1.0.2 - Added proper typing imports
• v1.0.1 - Initial version split from analyzer_core
"""
from typing import Dict, Optional, List
import pandas as pd
import talib.abstract as ta
import numpy as np
import logging

logger = logging.getLogger(__name__)

class AnalysisEngine:
    CURRENT_VERSION = "1.0.4"
    
    def __init__(
        self,
        min_data_quality: float = 0.3,
        max_null_percentage: float = 0.2,
        top_pairs_count: int = 10,
        least_pairs_count: int = 10,
        timeframe: str = '1h'
    ):
        self._version = self.CURRENT_VERSION
        self.min_data_quality = min_data_quality
        self.max_null_percentage = max_null_percentage
        self.top_pairs_count = top_pairs_count
        self.least_pairs_count = least_pairs_count
        self.timeframe = timeframe
        logger.info(f"AnalysisEngine v{self._version} initialized with timeframe={self.timeframe}, top_pairs={self.top_pairs_count}, least_pairs={self.least_pairs_count}")

    @property
    def version(self) -> str:
        """Get current engine version"""
        return self._version

    def _calculate_volatility(self, dataframe: pd.DataFrame) -> float:
        """Calculate annualized volatility from OHLCV data"""
        try:
            returns = np.log(dataframe['close'] / dataframe['close'].shift(1))
            volatility = returns.rolling(window=min(14, len(returns))).std().mean()
            
            # Handle NaN values
            if pd.isna(volatility):
                return 0.0
                
            # Annualize based on timeframe
            timeframe_multipliers = {
                '1m': np.sqrt(525600),   # minutes in a year
                '5m': np.sqrt(105120),   # 5-min periods in a year
                '15m': np.sqrt(35040),   # 15-min periods in a year
                '1h': np.sqrt(8760),     # hours in a year
                '4h': np.sqrt(2190),     # 4-hour periods in a year
                '1d': np.sqrt(365),      # days in a year
            }
            
            multiplier = timeframe_multipliers.get(self.timeframe, np.sqrt(365))
            return float(volatility * multiplier)
            
        except Exception as e:
            logger.warning(f"Error calculating volatility: {e}")
            return 0.0

    def _calculate_coral_score(self, dataframe: pd.DataFrame) -> float:
        """Calculate Coral Trend effectiveness score"""
        try:
            if len(dataframe) < 20:
                return 0.0
                
            length = min(20, len(dataframe) // 2)
            diff = dataframe['close'].diff(length)
            std = dataframe['close'].rolling(length).std()
            
            # Avoid division by zero
            coral = diff / (std * np.sqrt(length) + 1e-8)
            score = (coral.abs() > 1.0).mean()
            
            return float(score) if not pd.isna(score) else 0.0
            
        except Exception as e:
            logger.warning(f"Error calculating coral score: {e}")
            return 0.0

    def _calculate_stc_score(self, dataframe: pd.DataFrame) -> float:
        """Calculate Schaff Trend Cycle effectiveness"""
        try:
            if len(dataframe) < 50:
                return 0.0
                
            # Calculate MACD with error handling
            try:
                ema_fast = ta.EMA(dataframe, timeperiod=min(23, len(dataframe)//3))
                ema_slow = ta.EMA(dataframe, timeperiod=min(50, len(dataframe)//2))
                macd = ema_fast - ema_slow
            except Exception:
                # Fallback to simple moving averages
                macd = dataframe['close'].rolling(12).mean() - dataframe['close'].rolling(26).mean()
            
            # Calculate stochastic oscillator of MACD
            window = min(10, len(macd)//5)
            if window < 2:
                return 0.0
                
            macd_min = macd.rolling(window).min()
            macd_max = macd.rolling(window).max()
            
            # Avoid division by zero
            denominator = macd_max - macd_min
            stoch = 100 * (macd - macd_min) / (denominator + 1e-8)
            
            score = stoch.diff().abs().mean()
            return float(score) if not pd.isna(score) else 0.0
            
        except Exception as e:
            logger.warning(f"Error calculating STC score: {e}")
            return 0.0

    def check_data_quality(self, dataframe: pd.DataFrame) -> bool:
        """Validate data meets minimum quality thresholds"""
        try:
            if dataframe.empty:
                return False
                
            # Check minimum length
            if len(dataframe) < len(dataframe) * self.min_data_quality:
                return False
                
            # Check for excessive null values
            null_pct = dataframe.isnull().mean().max()
            if null_pct > self.max_null_percentage:
                return False
                
            # Check for valid OHLCV data
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in dataframe.columns for col in required_columns):
                return False
                
            # Check for reasonable price data (no negatives, etc.)
            price_columns = ['open', 'high', 'low', 'close']
            for col in price_columns:
                if (dataframe[col] <= 0).any():
                    return False
                    
            return True
            
        except Exception as e:
            logger.warning(f"Error checking data quality: {e}")
            return False

    def analyze_dataframe(self, dataframe: pd.DataFrame, pair: str) -> Optional[Dict[str, float]]:
        """Analyze prepared OHLCV dataframe"""
        try:
            if not self.check_data_quality(dataframe):
                logger.warning(f"Data quality check failed for {pair}")
                return None

            # Calculate ADX with error handling
            try:
                adx_value = ta.ADX(dataframe, timeperiod=min(14, len(dataframe)//3)).mean()
                trend_strength = float(adx_value) if not pd.isna(adx_value) else 0.0
            except Exception as e:
                logger.debug(f"ADX calculation failed for {pair}, using fallback: {e}")
                # Fallback trend calculation
                price_change = dataframe['close'].pct_change().abs().mean()
                trend_strength = float(price_change * 100) if not pd.isna(price_change) else 0.0

            # Calculate volume score with error handling
            try:
                volume_score = float(np.log1p(dataframe['volume'].mean()))
                if pd.isna(volume_score):
                    volume_score = 0.0
            except Exception:
                volume_score = 0.0

            result = {
                'pair': pair,
                'volatility': self._calculate_volatility(dataframe),
                'trend_strength': trend_strength,
                'volume_score': volume_score,
                'coral_score': self._calculate_coral_score(dataframe),
                'stc_score': self._calculate_stc_score(dataframe),
                'data_points': len(dataframe),
                'data_quality': float(1 - dataframe.isnull().mean().mean()),
                'timeframe': self.timeframe
            }
            
            # Validate all values are numeric and not NaN
            for key, value in result.items():
                if isinstance(value, (int, float)) and (pd.isna(value) or not np.isfinite(value)):
                    result[key] = 0.0
            
            return result
            
        except Exception as e:
            logger.error(f"Analysis error for {pair}: {str(e)}")
            return None

    def generate_report(self, results: List[Dict], failed_pairs: List[str]) -> Dict:
        """
        Generate a report including top and least volatile pairs.
        """
        try:
            if not results:
                return {
                    'total_pairs': len(failed_pairs),
                    'successful_pairs': 0,
                    'failed_pairs': len(failed_pairs),
                    'top_pairs': [],
                    'least_volatile_pairs': []
                }
            
            sorted_by_volatility = sorted(results, key=lambda x: x.get('volatility', 0), reverse=True)
            top_pairs = [res['pair'] for res in sorted_by_volatility[:self.top_pairs_count]]
            least_pairs = [res['pair'] for res in sorted_by_volatility[-self.least_pairs_count:]] if self.least_pairs_count > 0 else []

            return {
                'total_pairs': len(results) + len(failed_pairs),
                'successful_pairs': len(results),
                'failed_pairs': len(failed_pairs),
                'top_pairs': top_pairs,
                'least_volatile_pairs': least_pairs,
                'engine_version': self._version
            }
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {
                'total_pairs': len(failed_pairs),
                'successful_pairs': 0,
                'failed_pairs': len(failed_pairs),
                'top_pairs': [],
                'least_volatile_pairs': [],
                'error': str(e)
            }