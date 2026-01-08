import sqlite_utils
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "stock_monitor.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_db() -> sqlite_utils.Database:
    """Get database connection with WAL enabled."""
    db = sqlite_utils.Database(DB_PATH)
    db.enable_wal()
    return db


# ============= WATCH LIST OPERATIONS =============


def add_to_watchlist(
    symbol: str, dma_period: int, alert_threshold: float, company_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add or update a stock in the watch list.
    """
    db = get_db()
    table = db["watch_list"]
    symbol = symbol.upper()

    record = {
        "symbol": symbol,
        "dma_period": dma_period,
        "alert_threshold": alert_threshold,
        "company_name": company_name,
        "last_price": 0.0,
        "change": 0.0,
        "change_percent": 0.0,
        "last_dma": 0.0,
        "last_checked": datetime.utcnow().isoformat(),
    }

    # Check if exists to preserve state
    existing = get_watchlist_item(symbol)
    if existing:
        record["last_price"] = existing.get("last_price", 0.0)
        record["last_dma"] = existing.get("last_dma", 0.0)

    table.upsert(record, pk="symbol")
    return table.get(symbol)


def get_watchlist_item(symbol: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    try:
        return db["watch_list"].get(symbol.upper())
    except sqlite_utils.db.NotFoundError:
        return None


def update_market_state(
    symbol: str, price: float, dma: float, change: float = 0.0, change_percent: float = 0.0
) -> None:
    """
    Updates both Price and DMA after a check cycle.
    Preserves 'Previous State' for the next run.
    """
    db = get_db()
    db["watch_list"].update(
        symbol.upper(),
        {
            "last_price": price,
            "last_dma": dma,
            "change": change,
            "change_percent": change_percent,
            "last_checked": datetime.utcnow().isoformat(),
        },
    )


def get_watchlist() -> List[Dict[str, Any]]:
    db = get_db()
    return list(db["watch_list"].rows_where(order_by="symbol"))


def remove_from_watchlist(symbol: str) -> bool:
    db = get_db()
    try:
        db["watch_list"].delete(symbol.upper())
        return True
    except sqlite_utils.db.NotFoundError:
        return False


# ============= LOGS OPERATIONS =============


def add_log(symbol: str, message: str, alert_type: str = "INFO") -> Dict[str, Any]:
    db = get_db()
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "symbol": symbol.upper(),
        "message": message,
        "alert_type": alert_type,
    }
    db["logs"].insert(record)
    return record


def get_logs(limit: int = 100) -> List[Dict[str, Any]]:
    db = get_db()
    return list(db["logs"].rows_where(order_by="-timestamp", limit=limit))


def clear_old_logs(days: int = 30) -> int:
    db = get_db()
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    result = db.execute("DELETE FROM logs WHERE timestamp < ?", [cutoff])
    return result.rowcount


# ============= INITIALIZATION =============


def initialize_database() -> None:
    db = get_db()

    if "watch_list" not in db.table_names():
        db["watch_list"].create(
            {
                "symbol": str,
                "dma_period": int,
                "alert_threshold": float,
                "company_name": str,
                "last_price": float,
                "change": float,
                "change_percent": float,
                "last_dma": float,
                "last_checked": str,
            },
            pk="symbol",
        )

    # Migration: Add 'last_dma' column if it's missing
    table = db["watch_list"]
    if "last_dma" not in table.columns_dict:
        table.add_column("last_dma", float)
    if "company_name" not in table.columns_dict:
        table.add_column("company_name", str)
    if "change" not in table.columns_dict:
        table.add_column("change", float)
    if "change_percent" not in table.columns_dict:
        table.add_column("change_percent", float)

    if "logs" not in db.table_names():
        db["logs"].create(
            {
                "id": int, 
                "timestamp": str, 
                "symbol": str, 
                "message": str, 
                "alert_type": str
            }, 
            pk="id"
        )
        db["logs"].create_index(["timestamp", "symbol"])

    # Migration: Add 'alert_type' to logs
    if "alert_type" not in db["logs"].columns_dict:
        db["logs"].add_column("alert_type", str)
        # Backfill existing values
        db["logs"].update_where("alert_type IS NULL", {"alert_type": "INFO"})


initialize_database()
