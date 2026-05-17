#!/usr/bin/env python3
"""
Enhanced Trading Agent Setup Script
Automated installation and configuration
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
import shutil
import json

def run_command(cmd, description=None, check=True):
    """Run a command with error handling"""
    if description:
        print(f"\n{'='*60}")
        print(f"🔄 {description}")
        print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def check_nodejs():
    """Check if Node.js is installed"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js {result.stdout.strip()} detected")
            return True
    except:
        pass
    print("❌ Node.js is not installed. Please install Node.js 16 or higher")
    return False

def install_python_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")

    # Upgrade pip
    run_command("pip install --upgrade pip", "Upgrading pip")

    # Install requirements
    if os.path.exists("requirements.txt"):
        run_command("pip install -r requirements.txt", "Installing Python requirements")

    # Install additional packages for enhanced features
    additional_packages = [
        "prometheus-fastapi-instrumentator",
        "psutil",
        "PyJWT[crypto]",
        "bcrypt",
        "python-jose[cryptography]",
        "aiohttp",
        "websockets"
    ]

    for package in additional_packages:
        run_command(f"pip install {package}", f"Installing {package}")

def generate_data():
    """Generate sample data"""
    print("\n📊 Generating data...")

    # Check if data generator exists
    if os.path.exists("data_generator.py"):
        run_command("python data_generator.py", "Generating trading data")
    else:
        print("⚠️  Data generator not found. Skipping data generation.")

def train_models():
    """Train RL models"""
    print("\n🤖 Training models...")

    if os.path.exists("agent_rl.py"):
        run_command("python agent_rl.py", "Training reinforcement learning models")
    else:
        print("⚠️  RL training script not found. Skipping model training.")

def run_backtests():
    """Run backtests"""
    print("\n📈 Running backtests...")

    # Standard backtest
    if os.path.exists("backtest.py"):
        run_command("python backtest.py", "Running standard backtest")

    # Enhanced backtest
    if os.path.exists("backtest_enhanced.py"):
        run_command("python backtest_enhanced.py", "Running enhanced backtest")

def setup_frontend():
    """Setup frontend dependencies"""
    print("\n🎨 Setting up frontend...")

    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False

    os.chdir(frontend_dir)

    # Install dependencies
    if run_command("npm install", "Installing frontend dependencies"):
        # Install additional 3D libraries
        run_command("npm install three @react-three/fiber @react-three/drei", "Installing 3D libraries")

        # Return to root directory
        os.chdir("..")
        return True
    else:
        os.chdir("..")
        return False

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")

    directories = [
        "data/raw",
        "data/processed",
        "models/rl",
        "models/lstm",
        "results",
        "logs",
        "api"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def create_config_files():
    """Create configuration files"""
    print("\n⚙️  Creating configuration files...")

    # Create .env file for API
    env_content = """# API Configuration
API_KEY_1=your-secret-api-key-1-change-this-in-production
API_KEY_2=your-secret-api-key-2-change-this-in-production
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production

# CORS Configuration
ALLOWED_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]

# Rate Limiting
REQUESTS_PER_MINUTE=60

# Trading Configuration
INITIAL_BALANCE=10000
COMMISSION_RATE=0.001
MAX_POSITION_SIZE=0.1
"""

    with open("api/.env", "w") as f:
        f.write(env_content)

    print("✅ Created api/.env")

    # Create config.json for frontend
    config_content = {
        "apiBaseUrl": "http://localhost:8001",
        "wsUrl": "ws://localhost:8001/ws/signals",
        "tickers": ["SPY", "QQQ", "AAPL", "MSFT", "NVDA"],
        "theme": "dark",
        "enableAnimations": True,
        "enableSound": False
    }

    with open("frontend/src/config.json", "w") as f:
        json.dump(config_content, f, indent=2)

    print("✅ Created frontend/src/config.json")

def create_startup_scripts():
    """Create startup scripts"""
    print("\n🚀 Creating startup scripts...")

    # Windows
    windows_bat = """@echo off
echo Starting Enhanced Trading Agent System
echo =======================================

echo Starting API...
start /B api\\enhanced_api.py

echo Starting Frontend...
cd frontend
start npm start
cd ..

echo Starting Trading Engine...
start trading_engine.py

echo System started!
echo API: http://localhost:8001
echo Frontend: http://localhost:3000
pause
"""

    with open("start_system.bat", "w") as f:
        f.write(windows_bat)

    # Linux/Mac
    shell_script = """#!/bin/bash
echo "Starting Enhanced Trading Agent System"
echo "======================================"

echo "Starting API..."
python api/enhanced_api.py &

echo "Starting Frontend..."
cd frontend
npm start &
cd ..

echo "Starting Trading Engine..."
python trading_engine.py &

echo "System started!"
echo "API: http://localhost:8001"
echo "Frontend: http://localhost:3000"
"""

    with open("start_system.sh", "w") as f:
        f.write(shell_script)

    # Make shell script executable
    os.chmod("start_system.sh", 0o755)

    print("✅ Created startup scripts")

def generate_readme():
    """Generate README with current system info"""
    print("\n📝 Generating README...")

    readme_content = """# Enhanced Trading Agent System

## System Overview
This is an enhanced trading agent system with advanced features including:
- Reinforcement Learning models for trading decisions
- 3D portfolio visualization
- Real-time trading engine
- Advanced backtesting with Monte Carlo simulation
- Authentication and security features

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- 8GB+ RAM recommended

### Installation
Run the setup script:
```bash
python setup.py
```

### Starting the System
Use the provided startup scripts:
- Windows: `start_system.bat`
- Linux/Mac: `start_system.sh`

### Access Points
- API Documentation: http://localhost:8001/docs
- Frontend: http://localhost:3000
- System Health: http://localhost:8001/api/system/health

## Configuration
- API keys and secrets in `api/.env`
- Frontend configuration in `frontend/src/config.json`
- Model training parameters in `agent_rl.py`

## Features
1. **AI Trading Agent**: PPO-based reinforcement learning
2. **Enhanced API**: JWT authentication, rate limiting, monitoring
3. **3D Visualization**: Interactive portfolio charts
4. **Real-time Trading**: Live trading with risk management
5. **Advanced Backtesting**: Monte Carlo simulation, risk metrics

## Support
For issues and questions, check the documentation in the docs/ folder.
"""

    with open("README.md", "w") as f:
        f.write(readme_content)

    print("✅ Generated README.md")

def main():
    """Main setup function"""
    print("🚀 Enhanced Trading Agent Setup")
    print("=" * 50)

    # Check system requirements
    if not check_python_version():
        sys.exit(1)

    if not check_nodejs():
        print("\n⚠️  Node.js is required for frontend features")
        response = input("Continue without frontend? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)

    # Create directories
    create_directories()

    # Create configuration files
    create_config_files()

    # Install dependencies
    print("\n📥 Installing dependencies...")
    install_python_dependencies()

    if check_nodejs():
        setup_frontend()

    # Generate data and train models
    generate_data()
    train_models()
    run_backtests()

    # Create startup scripts
    create_startup_scripts()

    # Generate documentation
    generate_readme()

    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")
    print("\nNext steps:")
    print("1. Review and update configuration files")
    print("2. Check API health: http://localhost:8001/api/system/health")
    print("3. Start the system using startup scripts")
    print("4. Access the frontend: http://localhost:3000")
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()