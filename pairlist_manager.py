# FILENAME: pairlist_manager.py
# ACTION: CREATE NEW FILE
# DESCRIPTION: Utility for managing and viewing pairlists from config files

#!/usr/bin/env python3
"""
Pairlist Manager - Utility for managing Freqtrade pairlists
Version: 1.0.0

This utility helps you manage, view, and create pairlists for the analyzer
"""
import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.pairlist_handler import PairlistHandler

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Pairlist Manager - Manage Freqtrade pairlists',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all available configs
  python pairlist_manager.py --list --quote USDT
  
  # Show pairs from specific config
  python pairlist_manager.py --show strategy1 --quote USDT
  
  # Create a new pairlist config
  python pairlist_manager.py --create my-strategy --pairs BTC/USDT ETH/USDT ADA/USDT