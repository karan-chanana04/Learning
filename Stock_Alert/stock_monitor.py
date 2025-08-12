#!/usr/bin/env python3
"""
Free Stock Monitoring & Notification System
- Uses yfinance (free Yahoo Finance API)
- Gmail for notifications (free)
- Local scheduling (no cloud costs)
- Monitors 44 stocks for daily drops >5% and 3-day consecutive declines
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule
import time
import os
import logging
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stock_monitor.log'),
        logging.StreamHandler()
    ]
)

# Your 44 stock tickers
TICKERS = [
    'ADBE', 'AMD', 'GOOG', 'AMZN', 'AXP', 'AAPL', 'CLSK', 'CRWD', 
    'CVS', 'DDOG', 'DEFT', 'ELV', 'XOM', 'FIG', 'HAL', 'HUM', 
    'INTC', 'LMT', 'LCID', 'META', 'MSFT', 'NVTS', 'NVDA', 'PLTR', 
    'RIVN', 'HOOD', 'RCKT', 'SLB', 'SNOW', 'SOFI', 'TSLA', 'UNH', 
    'VOO', 'WMT', 'BAC', 'SMCI', 'SNAP', 'CVX', 'GOOGL', 'VTI', 
    'JPM', 'RDDT', 'BITF', 'WFC'  # Added one more to reach 44
]

class StockMonitor:
    def __init__(self):
        # Email configuration - set these as environment variables
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.email_user = os.getenv("EMAIL_USER")  # Your Gmail address
        self.email_pass = os.getenv("EMAIL_PASS")  # Gmail App Password
        self.to_email = os.getenv("TO_EMAIL", self.email_user)  # Recipient email
        
        # Thresholds
        self.daily_drop_threshold = 0.05  # 5%
        self.consecutive_days = 3
        
    def is_market_day(self) -> bool:
        """Check if today is a market day (Monday-Friday, basic check)"""
        today = datetime.now()
        return today.weekday() < 5  # 0-4 are Mon-Fri
    
    def check_daily_drop(self, ticker: str) -> Optional[Dict]:
        """Check if stock dropped more than threshold today"""
        try:
            stock = yf.Ticker(ticker)
            # Get 5 days to ensure we have at least 2 trading days
            hist = stock.history(period="5d")
            
            if len(hist) >= 2:
                current_price = hist['Close'].iloc[-1]
                previous_close = hist['Close'].iloc[-2]
                daily_change = (current_price - previous_close) / previous_close
                
                if daily_change <= -self.daily_drop_threshold:
                    logging.info(f"📉 {ticker}: {daily_change*100:.2f}% drop detected")
                    return {
                        'ticker': ticker,
                        'change_percent': daily_change * 100,
                        'current_price': current_price,
                        'previous_close': previous_close
                    }
        except Exception as e:
            logging.error(f"Error checking daily drop for {ticker}: {e}")
        return None

    def check_consecutive_decline(self, ticker: str) -> Optional[Dict]:
        """Check if stock declined for consecutive days"""
        try:
            stock = yf.Ticker(ticker)
            # Get 10 days to ensure we have enough trading days
            hist = stock.history(period="10d")
            
            if len(hist) >= self.consecutive_days + 1:
                consecutive_down = 0
                
                # Check from most recent day backwards
                for i in range(len(hist) - 1, 0, -1):
                    if hist['Close'].iloc[i] < hist['Close'].iloc[i-1]:
                        consecutive_down += 1
                    else:
                        break
                        
                if consecutive_down >= self.consecutive_days:
                    logging.info(f"📊 {ticker}: {consecutive_down} consecutive down days")
                    return {
                        'ticker': ticker,
                        'consecutive_days': consecutive_down,
                        'current_price': hist['Close'].iloc[-1],
                        'start_price': hist['Close'].iloc[-(consecutive_down+1)],
                        'total_decline': ((hist['Close'].iloc[-1] - hist['Close'].iloc[-(consecutive_down+1)]) / hist['Close'].iloc[-(consecutive_down+1)]) * 100
                    }
        except Exception as e:
            logging.error(f"Error checking consecutive decline for {ticker}: {e}")
        return None
    def create_email_content(self, alerts_data: Dict) -> str:
        """Create HTML email content"""
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .negative {{ color: #d32f2f; font-weight: bold; }}
                .ticker {{ font-weight: bold; color: #1976d2; }}
            </style>
        </head>
        <body>
            <h2>🚨 Stock Alert Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S ET')}</h2>
        """
        
        # Daily drops section
        if alerts_data['daily_drops']:
            html_content += """
            <h3>📉 Daily Drops (>5%)</h3>
            <table>
                <tr>
                    <th>Ticker</th>
                    <th>Change %</th>
                    <th>Current Price</th>
                    <th>Previous Close</th>
                    <th>Chart</th>
                </tr>
            """
            
            for alert in alerts_data['daily_drops']:
                chart_link = f"https://finance.yahoo.com/quote/{alert['ticker']}"
                html_content += f"""
                <tr>
                    <td class="ticker">{alert['ticker']}</td>
                    <td class="negative">{alert['change_percent']:.2f}%</td>
                    <td>${alert['current_price']:.2f}</td>
                    <td>${alert['previous_close']:.2f}</td>
                    <td><a href="{chart_link}" target="_blank">View Chart</a></td>
                </tr>
                """
            html_content += "</table><br>"
        
        # Consecutive declines section
        if alerts_data['consecutive_declines']:
            html_content += """
            <h3>📊 3+ Day Consecutive Declines</h3>
            <table>
                <tr>
                    <th>Ticker</th>
                    <th>Days Down</th>
                    <th>Current Price</th>
                    <th>Total Decline %</th>
                    <th>Chart</th>
                </tr>
            """
            
            for alert in alerts_data['consecutive_declines']:
                chart_link = f"https://finance.yahoo.com/quote/{alert['ticker']}"
                html_content += f"""
                <tr>
                    <td class="ticker">{alert['ticker']}</td>
                    <td>{alert['consecutive_days']}</td>
                    <td>${alert['current_price']:.2f}</td>
                    <td class="negative">{alert['total_decline']:.2f}%</td>
                    <td><a href="{chart_link}" target="_blank">View Chart</a></td>
                </tr>
                """
            html_content += "</table>"
        
        html_content += """
            <hr>
            <p><small>This alert was generated by your Free Stock Monitor System</small></p>
        </body>
        </html>
        """
        
        return html_content

    def send_email_alert(self, alerts_data: Dict) -> bool:
        """Send email alert with stock alerts"""
        if not (self.email_user and self.email_pass):
            logging.error("Email credentials not configured. Set EMAIL_USER and EMAIL_PASS environment variables.")
            return False
            
        if not (alerts_data['daily_drops'] or alerts_data['consecutive_declines']):
            return True  # No alerts to send
        
        try:
            # Create email
            subject = f"🚨 Stock Alerts - {len(alerts_data['daily_drops'])} drops, {len(alerts_data['consecutive_declines'])} declines"
            html_content = self.create_email_content(alerts_data)
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_user
            msg['To'] = self.to_email
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_pass)
                server.send_message(msg)
            
            logging.info(f"✉️ Alert email sent successfully to {self.to_email}")
            return True
            
        except Exception as e:
            logging.error(f"Error sending email: {e}")
            return False
    def run_monitoring_cycle(self):
        """Main monitoring function"""
        if not self.is_market_day():
            logging.info("Weekend detected, skipping monitoring")
            return
        
        logging.info(f"🔍 Starting stock monitoring cycle for {len(TICKERS)} stocks")
        
        alerts_data = {
            'daily_drops': [],
            'consecutive_declines': []
        }
        
        # Check each ticker
        for i, ticker in enumerate(TICKERS):
            logging.info(f"Checking {ticker} ({i+1}/{len(TICKERS)})")
            
            # Check for daily drops
            drop_alert = self.check_daily_drop(ticker)
            if drop_alert:
                alerts_data['daily_drops'].append(drop_alert)
            
            # Check for consecutive declines
            decline_alert = self.check_consecutive_decline(ticker)
            if decline_alert:
                alerts_data['consecutive_declines'].append(decline_alert)
            
            # Rate limiting to be nice to Yahoo Finance
            time.sleep(0.5)  # Wait 0.5 seconds between requests
        
        # Send alerts if any found
        total_alerts = len(alerts_data['daily_drops']) + len(alerts_data['consecutive_declines'])
        if total_alerts > 0:
            logging.info(f"🚨 {total_alerts} alerts triggered - sending notification")
            self.send_email_alert(alerts_data)
        else:
            logging.info("✅ No alerts triggered")
        
        logging.info("Monitoring cycle completed")

def setup_scheduler(monitor):
    """Setup the monitoring schedule"""
    # Run after market close at 5:30 PM ET (30 minutes after close)
    schedule.every().day.at("17:30").do(monitor.run_monitoring_cycle)
    
    # Optional: Run a test check at 6 PM ET
    # schedule.every().day.at("18:00").do(monitor.run_monitoring_cycle)
    
    logging.info("📅 Stock monitoring scheduled for 5:30 PM ET daily")

def main():
    """Main function to start the monitoring system"""
    print("🚀 Starting Free Stock Monitoring System")
    print(f"📊 Monitoring {len(TICKERS)} stocks:")
    print(f"   • Daily drops > 5%")
    print(f"   • 3+ consecutive declining days")
    print(f"   • Scheduled for 5:30 PM ET daily")
    print()
    
    # Check email configuration
    if not (os.getenv("EMAIL_USER") and os.getenv("EMAIL_PASS")):
        print("⚠️  EMAIL CONFIGURATION REQUIRED:")
        print("   Set these environment variables:")
        print("   EMAIL_USER=your-gmail@gmail.com")
        print("   EMAIL_PASS=your-app-password")
        print("   TO_EMAIL=recipient@email.com (optional, defaults to EMAIL_USER)")
        print()
        print("   For Gmail App Password, visit: https://myaccount.google.com/apppasswords")
        print()
    
    monitor = StockMonitor()
    
    # Run immediate test if requested
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("🧪 Running test monitoring cycle...")
        monitor.run_monitoring_cycle()
        return
    
    # Setup scheduler
    setup_scheduler(monitor)
    
    print("✅ System started! Press Ctrl+C to stop.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n👋 Stock monitoring stopped by user")

if __name__ == "__main__":
    main()
