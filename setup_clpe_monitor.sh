#!/bin/bash

# CLPE NCRPES Service Monitor Setup Script

echo "🏥 Setting up CLPE NCRPES Service Monitor..."
echo "🔒 Integration Testing - System:CENTRAL_LOYALTY_PROMOTIONS_ENGINE"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.7+ and try again."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv clpe_monitor_env

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source clpe_monitor_env/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📥 Installing Azure dependencies..."
pip install -r requirements_service_checker.txt

echo ""
echo "✅ CLPE NCRPES Monitor setup complete!"
echo ""
echo "🏥 To monitor ncrpes.exe service on CLPE VMs:"
echo ""
echo "1. Activate the virtual environment:"
echo "   source clpe_monitor_env/bin/activate"
echo ""
echo "2. Login to Azure (if not already logged in):"
echo "   az login"
echo ""
echo "3. Run the CLPE NCRPES monitor:"
echo "   python clpe_ncrpes_monitor.py"
echo ""
echo "4. When done, deactivate the virtual environment:"
echo "   deactivate"
echo ""
echo "🔒 Security Notes:"
echo "   - Restricted to Integration Testing subscription"
echo "   - Only monitors VMs tagged with System:CENTRAL_LOYALTY_PROMOTIONS_ENGINE"
echo "   - Monitors ncrpes.exe service specifically"
echo ""
echo "📋 Expected CLPE VMs:"
echo "   - CLPEINTDB1 (Database Server)"
echo "   - CLPEINTWEB1 (Web Server 1)"
echo "   - CLPEINTWEB2 (Web Server 2)"
