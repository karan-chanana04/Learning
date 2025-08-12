# Free Stock Monitoring System - Setup Guide

## 🎯 Features
- **100% Free**: Uses free APIs and services only
- **44 Stocks**: Monitors your complete portfolio
- **Dual Alerts**: Daily drops >5% + 3-day consecutive declines
- **Email Notifications**: HTML-formatted alerts with charts
- **Smart Scheduling**: Runs after market close (5:30 PM ET)
- **Local Deployment**: No cloud costs

## 📋 Requirements

### 1. Install Python Dependencies
Install from the included requirements.txt:

```bash
pip install -r requirements.txt
```

### 2. Gmail Setup (Free Email Service)

1. **Enable 2FA on Gmail**: Required for App Passwords
   - Go to Google Account settings
   - Security → 2-Step Verification → Turn On

2. **Create App Password**:
   - Visit: https://myaccount.google.com/apppasswords
   - Select "Mail" and generate password
   - Copy the 16-character password (no spaces)

### 3. Environment Variables Setup

#### Mac/Linux:
```bash
export EMAIL_USER="your-gmail@gmail.com"
export EMAIL_PASS="your-16-digit-app-password"
export TO_EMAIL="recipient@email.com"
```

You can also add these to your `~/.bash_profile` or `~/.zshrc`:
```bash
echo 'export EMAIL_USER="your-gmail@gmail.com"' >> ~/.zshrc
echo 'export EMAIL_PASS="your-16-digit-app-password"' >> ~/.zshrc
echo 'export TO_EMAIL="recipient@email.com"' >> ~/.zshrc
source ~/.zshrc
```

#### Windows (Command Prompt):
```cmd
set EMAIL_USER=your-gmail@gmail.com
set EMAIL_PASS=your-16-digit-app-password
set TO_EMAIL=recipient@email.com
```

#### Windows (PowerShell):
```powershell
$env:EMAIL_USER="your-gmail@gmail.com"
$env:EMAIL_PASS="your-16-digit-app-password"
$env:TO_EMAIL="recipient@email.com"
```

## 🚀 Running the System

### 1. Navigate to Directory
```bash
cd /Users/karanchanana/Repos/Learning/Stock_Alert
```

### 2. Test Run First
```bash
python3 stock_monitor.py --test
```

This runs an immediate check to verify everything works.

### 3. Start Scheduled Monitoring
```bash
python3 stock_monitor.py
```

The system will:
- Run daily at 5:30 PM ET
- Monitor all 44 stocks
- Send email alerts when conditions are met
- Log all activity to `stock_monitor.log`

## 📅 Scheduling Options

### Option 1: Keep Script Running (Recommended)
- Simple: Just run `python3 stock_monitor.py`
- The script handles scheduling internally
- Runs continuously, checks every minute for scheduled time

### Option 2: Mac Cron Job
```bash
# Edit crontab
crontab -e

# Add this line (runs at 5:30 PM Monday-Friday)
30 17 * * 1-5 cd /Users/karanchanana/Repos/Learning/Stock_Alert && /usr/bin/python3 stock_monitor.py --test
```

## 📧 Email Alert Example

You'll receive HTML emails with tables showing:

**Daily Drops (>5%)**
| Ticker | Change % | Current Price | Previous Close | Chart |
|--------|----------|---------------|----------------|-------|
| TSLA   | -7.25%   | $245.67       | $264.89        | View  |

**3+ Day Consecutive Declines**
| Ticker | Days Down | Current Price | Total Decline % | Chart |
|--------|-----------|---------------|-----------------|-------|
| NVDA   | 4         | $112.34       | -12.45%        | View  |

## 🔧 Customization

### Change Alert Thresholds:
```python
# In the StockMonitor.__init__() method:
self.daily_drop_threshold = 0.03  # Change to 3%
self.consecutive_days = 4         # Change to 4 days
```

### Change Schedule Time:
```python
# In setup_scheduler() function:
schedule.every().day.at("16:00").do(monitor.run_monitoring_cycle)  # 4 PM ET
```

### Add More Stocks:
```python
# Add to TICKERS list:
TICKERS = [
    'ADBE', 'AMD', # ... existing stocks
    'COIN', 'SQ', 'PYPL'  # Add new ones
]
```

## 🛠️ Troubleshooting

### "Gmail Authentication Failed"
- Verify App Password is correct (16 digits, no spaces)
- Ensure 2FA is enabled on Gmail
- Check environment variables are set: `echo $EMAIL_USER`

### "No Stock Data"
- Yahoo Finance might be temporarily down
- Check internet connection
- Script will retry on next scheduled run

### "No Alerts Sent"
- This is normal! Alerts only send when conditions are met
- Check log file for "No alerts triggered" message

### Script Stops Running
- Check log file for errors
- Restart the script
- Consider using cron job instead

## 💡 Tips for Best Results

1. **Run After Market Close**: Default 5:30 PM ET gives time for all data to update
2. **Check Logs Regularly**: Monitor `stock_monitor.log` for any issues  
3. **Test Email**: Run `--test` occasionally to ensure emails work
4. **Keep Computer On**: For continuous monitoring, don't let computer sleep
5. **Backup Configuration**: Save your environment variables and script

## 🆓 Cost Breakdown
- **yfinance API**: Free (Yahoo Finance data)
- **Gmail**: Free (for personal use)
- **Python**: Free
- **Local hosting**: Free (uses your computer)
- **Total monthly cost**: $0.00

## 📈 Next Steps

Once running successfully, consider these free enhancements:
- Add more stocks to monitor
- Create different alert thresholds for different stock categories
- Add basic data logging to track alert frequency
- Set up phone notifications using free services like Pushover (limited free tier)

Your free stock monitoring system is now ready to help you stay on top of your 44-stock portfolio! 🚀
