import os
import time
import logging
from typing import Dict, Any, Optional, List

from twelvedata import TDClient
from . import database
from . import notifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StockEngine")

# Validate API Key on startup (Fixed variable name to match README)
API_KEY = os.environ.get("TWELVE_DATA_API_KEY")
if not API_KEY:
    # Fallback to check if user used the other name
    API_KEY = os.environ.get("TWELVEDATA_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "CRITICAL: TWELVE_DATA_API_KEY is not set in environment variables."
    )

TD = TDClient(apikey=API_KEY)
RATE_LIMIT_DELAY = 10  # Seconds between API calls to avoid limits

# --- CORE DATA FETCHING ---


def fetch_stock_history(symbol: str, days: int = 300) -> List[Dict[str, Any]]:
    """
    Fetches full OHLC + 3 DMAs for the frontend Chart.
    """
    try:
        ts = (
            TD.time_series(symbol=symbol, interval="1day", outputsize=days)
            .with_sma(time_period=50)
            .with_sma(time_period=100)
            .with_sma(time_period=200)
        )
        data = ts.as_json()
    except Exception as e:
        logger.error(f"History fetch failed for {symbol}: {e}")
        return []

    records = []
    for row in data:
        records.append(
            {
                "date": row["datetime"][:10],
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "dma50": float(row["sma"]) if row.get("sma") else None,
                "dma100": float(row["sma1"]) if row.get("sma1") else None,
                "dma200": float(row["sma2"]) if row.get("sma2") else None,
            }
        )

    # Frontend expects Oldest -> Newest
    records.reverse()
    return records


def fetch_company_name(symbol: str) -> Optional[str]:
    """
    Fetches the company name using Twelve Data's symbol search or quote.
    """
    try:
        # Quote is lightweight and usually contains the name
        q = TD.quote(symbol=symbol)
        data = q.as_json()
        return data.get("name")
    except Exception as e:
        logger.error(f"Company name fetch failed for {symbol}: {e}")
        return None


def fetch_latest_snapshot(symbol: str, dma_period: int) -> Optional[Dict[str, Any]]:
    """
    Lightweight fetch for the Alert Engine.
    """
    try:
        ts = TD.time_series(symbol=symbol, interval="1day", outputsize=30).with_sma(
            time_period=dma_period
        )
        data = ts.as_json()
        latest = data[0]
        
        # Calculate daily change if possible
        change = 0.0
        change_percent = 0.0
        
        if len(data) > 1:
            prev_close = float(data[1]["close"])
            curr_close = float(latest["close"])
            change = curr_close - prev_close
            change_percent = (change / prev_close) * 100.0

        return {
            "symbol": symbol,
            "price": float(latest["close"]),
            "dma": float(latest["sma"]),
            "change": change,
            "change_percent": change_percent,
            "datetime": latest["datetime"],
            "dma_period": dma_period,
        }
    except Exception as e:
        logger.error(f"Snapshot fetch failed for {symbol}: {e}")
        return None


# --- ALERT LOGIC ---


def check_crossover(
    watchlist_item: Dict[str, Any], current_data: Dict[str, Any]
) -> None:
    symbol = watchlist_item["symbol"]
    period = watchlist_item["dma_period"]
    threshold_percent = watchlist_item["alert_threshold"]

    # 1. Get Previous State
    prev_price = watchlist_item.get("last_price")
    prev_dma = watchlist_item.get("last_dma")

    # 2. Get Current State
    curr_price = current_data["price"]
    curr_dma = current_data["dma"]
    change = current_data.get("change", 0.0)
    change_p = current_data.get("change_percent", 0.0)

    # 3. Bootstrap (First Run)
    if not prev_price or not prev_dma:
        logger.info(f"{symbol}: Bootstrapping state (Price: {curr_price})")
        database.update_market_state(symbol, curr_price, curr_dma, change, change_p)
        return

    # 4. Crossover Detection
    crossed_above = (prev_price < prev_dma) and (curr_price > curr_dma)
    crossed_below = (prev_price > prev_dma) and (curr_price < curr_dma)

    if crossed_above or crossed_below:
        # Check Threshold (Noise Filter)
        distance = abs(curr_price - curr_dma) / curr_dma
        required_distance = threshold_percent / 100.0

        if distance < required_distance:
            # FIX: Do NOT update state. 
            # We want to keep the "old" price (on the other side of DMA) as the reference
            # until the price moves explicitly beyond the threshold.
            logger.info(
                f"{symbol}: Weak cross ignored ({distance:.2%} < {required_distance:.2%}). Keeping previous state."
            )
            return

        # Trigger Logic & Explicit State Update
        # Trigger Logic & Explicit State Update
        if crossed_above:
            msg = f"Price crossed ABOVE {period} DMA"
            _trigger(symbol, curr_price, period, curr_dma, "crossed above", msg, "BULLISH")
            database.update_market_state(symbol, curr_price, curr_dma, change, change_p)
            return

        elif crossed_below:
            msg = f"Price crossed BELOW {period} DMA"
            _trigger(symbol, curr_price, period, curr_dma, "crossed below", msg, "BEARISH")
            database.update_market_state(symbol, curr_price, curr_dma, change, change_p)
            return

    # 5. Save State (No cross occurred)
    # Only update if no potential cross is pending validation, or simply update regular tracking.
    database.update_market_state(symbol, curr_price, curr_dma, change, change_p)


def _trigger(symbol, price, period, dma, condition, message, alert_type="INFO"):
    logger.warning(f"TRIGGER: {message} ({alert_type})")
    database.add_log(symbol, message, alert_type)
    notifier.send_alert_email(symbol, price, period, dma, condition)


def run_checks():
    """Single Run of the Alert Loop (Stateless)."""
    logger.info("--- Engine Cycle Start ---")
    watchlist = database.get_watchlist()

    if not watchlist:
        logger.info("Watchlist empty.")
        return

    for item in watchlist:
        logger.info(f"Checking {item['symbol']}...")
        data = fetch_latest_snapshot(item["symbol"], item["dma_period"])
        if data:
            check_crossover(item, data)
        time.sleep(RATE_LIMIT_DELAY)

    logger.info("--- Engine Cycle End ---")


if __name__ == "__main__":
    run_checks()
