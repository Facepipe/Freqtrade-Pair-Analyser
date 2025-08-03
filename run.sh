#!/bin/bash

# Quick run script with common parameters
echo "🚀 Running Freqtrade Pair Analyzer..."

# Default parameters
QUOTE_CURRENCY="USDT"
TIMEFRAME="1h"
WORKERS="4"
TOP_PAIRS="10"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -q|--quote)
            QUOTE_CURRENCY="$2"
            shift 2
            ;;
        -t|--timeframe)
            TIMEFRAME="$2"
            shift 2
            ;;
        -w|--workers)
            WORKERS="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -q, --quote CURRENCY    Quote currency (default: USDT)"
            echo "  -t, --timeframe TF      Timeframe (default: 1h)"
            echo "  -w, --workers N         Number of workers (default: 4)"
            echo "  -h, --help             Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "Configuration:"
echo "  Quote Currency: $QUOTE_CURRENCY"
echo "  Timeframe: $TIMEFRAME"
echo "  Workers: $WORKERS"
echo ""

python pair_analyzer.py \
    --quote "$QUOTE_CURRENCY" \
    --timeframe "$TIMEFRAME" \
    --workers "$WORKERS" \
    --top-pairs "$TOP_PAIRS" \
    --verbose
