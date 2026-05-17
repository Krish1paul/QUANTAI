# Enhanced Trading Agent API Documentation

## Overview

The Enhanced Trading Agent API provides a comprehensive RESTful API for accessing trading signals, portfolio data, and backtest results. The API includes authentication, rate limiting, monitoring, and WebSocket support for real-time data.

## Base URL
```
http://localhost:8001
```

## Authentication

### API Key Authentication
Generate a token using your API key:
```
GET /api/auth/generate-token?api_key=your_api_key
```

### JWT Authentication
Include the JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### Health and System Status

#### Get System Health
```http
GET /api/system/health
```
Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-04-15T10:00:00Z",
  "metrics": {
    "cpu_percent": 45.2,
    "memory_percent": 67.8,
    "disk_percent": 52.1,
    "connections": 3,
    "loaded_models": ["SPY", "QQQ", "AAPL"]
  },
  "loaded_models": ["SPY", "QQQ", "AAPL"]
}
```

#### Get System Metrics (Authenticated)
```http
GET /api/system/metrics
Authorization: Bearer <token>
```
Response:
```json
{
  "timestamp": "2026-04-15T10:00:00Z",
  "cpu_percent": 45.2,
  "memory_percent": 67.8,
  "disk_percent": 52.1,
  "request_stats": {
    "client_id": {
      "requests": 10,
      "avg_response_time": 0.15
    }
  }
}
```

### Trading Signals

#### Get Signal for a Ticker
```http
GET /api/signal/{ticker}
Authorization: Bearer <token>
```
Example:
```http
GET /api/signal/AAPL
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Response:
```json
{
  "ticker": "AAPL",
  "action": "BUY",
  "action_code": 1,
  "current_price": 175.20,
  "signal_strength": "high",
  "confidence": 0.85,
  "technical_indicators": {
    "rsi_14": 35.2,
    "macd": 0.42,
    "signal_strength": "high",
    "recommendation": "Strong Buy - Oversold with upward momentum"
  },
  "timestamp": "2026-04-15T10:00:00Z"
}
```

#### Get All Signals
```http
GET /api/signal/all
Authorization: Bearer <token>
```

#### Get Batch Signals
```http
POST /api/batch-signals
Authorization: Bearer <token>
Content-Type: application/json

{
  "tickers": ["SPY", "QQQ", "AAPL"]
}
```

### Portfolio Simulation

#### Simulate Portfolio
```http
POST /api/portfolio/simulate
Authorization: Bearer <token>
Content-Type: application/json

{
  "ticker": "AAPL",
  "initial_balance": 10000,
  "strategy": "rl"
}
```

Response:
```json
{
  "ticker": "AAPL",
  "final_value": 11518.75,
  "total_return": 15.19,
  "bh_return": 5.83,
  "alpha": 9.36,
  "n_trades": 35,
  "win_rate": 60.0,
  "sharpe_ratio": 0.412,
  "max_drawdown": -30.12,
  "portfolio_values": [10000, 10050, ...],
  "trades": [
    {
      "step": 10,
      "pnl": 125.50,
      "return_pct": 1.25
    }
  ],
  "strategy": "rl",
  "simulation_date": "2026-04-15T10:00:00Z"
}
```

### Backtest Data

#### Get Backtest Results
```http
GET /api/backtest/{ticker}
Authorization: Bearer <token>
```
Example:
```http
GET /api/backtest/QQQ
```

Response:
```json
{
  "ticker": "QQQ",
  "final_value": 10555.25,
  "total_return": 5.55,
  "bh_return": 20.37,
  "alpha": -14.82,
  "sharpe": 0.036,
  "max_drawdown": -25.63,
  "win_rate": 60.0,
  "chart_exists": true,
  "backtest_date": "2026-04-15T10:00:00Z"
}
```

#### Get Backtest Summary
```http
GET /api/backtest/summary/all
Authorization: Bearer <token>
```

### Tickers and Data

#### Get Available Tickers
```http
GET /api/tickers
Authorization: Bearer <token>
```

Response:
```json
{
  "tickers": [
    {
      "ticker": "SPY",
      "data_points": 252,
      "last_updated": "2024-12-31",
      "model_available": true
    },
    {
      "ticker": "QQQ",
      "data_points": 252,
      "last_updated": "2024-12-31",
      "model_available": true
    }
  ]
}
```

#### Get Historical Data
```http
GET /api/data/{ticker}?rows=100
Authorization: Bearer <token>
```
Example:
```http
GET /api/data/AAPL?rows=50
```

Response:
```json
{
  "ticker": "AAPL",
  "rows": 50,
  "data": {
    "close": [175.20, 176.50, ...],
    "volume": [45210000, 48320000, ...],
    "rsi": [35.2, 38.5, ...],
    "macd": [0.42, 0.45, ...]
  }
}
```

### Data Export

#### Export Data
```http
GET /api/export/{format}
Authorization: Bearer <token>
```
Example:
```http
GET /api/export/csv
```

### WebSocket

#### Real-time Signals WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8001/ws/signals');

// First message must be authentication
ws.send(JSON.stringify({
  type: 'auth',
  token: 'your_jwt_token'
}));

// Listen for signals
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'signals') {
    console.log('Updated signals:', data.signals);
  }
};
```

## Error Handling

### Error Response Format
```json
{
  "error": "Error message",
  "details": "Additional error details",
  "timestamp": "2026-04-15T10:00:00Z"
}
```

### Common Error Codes
- `401 Unauthorized`: Invalid or missing authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limiting

- Default: 60 requests per minute per client
- Headers include rate limit information:
  - `X-RateLimit-Limit`: 60
  - `X-RateLimit-Remaining`: 58
  - `X-RateLimit-Reset`: 1713204000

## WebSocket Events

### Message Format
```json
{
  "type": "signals",
  "signals": {
    "SPY": { ... },
    "QQQ": { ... }
  },
  "timestamp": "2026-04-15T10:00:00Z"
}
```

### Event Types
- `welcome`: Connection established
- `signals`: Updated trading signals
- `error`: Error message

## Examples

### Python Example
```python
import requests
import json

# Get JWT token
response = requests.get("http://localhost:8001/api/auth/generate-token?api_key=your_api_key")
token = response.json()["access_token"]

# Get signal
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://localhost:8001/api/signal/AAPL", headers=headers)
signal = response.json()
print(f"Action: {signal['action']}")

# Portfolio simulation
data = {
    "ticker": "AAPL",
    "initial_balance": 10000,
    "strategy": "rl"
}
response = requests.post("http://localhost:8001/api/portfolio/simulate",
                        json=data, headers=headers)
portfolio = response.json()
```

### JavaScript Example
```javascript
// API client
const apiClient = {
  baseURL: 'http://localhost:8001',
  token: null,

  async authenticate(apiKey) {
    const response = await fetch(`${this.baseURL}/api/auth/generate-token?api_key=${apiKey}`);
    const data = await response.json();
    this.token = data.access_token;
  },

  async getSignal(ticker) {
    const response = await fetch(`${this.baseURL}/api/signal/${ticker}`, {
      headers: { Authorization: `Bearer ${this.token}` }
    });
    return response.json();
  },

  async getBacktest(ticker) {
    const response = await fetch(`${this.baseURL}/api/backtest/${ticker}`, {
      headers: { Authorization: `Bearer ${this.token}` }
    });
    return response.json();
  }
};

// Usage
apiClient.authenticate('your_api_key')
  .then(() => {
    return apiClient.getSignal('AAPL');
  })
  .then(signal => {
    console.log('Signal:', signal);
  });
```

## Webhook Integration

The API can send webhook notifications for important events:

```http
POST /api/webhooks/trade-executed
Authorization: Bearer <token>
Content-Type: application/json

{
  "ticker": "AAPL",
  "action": "BUY",
  "quantity": 100,
  "price": 175.20,
  "timestamp": "2026-04-15T10:00:00Z"
}
```

## Monitoring

### Prometheus Metrics
The API exposes metrics at `/metrics` endpoint:
- `api_requests_total`: Total API requests
- `api_request_duration_seconds`: Request duration
- `active_connections`: Active WebSocket connections

### Logging
The API includes structured logging for:
- Request/response logs
- Error logs
- Performance metrics
- Security events

## Security Best Practices

1. **Use HTTPS** in production
2. **Rotate API keys** regularly
3. **Implement rate limiting**
4. **Validate all inputs**
5. **Monitor for suspicious activity**
6. **Use short-lived JWT tokens**

## Performance Optimization

1. **Use caching** for frequently accessed data
2. **Implement pagination** for large responses
3. **Use compression** for API responses
4. **Optimize database queries**
5. **Use CDN** for static assets