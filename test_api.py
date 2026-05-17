#!/usr/bin/env python3
"""
Test script to verify the enhanced trading agent system
"""

import requests
import json
import time
import sys

def test_api_endpoints():
    """Test all API endpoints"""
    base_url = "http://localhost:8001"

    print("🧪 Testing API Endpoints")
    print("=" * 50)

    tests = [
        ("Root endpoint", f"{base_url}/"),
        ("Health check", f"{base_url}/health"),
        ("Tickers list", f"{base_url}/tickers"),
        ("AAPL signal", f"{base_url}/signal/AAPL"),
        ("All signals", f"{base_url}/signals/all"),
        ("Backtest AAPL", f"{base_url}/backtest/AAPL")
    ]

    results = []

    for name, url in tests:
        try:
            print(f"Testing {name}...")
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {name}: Success")
                results.append((name, True, response.json()))
            else:
                print(f"❌ {name}: Status {response.status_code}")
                results.append((name, False, None))
        except Exception as e:
            print(f"❌ {name}: Error - {str(e)}")
            results.append((name, False, str(e)))

    return results

def test_websocket():
    """Test WebSocket connection"""
    print("\n🔌 Testing WebSocket")
    print("=" * 30)

    try:
        import websocket
        ws = websocket.create_connection("ws://localhost:8001/ws/signals")
        print("✅ WebSocket connected")

        # Wait for message
        message = ws.recv()
        data = json.loads(message)
        print(f"✅ Received message: {data['type']}")

        ws.close()
        print("✅ WebSocket closed successfully")
        return True

    except Exception as e:
        print(f"❌ WebSocket error: {str(e)}")
        return False

def check_frontend():
    """Check if frontend is accessible"""
    print("\n🌐 Checking Frontend")
    print("=" * 30)

    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is running at http://localhost:3000")
            return True
        else:
            print("❌ Frontend returned status code:", response.status_code)
            return False
    except:
        print("❌ Frontend is not running")
        print("   Start it with: cd frontend && npm start")
        return False

def check_models():
    """Check if trained models exist"""
    print("\n🤖 Checking Models")
    print("=" * 30)

    models_dir = "models/rl"
    if not os.path.exists(models_dir):
        print("❌ Models directory not found")
        return False

    models = []
    for file in os.listdir(models_dir):
        if file.endswith(".zip"):
            models.append(file)

    if models:
        print("✅ Found trained models:")
        for model in models:
            print(f"   - {model}")
        return True
    else:
        print("❌ No trained models found")
        print("   Train models with: python agent_rl.py")
        return False

def check_backtest_results():
    """Check backtest results"""
    print("\n📊 Checking Backtest Results")
    print("=" * 35)

    results_dir = "results"
    if not os.path.exists(results_dir):
        print("❌ Results directory not found")
        return False

    files = [f for f in os.listdir(results_dir) if f.endswith('.png') or f.endswith('.csv')]

    if files:
        print("✅ Found backtest results:")
        for file in files:
            print(f"   - {file}")

        # Try to read summary
        summary_file = os.path.join(results_dir, "backtest_summary.csv")
        if os.path.exists(summary_file):
            try:
                import pandas as pd
                df = pd.read_csv(summary_file)
                print("\n📈 Backtest Summary:")
                print(df.to_string(index=False))
            except:
                print("❌ Could not read summary file")
        return True
    else:
        print("❌ No backtest results found")
        print("   Run backtest with: python backtest.py")
        return False

def main():
    """Main test function"""
    print("🚀 Enhanced Trading Agent System Test")
    print("=" * 60)

    results = []

    # Test API
    api_results = test_api_endpoints()
    results.extend(api_results)

    # Test WebSocket
    ws_result = test_websocket()
    results.append(("WebSocket", ws_result, None))

    # Check frontend
    frontend_result = check_frontend()
    results.append(("Frontend", frontend_result, None))

    # Check models
    models_result = check_models()
    results.append(("Models", models_result, None))

    # Check backtest results
    backtest_result = check_backtest_results()
    results.append(("Backtest Results", backtest_result, None))

    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    print(f"Passed: {passed}/{total}")

    for name, success, details in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")

    if passed == total:
        print("\n🎉 All tests passed!")
        print("\nNext steps:")
        print("1. Access the dashboard: http://localhost:3000")
        print("2. View API docs: http://localhost:8001/docs")
        print("3. Start trading: python trading_engine.py")
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        print("\nFix the issues above to get the full system working.")

if __name__ == "__main__":
    import os
    main()