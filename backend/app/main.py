import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
from typing import List, Optional
from dotenv import load_dotenv

# Load env vars for local dev
load_dotenv()

from . import database, models, engine

# Logger for the scheduler
logger = logging.getLogger("Scheduler")

# Background Task Loop
async def run_scheduler():
    """Runs the engine check every 300 seconds (5 minutes)."""
    while True:
        logger.info("⏳ Scheduler: Triggering check cycle...")
        try:
            # Run the synchronous engine logic in a thread pool
            await asyncio.to_thread(engine.run_checks)
        except Exception as e:
            logger.error(f"Scheduler Error: {e}")
        
        # Wait for 5 minutes before next check
        await asyncio.sleep(300) 

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the background loop
    asyncio.create_task(run_scheduler())
    yield
    # Shutdown logic (if any) can go here

app = FastAPI(title="Stock Notifier API", lifespan=lifespan)

@app.get("/")
def health_check():
    return {"status": "ok", "service": "Stock Notifier Backend"}


# --- WATCHLIST ENDPOINTS ---


@app.get("/watchlist", response_model=List[models.StockWatchResponse])
def get_watchlist():
    """Get all monitored stocks."""
    return database.get_watchlist()


@app.post("/watchlist", response_model=models.StockWatchResponse)
def add_to_watchlist(item: models.StockWatchRequest):
    """Add a stock to monitor."""
    # 1. Fetch Company Name (Metadata)
    company_name = engine.fetch_company_name(item.symbol)
    
    # 2. Add to DB
    return database.add_to_watchlist(
        item.symbol, 
        item.dma_period, 
        item.alert_threshold,
        company_name=company_name
    )


@app.delete("/watchlist/{symbol}")
def remove_from_watchlist(symbol: str):
    """Stop monitoring a stock."""
    success = database.remove_from_watchlist(symbol)
    if not success:
        raise HTTPException(status_code=404, detail="Stock not found")
    return {"status": "deleted", "symbol": symbol}


# --- DATA ENDPOINTS (For Charts) ---


@app.get("/stock/{symbol}/history", response_model=List[models.ChartDataPoint])
def get_stock_history(symbol: str):
    """
    Fetches full history + 3 DMAs for the frontend chart.
    """
    data = engine.fetch_stock_history(symbol.upper())
    if not data:
        raise HTTPException(status_code=404, detail="Stock data not found or API error")
    return data


# --- ALERT LOGS ---


@app.get("/logs", response_model=List[models.LogResponse])
def get_alert_logs(limit: int = 50):
    return database.get_logs(limit=limit)


# --- BACKGROUND TASKS ---


@app.post("/force-check")
def force_check_now(
    background_tasks: BackgroundTasks, x_admin_token: Optional[str] = Header(None)
):
    """
    Manually trigger an engine run. Protected by Admin Token.
    """
    expected_token = os.getenv("ADMIN_TOKEN")

    if expected_token and x_admin_token != expected_token:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid Admin Token")

    background_tasks.add_task(engine.run_checks)
    return {"status": "Check triggered in background"}
