"""Data Infrastructure Workflows for AFC3."""
import asyncio
import sys
sys.path.insert(0, '.')

from data.data_service import get_data_service
from data.storage.market_data_store import get_market_data_store, get_feature_store
from data.features.feature_engine import get_feature_engine

async def workflow_j():
    """Workflow J - Data Ingestion"""
    print("="*50)
    print("WORKFLOW J: Data Ingestion")
    print("="*50)
    
    service = get_data_service()
    
    # Fetch historical data
    print("\n[1/3] Fetching historical SPY data...")
    spy_data = await service.get_historical_data(
        "SPY", "2024-01-01", "2024-03-01", "1d"
    )
    print(f"  Fetched {len(spy_data)} bars")
    
    # Fetch crypto data
    print("\n[2/3] Fetching historical BTC data...")
    btc_data = await service.get_historical_data(
        "BTC", "2024-01-01", "2024-03-01", "1d", "crypto"
    )
    print(f"  Fetched {len(btc_data)} bars")
    
    # Get latest price
    print("\n[3/3] Getting latest prices...")
    for sym in ["SPY", "BTC", "AAPL"]:
        price = await service.get_latest_price(sym)
        print(f"  {sym}: ${price['price']:.2f}")
    
    return {"status": "success", "spy_bars": len(spy_data), "btc_bars": len(btc_data)}

async def workflow_k():
    """Workflow K - Feature Generation"""
    print("="*50)
    print("WORKFLOW K: Feature Generation")
    print("="*50)
    
    service = get_data_service()
    feature_engine = get_feature_engine()
    
    # Get data
    print("\n[1/2] Fetching data for feature computation...")
    bars = await service.get_historical_data("SPY", "2024-01-01", "2024-03-01", "1d")
    print(f"  Fetched {len(bars)} bars")
    
    # Compute features
    print("\n[2/2] Computing features...")
    from data.schemas.market_data import OHLCVData
    ohlcv = [OHLCVData.from_dict(b) for b in bars]
    
    features = feature_engine.compute_features_for_bars(ohlcv, ["sma", "zscore", "rsi", "momentum"])
    print(f"  Computed {len(features)} features")
    
    for f in features:
        print(f"    {f.feature_name}: {f.value:.4f}")
    
    return {"status": "success", "features_computed": len(features)}

async def workflow_l():
    """Workflow L - Backtest with Data Layer"""
    print("="*50)
    print("WORKFLOW L: Backtest with Data Layer")
    print("="*50)
    
    service = get_data_service()
    
    # Get data
    print("\n[1/3] Getting historical data...")
    bars = await service.get_historical_data("SPY", "2024-01-01", "2024-06-01", "1d")
    print(f"  Got {len(bars)} bars")
    
    # Get features
    print("\n[2/3] Computing features...")
    features = await service.get_feature_set("SPY", ["sma", "zscore"], period=200)
    print(f"  Features: {features.get('cached', True)}")
    
    # Simple backtest
    print("\n[3/3] Running backtest...")
    closes = [b['close'] for b in bars]
    sma_20 = sum(closes[-20:]) / 20
    
    signal = "BUY" if closes[-1] > sma_20 else "SELL"
    pnl = (closes[-1] - closes[0]) / closes[0] * 100
    
    print(f"  Signal: {signal}")
    print(f"  P&L: {pnl:.2f}%")
    
    return {"status": "success", "signal": signal, "pnl": pnl}

async def main():
    print("Data Infrastructure Workflows")
    print("="*50)
    
    result_j = await workflow_j()
    print(f"\nResult J: {result_j['status']}")
    
    result_k = await workflow_k()
    print(f"\nResult K: {result_k['status']}")
    
    result_l = await workflow_l()
    print(f"\nResult L: {result_l['status']}")
    
    print("\n" + "="*50)
    print("Data workflows complete!")

if __name__ == "__main__":
    asyncio.run(main())
