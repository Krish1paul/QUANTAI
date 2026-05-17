# Enhanced Trading Agent - Setup Guide

## Overview
This enhanced trading agent system includes advanced features such as:
- **Authentication & Security**: JWT-based API authentication, rate limiting
- **3D Visualizations**: Interactive 3D portfolio charts using Three.js
- **Advanced Backtesting**: Monte Carlo simulations, enhanced risk metrics
- **Real-time Trading**: Live trading engine with risk management
- **Feature Engineering**: Advanced technical indicators and feature selection

## Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn
- Optional: GPU support for faster model training

## Setup Instructions

### 1. Python Backend Setup

#### Step 1: Clone Repository
```bash
git clone <repository-url>
cd /Users/krishpaul/Work/Vs code/Pbl
```

#### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

#### Step 3: Install Additional Libraries for Enhanced Features
```bash
# For enhanced API features
pip install prometheus-fastapi-instrumentator psutil PyJWT bcrypt python-jose[cryptography]

# For 3D visualization (if using Three.js directly)
pip install three

# For real-time trading
pip install aiohttp yfinance
```

#### Step 4: Generate Data
```bash
python data_generator.py
```

#### Step 5: Train Models
```bash
python agent_rl.py
```

#### Step 6: Run Backtesting
```bash
# Standard backtesting
python backtest.py

# Enhanced backtesting with Monte Carlo
python backtest_enhanced.py
```

### 2. Frontend Setup

#### Step 1: Install Node Dependencies
```bash
cd frontend
npm install

# Install additional 3D libraries
npm install three @react-three/fiber @react-three/drei
```

#### Step 2: Start Development Server
```bash
npm start
```

#### Step 3: Build for Production
```bash
npm run build
```

### 3. API Setup

#### Basic API
```bash
cd api
python main.py
```

#### Enhanced API (Recommended for Production)
```bash
cd api
python enhanced_api.py
```

The enhanced API includes:
- Authentication with JWT
- Rate limiting
- System monitoring
- WebSocket authentication
- Enhanced security features

## Configuration

### API Configuration
Create a `.env` file in the `api` directory:
```env
API_KEY_1=your-secret-api-key-1
API_KEY_2=your-secret-api-key-2
JWT_SECRET=your-jwt-secret-key
ALLOWED_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]
```

### Frontend Configuration
Update `src/config.js`:
```javascript
export const API_BASE_URL = process.env.NODE_ENV === 'production'
  ? 'https://your-api-domain.com'
  : 'http://localhost:8001';
```

## Features Overview

### 1. Enhanced API Features
- **Authentication**: JWT-based authentication with API key management
- **Rate Limiting**: Configurable request limits per minute
- **Monitoring**: Prometheus metrics integration
- **WebSocket**: Real-time authenticated data streaming
- **Security**: HTTPS, CORS, trusted host middleware

### 2. Advanced Frontend Features
- **3D Portfolio Visualization**: Interactive 3D charts
- **Risk Heatmaps**: Visual risk assessment
- **Correlation Networks**: Asset correlation visualization
- **Advanced Charts**: Option strategies, Monte Carlo simulations
- **Real-time Updates**: WebSocket integration

### 3. Enhanced Backtesting
- **Monte Carlo Simulation**: 1000+ portfolio simulations
- **Advanced Metrics**: Sortino ratio, Ulcer Index, VaR/CVaR
- **Risk Analysis**: Comprehensive risk metrics
- **Visual Reports**: Enhanced charts and analysis

### 4. Real-time Trading Engine
- **Risk Management**: Position sizing, stop-loss, take-profit
- **Signal Processing**: Real-time signal interpretation
- **Portfolio Management**: Live position tracking
- **Performance Monitoring**: Real-time P&L tracking

## Deployment

### Production Setup

#### Backend
1. Use the enhanced API for production
2. Set up reverse proxy (nginx)
3. Configure HTTPS
4. Set up monitoring and logging

```nginx
# Example nginx configuration
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### Frontend
1. Build the production version
2. Serve static files from CDN or web server
3. Configure API endpoints

```bash
npm run build
# Serve from nginx or other web server
```

### Docker Deployment

#### Backend Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY api/ .
CMD ["python", "enhanced_api.py"]
```

#### Frontend Dockerfile
```dockerfile
FROM node:16 as build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
CMD ["nginx", "-g", "daemon off;"]
```

## Monitoring and Maintenance

### System Monitoring
- API health checks
- Performance metrics
- Error tracking
- Resource utilization

### Logging
- Application logs
- Error logs
- Trading activity logs
- Access logs

### Updates
- Regular dependency updates
- Security patches
- Feature updates

## Troubleshooting

### Common Issues

1. **API Connection Issues**
   - Check if the API is running on port 8001
   - Verify CORS settings
   - Check authentication credentials

2. **Frontend Issues**
   - Clear browser cache
   - Check console for errors
   - Verify API endpoint configuration

3. **Model Loading Issues**
   - Ensure models are trained and saved
   - Check model file permissions
   - Verify model compatibility

### Performance Optimization
- Use GPU for model training
- Implement caching
- Optimize database queries
- Use CDNs for static assets

## Support

For support and questions:
- Check the documentation
- Review the code comments
- Open an issue on GitHub
- Contact the development team