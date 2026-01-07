# Stock Monitor

A FastAPI-based stock monitoring application that tracks stocks using Twelve Data API, calculates DMA (Displacement Moving Average), and sends email alerts.

## Project Structure

```
stock-monitor/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI entry point & Scheduler setup
│   │   ├── database.py        # SQLite connection
│   │   ├── models.py          # Pydantic Models
│   │   ├── engine.py          # Twelve Data API & Logic
│   │   └── notifier.py        # Email logic
│   ├── data/
│   │   └── stock_monitor.db   # SQLite database
│   ├── requirements.txt
│   ├── .env                   # Credentials
│   └── Dockerfile
└── docker-compose.yml
```

## Setup Instructions

### 1. Configure Environment Variables

Create `backend/.env` with the following content:

```env
# Twelve Data API Key
TWELVE_DATA_API_KEY=your_actual_api_key

# Email Credentials (Gmail example)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Email Routing
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=recipient@example.com

# Optional
CHART_URL=http://localhost:3000/chart
ADMIN_TOKEN=secret_token_for_force_check
```

### 2. Local Development Setup

```bash
cd backend

# Create & Activate Virtual Env
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install Dependencies
pip install -r requirements.txt

# Run App (Scheduler starts automatically)
uvicorn app.main:app --reload
```

The API will be available at: `http://localhost:8000`
