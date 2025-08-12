# Stock Alert System

A free stock monitoring system that tracks your portfolio and sends email alerts.

## 📁 Project Structure
```
Stock_Alert/
├── stock_monitor.py    # Main monitoring script
├── requirements.txt    # Python dependencies
├── README.md          # Complete setup guide
├── setup.sh          # Quick setup script
└── stock_monitor.log  # Generated log file (after first run)
```

## 🚀 Quick Start

```bash
cd /Users/karanchanana/Repos/Learning/Stock_Alert
./setup.sh
```

## 📊 What it monitors
- **44 stocks** for daily drops >5%
- **3+ consecutive declining days**
- **Runs daily at 5:30 PM ET**
- **100% free** using Yahoo Finance + Gmail

## ⚙️ Features
- HTML email alerts with charts
- Smart weekend/holiday detection  
- Rate limiting for API calls
- Comprehensive logging
- Easy customization

Built with Python 3 using yfinance, pandas, and schedule libraries.
