# Stock Monitor

A FastAPI-based stock monitoring application that tracks stocks using Twelve Data API, calculates DMA (Displacement Moving Average), and sends email alerts.

## Project Structure

```
stock-monitor/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI entry point & Scheduler setup
│   │   ├── database.py        # SQLite connection (using sqlite-utils)
│   │   ├── models.py          # Data structures for Stocks/Alerts
│   │   ├── engine.py          # Twelve Data API calls & DMA Calculation
│   │   └── notifier.py        # SMTP/Email logic
│   ├── data/
│   │   └── stocks.db          # The SQLite database file
│   ├── requirements.txt       # Dependencies
│   ├── .env                   # API Keys and Email Credentials
│   └── Dockerfile             # Docker configuration
└── docker-compose.yml         # Docker Compose for easy deployment
```

## Setup Instructions

### 1. Configure Environment Variables

Edit `backend/.env` and add your credentials:

```env
# Twelve Data API Key
TWELVE_DATA_API_KEY=your_actual_api_key

# Email Credentials (Gmail example)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=recipient@example.com
```

### 2. Local Development Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn app.main:app --reload
```

The API will be available at: `http://localhost:8000`

### 3. Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Features

- ✅ Stock price monitoring via Twelve Data API
- ✅ DMA (Displacement Moving Average) calculations
- ✅ SQLite database for storing stock data and alerts
- ✅ Automated scheduler for periodic checks
- ✅ Email notifications via SMTP
- ✅ RESTful API with FastAPI
- ✅ Docker support for easy deployment

## Requirements

- Python 3.11+
- Twelve Data API Key
- SMTP-enabled email account (Gmail, etc.)

## Notes

- For Gmail SMTP, you need to use an App Password (not your regular password)
- The scheduler will run automatically when the application starts
- Database is created automatically on first run
