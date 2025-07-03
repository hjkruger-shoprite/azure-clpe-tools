#!/bin/bash

# Azure Service Health Checker Setup Script

echo "🏥 Setting up Azure Service Health Checker..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.7+ and try again."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv azure_service_checker_env

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source azure_service_checker_env/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📥 Installing Azure dependencies..."
pip install -r requirements_service_checker.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "To use the Azure Service Health Checker:"
echo "1. Activate the virtual environment:"
echo "   source azure_service_checker_env/bin/activate"
echo ""
echo "2. Login to Azure:"
echo "   az login"
echo ""
echo "3. Run the service health checker:"
echo "   python azure_service_health_checker.py"
echo ""
echo "4. When done, deactivate the virtual environment:"
echo "   deactivate"
