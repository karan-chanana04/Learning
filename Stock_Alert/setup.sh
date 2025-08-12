#!/bin/bash

# Quick Setup Script for Stock Monitor
# Run this script to set up your free stock monitoring system

echo "🚀 Setting up Free Stock Monitoring System..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "✅ Python 3 found"

# Install required packages
echo "📦 Installing required packages..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Packages installed successfully"
else
    echo "❌ Failed to install packages. Please check your internet connection."
    exit 1
fi

# Check for environment variables
echo ""
echo "🔧 Checking email configuration..."

if [ -z "$EMAIL_USER" ] || [ -z "$EMAIL_PASS" ]; then
    echo "⚠️  EMAIL CONFIGURATION REQUIRED:"
    echo ""
    echo "Please set these environment variables:"
    echo "export EMAIL_USER=\"your-gmail@gmail.com\""
    echo "export EMAIL_PASS=\"your-16-digit-app-password\""
    echo "export TO_EMAIL=\"recipient@email.com\""
    echo ""
    echo "For Gmail App Password, visit: https://myaccount.google.com/apppasswords"
    echo ""
    echo "Add these to your ~/.zshrc or ~/.bash_profile to make them permanent:"
    echo "echo 'export EMAIL_USER=\"your-gmail@gmail.com\"' >> ~/.zshrc"
    echo "echo 'export EMAIL_PASS=\"your-16-digit-app-password\"' >> ~/.zshrc"
    echo "source ~/.zshrc"
else
    echo "✅ Email configuration found"
    
    # Run test
    echo ""
    echo "🧪 Running test to verify everything works..."
    python3 stock_monitor.py --test
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Setup completed successfully!"
        echo ""
        echo "To start monitoring:"
        echo "python3 stock_monitor.py"
        echo ""
        echo "To run in background:"
        echo "nohup python3 stock_monitor.py > monitor.out 2>&1 &"
    else
        echo "❌ Test failed. Please check your email configuration."
    fi
fi
