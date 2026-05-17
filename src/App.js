import React, { useState, useEffect, useCallback } from 'react';
import {
  AreaChart, Area, BarChart, Bar, RadarChart, Radar, LineChart, Line,
  ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ReferenceLine, ZAxis, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Cell
} from 'recharts';
import axios from 'axios';

// CSS variables and design system
const CSS_VARS = {
  bg: '#060c14',
  cardBg: '#0d1926',
  sidebarBg: '#0b1520',
  accent: '#00b4ff',
  green: '#00e5a0',
  red: '#ff4060',
  yellow: '#ffc840',
  muted: '#4a6a88',
  text: '#ddeeff',
  border: 'rgba(0,180,255,0.12)',
  borderHover: 'rgba(0,180,255,0.28)',
  fontMono: "'Space Mono', monospace",
  fontSans: "'DM Sans', sans-serif"
};

// Add Google Fonts
useEffect(() => {
  const fontLink = document.createElement('link');
  fontLink.href = 'https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@400;500&display=swap';
  fontLink.rel = 'stylesheet';
  document.head.appendChild(fontLink);

  const globalStyle = document.createElement('style');
  globalStyle.textContent = `
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: ${CSS_VARS.bg};
      color: ${CSS_VARS.text};
      font-family: ${CSS_VARS.fontSans};
      overflow: hidden;
    }
    body::before {
      content:'';
      position:fixed;
      inset:0;
      pointer-events:none;
      z-index:9999;
      background: repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.025) 2px,rgba(0,0,0,0.025) 4px);
    }
    ::-webkit-scrollbar {
      width:4px;
      height:4px;
    }
    ::-webkit-scrollbar-track {
      background:${CSS_VARS.sidebarBg};
    }
    ::-webkit-scrollbar-thumb {
      background:${CSS_VARS.borderHover};
      border-radius:2px;
    }
    @keyframes pulse {
      0%,100%{opacity:1;transform:scale(1)}
      50%{opacity:.5;transform:scale(1.5)}
    }
    @keyframes fadeUp {
      from{opacity:0;transform:translateY(10px)}
      to{opacity:1;transform:translateY(0)}
    }
    .fade-up {
      animation: fadeUp 0.35s ease forwards;
    }
    .nav-item {
      transition: all 0.2s ease;
    }
    .nav-item:hover {
      background: rgba(0,180,255,0.08);
    }
    .nav-item.active {
      border-left: 3px solid ${CSS_VARS.accent};
      color: ${CSS_VARS.accent};
      background: rgba(0,180,255,0.1);
    }
    .ticker-pill {
      transition: all 0.2s ease;
      cursor: pointer;
      padding: 6px 12px;
      border-radius: 20px;
      background: ${CSS_VARS.cardBg};
      border: 1px solid ${CSS_VARS.border};
    }
    .ticker-pill:hover {
      border-color: ${CSS_VARS.accent};
      background: rgba(0,180,255,0.1);
    }
    .ticker-pill.active {
      border-color: ${CSS_VARS.accent};
      background: rgba(0,180,255,0.2);
    }
  `;
  document.head.appendChild(globalStyle);
}, []);

// Ticker metadata
const TICKER_META = {
  SPY:  { name:'S&P 500 ETF',    price:659.80, change:+0.42, action:'BUY',  acc:55.47, ret:+2.49,  bh:+13.42, alpha:-10.93, sharpe:-0.081, dd:-21.13, wr:54.3, rsi:35.3, macd:+0.18 },
  QQQ:  { name:'NASDAQ 100 ETF', price:593.02, change:+0.61, action:'BUY',  acc:56.64, ret:+5.55,  bh:+20.37, alpha:-14.82, sharpe:0.036,  dd:-25.63, wr:60.0, rsi:41.1, macd:+0.31 },
  AAPL: { name:'Apple Inc.',     price:248.96, change:-0.18, action:'BUY',  acc:52.34, ret:+15.18, bh:+5.83,  alpha:+9.35,  sharpe:0.412,  dd:-30.12, wr:51.4, rsi:35.8, macd:+0.42 },
  MSFT: { name:'Microsoft Corp.',price:412.30, change:+0.09, action:'HOLD', acc:52.34, ret:+4.86,  bh:+12.41, alpha:-7.55,  sharpe:0.124,  dd:-18.44, wr:52.6, rsi:52.1, macd:+0.08 },
  NVDA: { name:'NVIDIA Corp.',   price:875.50, change:-1.24, action:'SELL', acc:52.34, ret:+8.21,  bh:+22.10, alpha:-13.89, sharpe:0.089,  dd:-28.50, wr:48.6, rsi:71.4, macd:-0.22 },
};
const TICKERS = ['SPY','QQQ','AAPL','MSFT','NVDA'];

// Data generation helpers
const gen = (n, base, vol) => {
  let v = base;
  return Array.from({ length: n }, (_, i) => {
    v += (Math.random() - 0.47) * vol;
    return { x: i, y: +v.toFixed(2) }
  })
}

const fmt = (v, dec=2) => v > 0 ? `+${v.toFixed(dec)}%` : `${v.toFixed(dec)}%`
const col = v => v > 0 ? CSS_VARS.green : v < 0 ? CSS_VARS.red : CSS_VARS.muted

// Components
const Card = ({ children, glow = false, className = '' }) => (
  <div className={`relative ${CSS_VARS.cardBg} rounded-[12px] border ${CSS_VARS.border} p-6 overflow-hidden ${className}`}>
    {glow && (
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        height: '1px',
        background: 'linear-gradient(90deg, transparent, #00b4ff, transparent)',
        opacity: 0.3
      }} />
    )}
    {children}
  </div>
)

const CardTitle = ({ children }) => (
  <div style={{
    fontFamily: CSS_VARS.fontMono,
    fontSize: 10,
    letterSpacing: 1.5,
    color: CSS_VARS.muted,
    textTransform: 'uppercase',
    marginBottom: 10
  }}>
    {children}
  </div>
)

const StatCard = ({ title, value, sub, color = CSS_VARS.text }) => (
  <Card glow>
    <CardTitle>{title}</CardTitle>
    <div style={{ fontFamily: CSS_VARS.fontMono, fontSize: 24, fontWeight: 'bold', color }}>
      {value}
    </div>
    {sub && (
      <div style={{ fontSize: 12, color: CSS_VARS.muted, marginTop: 4 }}>
        {sub}
      </div>
    )}
  </Card>
)

const Badge = ({ action }) => {
  const style = {
    borderRadius: 5,
    padding: '3px 10px',
    fontFamily: CSS_VARS.fontMono,
    fontSize: 11,
    fontWeight: 700,
    display: 'inline-block'
  }

  if (action === 'BUY') {
    return <div style={{...style, background: 'rgba(0,229,160,0.15)', color: CSS_VARS.green, border: `1px solid ${CSS_VARS.green}`}}>
      BUY
    </div>
  } else if (action === 'SELL') {
    return <div style={{...style, background: CSS_VARS.red, color: '#fff', border: `1px solid ${CSS_VARS.red}`}}>
      SELL
    </div>
  } else {
    return <div style={{...style, background: CSS_VARS.muted, color: CSS_VARS.text, border: `1px solid ${CSS_VARS.muted}`}}>
      HOLD
    </div>
  }
}

const Btn = ({ children, variant = 'ghost', onClick, className = '' }) => {
  const baseStyle = {
    fontFamily: CSS_VARS.fontMono,
    fontSize: 11,
    borderRadius: 6,
    padding: '6px 12px',
    cursor: 'pointer',
    border: `1px solid ${CSS_VARS.border}`,
    background: 'transparent',
    color: CSS_VARS.muted,
    transition: 'all 0.2s ease',
    ...className
  }

  const variants = {
    ghost: {},
    primary: { color: CSS_VARS.accent, borderColor: CSS_VARS.accent },
    success: { color: CSS_VARS.green, borderColor: CSS_VARS.green },
    danger: { color: CSS_VARS.red, borderColor: CSS_VARS.red },
    warning: { color: CSS_VARS.yellow, borderColor: CSS_VARS.yellow },
    active: { color: CSS_VARS.accent, borderColor: CSS_VARS.accent, background: 'rgba(0,180,255,0.1)' }
  }

  return (
    <div
      style={{...baseStyle, ...variants[variant]}}
      onClick={onClick}
      onMouseEnter={(e) => e.target.style.borderColor = CSS_VARS.borderHover}
      onMouseLeave={(e) => e.target.style.borderColor = CSS_VARS.border}
    >
      {children}
    </div>
  )
}

const Toggle = ({ checked, onChange }) => (
  <div
    style={{
      width: 38,
      height: 20,
      background: checked ? CSS_VARS.green : CSS_VARS.muted,
      borderRadius: 20,
      position: 'relative',
      cursor: 'pointer',
      transition: 'background 0.3s ease'
    }}
    onClick={onChange}
  >
    <div
      style={{
        position: 'absolute',
        top: 2,
        left: checked ? 18 : 2,
        width: 16,
        height: 16,
        background: CSS_VARS.text,
        borderRadius: 50,
        transition: 'left 0.3s ease'
      }}
    />
  </div>
)

const RiskBar = ({ label, value, max = 100, color }) => (
  <div style={{ display: 'flex', alignItems: 'center', marginBottom: 12 }}>
    <div style={{ width: 90, fontSize: 11, color: CSS_VARS.muted }}>{label}</div>
    <div style={{ flex: 1, height: 4, background: CSS_VARS.cardBg, borderRadius: 2, overflow: 'hidden' }}>
      <div
        style={{
          height: '100%',
          background: color || CSS_VARS.accent,
          width: `${Math.min((value / max) * 100, 100)}%`
        }}
      />
    </div>
    <div style={{ fontSize: 11, color: CSS_VARS.text, marginLeft: 8, fontFamily: CSS_VARS.fontMono }}>
      {value}
    </div>
  </div>
)

const DataTable = ({ columns, data, maxHeight }) => (
  <div style={{ background: CSS_VARS.cardBg, borderRadius: 8, overflow: 'hidden', maxHeight, overflowY: 'auto' }}>
    <div style={{
      background: CSS_VARS.sidebarBg,
      display: 'flex',
      fontFamily: CSS_VARS.fontMono,
      fontSize: 11,
      fontWeight: 700,
      borderBottom: `1px solid ${CSS_VARS.border}`
    }}>
      {columns.map((col, i) => (
        <div key={i} style={{ flex: col.flex || 1, padding: '10px', textAlign: col.align || 'left' }}>
          {col.label}
        </div>
      ))}
    </div>
    {data.map((row, i) => (
      <React.Fragment key={i}>
        <div style={{
          display: 'flex',
          borderBottom: i < data.length - 1 ? `1px solid ${CSS_VARS.border}` : 'none',
          background: i % 2 === 0 ? 'transparent' : 'rgba(0,180,255,0.03)',
          transition: 'background 0.2s ease'
        }}>
          {columns.map((col, j) => (
            <div key={j} style={{ flex: col.flex || 1, padding: '10px', textAlign: col.align || 'left', fontSize: 11 }}>
              {col.render ? col.render(row[col.key]) : row[col.key]}
            </div>
          ))}
        </div>
      </React.Fragment>
    ))}
  </div>
)

const SectionHead = ({ children, rightSlot }) => (
  <div style={{
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20
  }}>
    <div style={{
      fontFamily: CSS_VARS.fontMono,
      fontSize: 11,
      letterSpacing: 1,
      color: CSS_VARS.accent,
      textTransform: 'uppercase'
    }}>
      {children}
    </div>
    {rightSlot}
  </div>
)

const ChartTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{
        background: CSS_VARS.cardBg,
        border: `1px solid ${CSS_VARS.accent}`,
        borderRadius: 8,
        padding: 10,
        fontFamily: CSS_VARS.fontMono,
        fontSize: 11
      }}>
        {payload.map((entry, index) => (
          <div key={index} style={{ color: entry.color }}>
            {entry.name}: {typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}
          </div>
        ))}
      </div>
    )
  }
  return null
}

const TooltipProps = {
  content: <ChartTooltip />
}

// Pages
const OverviewPage = ({ activeTicker, setActiveTicker }) => {
  const [period, setPeriod] = useState('3M');

  const portfolioData = gen(90, 11518, 50);
  const lstmData = TICKERS.map(ticker => ({
    name: ticker,
    accuracy: 48 + Math.random() * 10
  }));

  const tradeData = Array.from({ length: 35 }, (_, i) => ({
    x: i,
    y: (Math.random() - 0.5) * 1000
  }));

  const actionData = [
    { name: 'BUY', value: 35, color: CSS_VARS.green },
    { name: 'HOLD', value: 180, color: CSS_VARS.muted },
    { name: 'SELL', value: 35, color: CSS_VARS.red }
  ];

  const recentTrades = [
    { ticker: 'AAPL', action: 'BUY', pnl: '+245.32', time: '14:32:15' },
    { ticker: 'NVDA', action: 'SELL', pnl: '-128.45', time: '14:28:43' },
    { ticker: 'QQQ', action: 'BUY', pnl: '+89.12', time: '14:15:22' },
    { ticker: 'SPY', action: 'HOLD', pnl: '+0', time: '13:45:10' },
    { ticker: 'MSFT', action: 'BUY', pnl: '+156.78', time: '13:22:05' }
  ];

  return (
    <div className="fade-up" style={{ height: 'calc(100vh - 120px)', overflowY: 'auto' }}>
      <SectionHead
        "System Overview"
        rightSlot={
          <>
            <Btn>⟳ Refresh</Btn>
            <Btn variant="ghost">↓ Export CSV</Btn>
            <Btn variant="primary">▶ Run Backtest</Btn>
          </>
        }
      />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 16, marginBottom: 20 }}>
        <StatCard title="Portfolio Value" value="$11,518" sub="↑ +15.18% total" color={CSS_VARS.green} />
        <StatCard title="Active Signals" value="3 BUY" sub="2 HOLD · 1 SELL active" color={CSS_VARS.accent} />
        <StatCard title="Best Win Rate" value="60.0%" sub="QQQ — 35 trades" color={CSS_VARS.yellow} />
        <StatCard title="Best Alpha" value="+9.35%" sub="AAPL vs B&H" color={CSS_VARS.green} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16, marginBottom: 20 }}>
        <Card glow>
          <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
            <Btn onClick={() => setPeriod('1M')} variant={period === '1M' ? 'active' : 'ghost'}>1M</Btn>
            <Btn onClick={() => setPeriod('3M')} variant={period === '3M' ? 'active' : 'ghost'}>3M</Btn>
            <Btn onClick={() => setPeriod('1Y')} variant={period === '1Y' ? 'active' : 'ghost'}>1Y</Btn>
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={portfolioData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,180,255,0.06)" />
              <XAxis dataKey="x" stroke={CSS_VARS.muted} tick={{ fill: CSS_VARS.muted, fontSize: 9 }} />
              <YAxis stroke={CSS_VARS.muted} tick={{ fill: CSS_VARS.muted, fontSize: 9 }} tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
              <Tooltip {...TooltipProps} />
              <defs>
                <linearGradient id="colorAgent" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={CSS_VARS.accent} stopOpacity={0.3}/>
                  <stop offset="95%" stopColor={CSS_VARS.accent} stopOpacity={0}/>
                </linearGradient>
              </defs>
              <Area type="monotone" dataKey="y" stroke={CSS_VARS.accent} fill="url(#colorAgent)" name="RL Agent" />
              <Line type="monotone" dataKey={(d, i) => 11518 + i * 20} stroke={CSS_VARS.yellow} strokeDasharray="5 5" name="Buy & Hold" />
            </AreaChart>
          </ResponsiveContainer>
        </Card>

        <Card glow>
          <CardTitle>LSTM Accuracy by Ticker</CardTitle>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={lstmData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,180,255,0.06)" />
              <XAxis dataKey="name" stroke={CSS_VARS.muted} tick={{ fill: CSS_VARS.muted, fontSize: 9 }} />
              <YAxis domain={[48, 58]} stroke={CSS_VARS.muted} tick={{ fill: CSS_VARS.muted, fontSize: 9 }} />
              <Tooltip {...TooltipProps} />
              <Bar dataKey="accuracy" fill={CSS_VARS.accent} radius={[4,4,0,0]} label={{ fill: CSS_VARS.muted, fontSize: 11 }}>
                {lstmData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={CSS_VARS.accent} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 16 }}>
        <Card glow>
          <CardTitle>Trade PnL — {activeTicker}</CardTitle>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={tradeData}>
              <XAxis dataKey="x" stroke={CSS_VARS.muted} tick={{ fill: CSS_VARS.muted, fontSize: 9 }} />
              <YAxis stroke={CSS_VARS.muted} tick={{ fill: CSS_VARS.muted, fontSize: 9 }} />
              <Tooltip {...TooltipProps} />
              <Bar dataKey="y">
                {tradeData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.y > 0 ? CSS_VARS.green : CSS_VARS.red} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card glow>
          <CardTitle>Action Distribution</CardTitle>
          <div style={{ marginBottom: 20 }}>
            {actionData.map((action, index) => (
              <div key={index} style={{ marginBottom: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
                  <div style={{ width: 60, fontSize: 11 }}>{action.name}</div>
                  <div style={{ flex: 1, height: 20, background: CSS_VARS.cardBg, borderRadius: 4, overflow: 'hidden' }}>
                    <div
                      style={{
                        height: '100%',
                        background: action.color,
                        width: `${(action.value / 250) * 100}%`
                      }}
                    />
                  </div>
                  <div style={{ width: 30, fontSize: 11, color: CSS_VARS.muted, fontFamily: CSS_VARS.fontMono }}>
                    {action.value}
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <Btn variant="success">Force BUY</Btn>
            <Btn variant="danger">Force SELL</Btn>
          </div>
        </Card>

        <Card glow>
          <CardTitle>Recent Trades</CardTitle>
          <DataTable
            columns={[
              { key: 'ticker', label: 'Ticker', flex: 1 },
              { key: 'action', label: 'Action', render: (v) => <Badge action={v} /> },
              { key: 'pnl', label: 'PnL', flex: 1, render: (v) => <span style={{ color: col(v) }}>{v}</span> },
              { key: 'time', label: 'Time', flex: 1, render: (v) => <span style={{ color: CSS_VARS.muted, fontFamily: CSS_VARS.fontMono }}>{v}</span> }
            ]}
            data={recentTrades}
            maxHeight={155}
          />
        </Card>
      </div>
    </div>
  )
}

const SignalsPage = ({ activeTicker, setActiveTicker, selectedTicker, setSelectedTicker }) => {
  const [filter, setFilter] = useState('ALL');

  const radarData = [
    { subject: 'RSI Signal', value: TICKER_META[selectedTicker].rsi },
    { subject: 'MACD', value: Math.abs(TICKER_META[selectedTicker].macd) * 100 },
    { subject: 'Volume', value: 65 + Math.random() * 20 },
    { subject: 'Trend', value: 58 + Math.random() * 20 },
    { subject: 'VIX', value: 75 - Math.random() * 20 },
    { subject: 'BB', value: 60 + Math.random() * 20 }
  ];

  const indicators = [
    { label: 'RSI(14)', value: TICKER_META[selectedTicker].rsi, max: 100 },
    { label: 'ADX', value: 25 + Math.random() * 20, max: 100 },
    { label: 'Stoch %K', value: 45 + Math.random() * 30, max: 100 },
    { label: 'BB Width', value: 30 + Math.random() * 40, max: 100 },
    { label: 'Vol Ratio', value: 0.8 + Math.random() * 0.4, max: 2 },
    { label: 'VIX', value: 15 + Math.random() * 10, max: 50 }
  ];

  const confidence = TICKER_META[selectedTicker].acc;
  const bias = confidence > 54 ? 'LONG' : confidence > 50 ? 'NEUTRAL' : 'SHORT';

  return (
    <div className="fade-up" style={{ height: 'calc(100vh - 120px)', overflowY: 'auto' }}>
      <SectionHead
        "Live Agent Signals"
        rightSlot={
          <>
            <div style={{ display: 'flex', gap: 4 }}>
              <Btn onClick={() => setFilter('ALL')} variant={filter === 'ALL' ? 'active' : 'ghost'}>ALL</Btn>
              <Btn onClick={() => setFilter('BUY')} variant={filter === 'BUY' ? 'active' : 'ghost'}>BUY</Btn>
              <Btn onClick={() => setFilter('HOLD')} variant={filter === 'HOLD' ? 'active' : 'ghost'}>HOLD</Btn>
              <Btn onClick={() => setFilter('SELL')} variant={filter === 'SELL' ? 'active' : 'ghost'}>SELL</Btn>
            </div>
            <Btn variant="ghost">⟳ Refresh All</Btn>
          </>
        }
      />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5,1fr)', gap: 16, marginBottom: 20 }}>
        {TICKERS.map(ticker => (
          <Card
            key={ticker}
            glow
            onClick={() => setSelectedTicker(ticker)}
            style={{ opacity: filter !== 'ALL' && TICKER_META[ticker].action !== filter ? 0.3 : 1, cursor: 'pointer' }}
          >
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontFamily: CSS_VARS.fontMono, fontSize: 14, fontWeight: 'bold', marginBottom: 4 }}>
                {ticker}
              </div>
              <Badge action={TICKER_META[ticker].action} />
            </div>
            <div style={{ fontFamily: CSS_VARS.fontMono, fontSize: 18, fontWeight: 'bold', marginBottom: 8 }}>
              ${TICKER_META[ticker].price}
            </div>
            <div style={{
              fontFamily: CSS_VARS.fontMono,
              fontSize: 14,
              marginBottom: 12,
              color: TICKER_META[ticker].change > 0 ? CSS_VARS.green : CSS_VARS.red
            }}>
              {TICKER_META[ticker].change > 0 ? '▲' : '▼'} {Math.abs(TICKER_META[ticker].change)}%
            </div>
            <div style={{
              fontFamily: CSS_VARS.fontMono,
              fontSize: 11,
              color:
                TICKER_META[ticker].rsi < 30 ? CSS_VARS.green :
                TICKER_META[ticker].rsi > 70 ? CSS_VARS.red : CSS_VARS.yellow
            }}>
              RSI: {TICKER_META[ticker].rsi}
            </div>
          </Card>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 16 }}>
        <Card glow>
          <CardTitle>Signal Strength — {selectedTicker}</CardTitle>
          <ResponsiveContainer width="100%" height={250}>
            <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
              <PolarGrid stroke="rgba(0,180,255,0.1)" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: CSS_VARS.muted, fontSize: 9 }} />
              <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: CSS_VARS.muted, fontSize: 9 }} />
              <Radar name={selectedTicker} dataKey="value" stroke={CSS_VARS.accent} fill={CSS_VARS.accent} fillOpacity={0.15} />
            </RadarChart>
          </ResponsiveContainer>
        </Card>

        <Card glow>
          <CardTitle>Technical Indicators — {selectedTicker}</CardTitle>
          <div style={{ marginBottom: 20 }}>
            {indicators.map((ind, i) => (
              <RiskBar
                key={i}
                label={ind.label}
                value={ind.max === 100 ? ind.value : ind.value.toFixed(2)}
                max={ind.max}
                color={
                  ind.label.includes('RSI') ?
                    (ind.value < 30 ? CSS_VARS.green : ind.value > 70 ? CSS_VARS.red : CSS_VARS.yellow) :
                    CSS_VARS.accent
                }
              />
            ))}
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <Btn variant="primary">View Chart</Btn>
            <Btn variant="ghost">Set Alert</Btn>
          </div>
        </Card>

        <Card glow>
          <CardTitle>Model Confidence — {selectedTicker}</CardTitle>
          <div style={{ textAlign: 'center', marginBottom: 20 }}>
            <div style={{
              fontFamily: CSS_VARS.fontMono,
              fontSize: 48,
              fontWeight: 'bold',
              color: confidence > 54 ? CSS_VARS.green : CSS_VARS.yellow
            }}>
              {confidence}%
            </div>
            <div style={{
              display: 'inline-block',
              padding: '8px 16px',
              background: CSS_VARS.cardBg,
              border: `1px solid ${CSS_VARS.muted}`,
              borderRadius: 20,
              marginBottom: 20,
              fontFamily: CSS_VARS.fontMono,
              fontSize: 11
            }}>
              ● {BIAS} BIAS
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 20 }}>
              <div>
                <div style={{ fontSize: 11, color: CSS_VARS.muted }}>Agent Return</div>
                <div style={{ fontFamily: CSS_VARS.fontMono, fontSize: 18, fontWeight: 'bold', color: col(TICKER_META[selectedTicker].ret) }}>
                  {fmt(TICKER_META[selectedTicker].ret)}
                </div>
              </div>
              <div>
                <div style={{ fontSize: 11, color: CSS_VARS.muted }}>Buy & Hold</div>
                <div style={{ fontFamily: CSS_VARS.fontMono, fontSize: 18, fontWeight: 'bold', color: col(TICKER_META[selectedTicker].bh) }}>
                  {fmt(TICKER_META[selectedTicker].bh)}
                </div>
              </div>
              <div>
                <div style={{ fontSize: 11, color: CSS_VARS.muted }}>Alpha</div>
                <div style={{ fontFamily: CSS_VARS.fontMono, fontSize: 18, fontWeight: 'bold', color: col(TICKER_META[selectedTicker].alpha) }}>
                  {fmt(TICKER_META[selectedTicker].alpha)}
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <Btn variant="success">Execute BUY</Btn>
              <Btn variant="danger">Execute SELL</Btn>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}

const PortfolioPage = ({ activeTicker }) => {
  const [isSimulating, setIsSimulating] = useState(false);

  const meta = TICKER_META[activeTicker];
  const finalValue = Math.round(10000 * (1 + meta.ret / 100));

  const portfolioData = gen(353, 10000, 100);
  const drawdownData = portfolioData.map(d => ({
    ...d,
    y: Math.max(0, d.y - 11518) / 11518 * 100
  }));

  const trades = Array.from({ length: 8 }, (_, i) => ({
    '#': i + 1,
    Entry: `$${(10000 + i * 500 + Math.random() * 1000).toFixed(0)}`,
    Exit: `$${(10500 + i * 500 + Math.random() * 1000).toFixed(0)}`,
    Size: `${Math.floor(1000 + Math.random() * 2000)}`,
    PnL: `${(Math.random() * 1000 - 500).toFixed(2)}`,
    'Ret%': `${(Math.random() * 20 - 10).toFixed(2)}%`
  }));

  return (
    <div className="fade-up" style={{ height: 'calc(100vh - 120px)', overflowY: 'auto' }}>
      <SectionHead
        "Portfolio Simulation"
        rightSlot={
          <>
            <div style={{ display: 'flex', gap: 4 }}>
              {TICKERS.map(ticker => (
                <Btn
                  key={ticker}
                  onClick={() => setActiveTicker(ticker)}
                  variant={activeTicker === ticker ? 'active' : 'ghost'}
                >
                  {ticker}
                </Btn>
              ))}
            </div>
            <Btn primary onClick={() => {
              setIsSimulating(true);
              setTimeout(() => setIsSimulating(false), 2000);
            }}>
              {isSimulating ? '⟳ Running...' : '▶ Re-simulate'}
            </Btn>
            <Btn variant="ghost">↓ Export</Btn>
          </>
        }
      />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5,1fr)', gap: 16, marginBottom: 20 }}>
        <StatCard title="Initial Capital" value="$10,000" />
        <StatCard title="Final Value" value={`$${finalValue}`} color={CSS_VARS.green} />
        <StatCard title="Agent Return" value={fmt(meta.ret)} sub={`B&H: ${fmt(meta.bh)}`} color={col(meta.ret)} />
        <StatCard title="Alpha Generated" value={fmt(meta.alpha)} color={col(meta.alpha)} />
        <StatCard title="Win Rate" value={`${meta.wr}%`} sub="35 trades" color={CSS_VARS.yellow} />
      </div>

      <Card glow style={{ marginBottom: 20 }}>
        <div style={{ height: 200 }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={portfolioData}>
              <defs>
                <linearGradient id="colorAgent2" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={CSS_VARS.accent} stopOpacity={0.3}/>
                  <stop offset="95%" stopColor={CSS_VARS.accent} stopOpacity={0}/>
                </linearGradient>
              </defs>
              <Area type="monotone" dataKey="y" stroke={CSS_VARS.accent} fill="url(#colorAgent2)" name="Agent Portfolio" />
              <Line type="monotone" dataKey={(d, i) => 10000 + i * meta.bh * 10} stroke={CSS_VARS.yellow} strokeDasharray="5 5" name="Buy & Hold" />
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,180,255,0.06)" />
              <XAxis dataKey="x" stroke={CSS_VARS.muted} tick={{ fill: CSS_VARS.muted, fontSize: 9 }} />
              <YAxis stroke={CSS_VARS.muted} tick={{ fill: CSS_VARS.muted, fontSize: 9 }} tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
              <Tooltip {...TooltipProps} />
              <Legend />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 16 }}>
        <Card glow>
          <CardTitle>Drawdown Analysis</CardTitle>
          <ResponsiveContainer width="100%" height={140}>
            <AreaChart data={drawdownData}>
              <defs>
                <linearGradient id="colorDrawdown" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={CSS_VARS.red} stopOpacity={0.3}/>
                  <stop offset="95%" stopColor={CSS_VARS.red} stopOpacity={0}/>
                </linearGradient>
              </defs>
              <Area type="monotone" dataKey="y" stroke={CSS_VARS.red} fill="url(#colorDrawdown)" />
              <ReferenceLine y={0} stroke={CSS_VARS.muted} strokeDasharray="3 3" />
              <XAxis dataKey="x" stroke={CSS_VARS.muted} tick={{ fill: CSS_VARS.muted, fontSize: 9 }} />
              <YAxis stroke={CSS_VARS.muted} tick={{ fill: CSS_VARS.muted, fontSize: 9 }} />
              <Tooltip {...TooltipProps} />
            </AreaChart>
          </ResponsiveContainer>
        </Card>

        <Card glow>
          <CardTitle>Trade Log — {activeTicker}</CardTitle>
          <DataTable
            columns={[
              { key: '#', label: '#', flex: 0.5 },
              { key: 'Entry', label: 'Entry()', flex: 1 },
              { key: 'Exit', label: 'Exit()', flex: 1 },
              { key: 'Size', label: 'Exit()', flex: 0.8 },
              { key: 'PnL', label: 'PnL', flex: 1, render: (v) => <span style={{ color: col(parseFloat(v)) }}>{v}</span> },
              { key: 'Ret%', label: 'Ret%', flex: 1, render: (v) => <span style={{ color: col(parseFloat(v)) }}>{v}</span> }
            ]}
            data={trades}
            maxHeight={155}
          />
        </Card>
      </div>
    </div>
  )
}

const BacktestPage = () => {
  const [view, setView] = useState('Returns');

  const backtestData = TICKERS.map(ticker => ({
    name: ticker,
    agent: TICKER_META[ticker].ret,
    bh: TICKER_META[ticker].bh,
    alpha: TICKER_META[ticker].alpha,
    sharpe: TICKER_META[ticker].sharpe,
    winRate: TICKER_META[ticker].wr,
    maxDD: Math.abs(TICKER_META[ticker].dd)
  }));

  const metricsColumns = [
    { key: 'name', label: 'Ticker', flex: 1, render: (v) => <span style={{ fontFamily: CSS_VARS.fontMono, fontWeight: 'bold' }}>{v}</span> },
    { key: 'agent', label: 'Agent Ret', flex: 1, render: (v) => <span style={{ color: col(v) }}>{fmt(v)}</span> },
    { key: 'bh', label: 'B&H', flex: 1, render: (v) => <span style={{ color: CSS_VARS.muted }}>{fmt(v)}</span> },
    { key: 'alpha', label: 'Alpha', flex: 1, render: (v) => <span style={{ color: col(v) }}>{fmt(v)}</span> },
    { key: 'sharpe', label: 'Sharpe', flex: 1, render: (v) => <span style={{ color: col(v) }}>{v.toFixed(3)}</span> },
    { key: 'maxDD', label: 'Max DD', flex: 1, render: (v) => <span style={{ color: CSS_VARS.red }}>{fmt(v)}</span> },
    { key: 'winRate', label: 'Win Rate', flex: 1, render: (v) => <span style={{ color: CSS_VARS.yellow }}>{v}%</span> },
    { key: 'name', label: 'Profit Factor', flex: 1 },
    { key: 'name', label: 'Trades', flex: 1 }
  ];

  return (
    <div className="fade-up" style={{ height: 'calc(100vh - 120px)', overflowY: 'auto' }}>
      <SectionHead
        "Backtest Results"
        rightSlot={
          <>
            <div style={{ display: 'flex', gap: 4 }}>
              <Btn onClick={() => setView('Returns')} variant={view === 'Returns' ? 'active' : 'ghost'}>Returns</Btn>
              <Btn onClick={() => setView('Sharpe')} variant={view === 'Sharpe' ? 'active' : 'ghost'}>Sharpe</Btn>
              <Btn onClick={() => setView('Win Rate')} variant={view === 'Win Rate' ? 'active' : 'ghost'}>Win Rate</Btn>
            </div>
            <Btn variant="primary">▶ Re-run Backtest</Btn>
            <Btn variant="ghost">↓ Download Report</Btn>
          </>
        }
      />

      <Card glow style={{ marginBottom: 20 }}>
        <div style={{ height: 300 }}>
          <ResponsiveContainer width="100%" height="100%">
            {view === 'Returns' ? (
              <BarChart data={backtestData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,180,255,0.06)" />
                <XAxis dataKey="name" stroke={CSS_VARS.muted} tick={{ fill: CSS_VARS.muted, fontSize: 9 }} />
                <YAxis stroke={CSS_VARS.muted} tick={{ fill: CSS_VARS.muted, fontSize: 9 }} />
                <Tooltip {...TooltipProps} />
                <ReferenceLine y={0} stroke={CSS_VARS.muted} />
                <Bar dataKey="agent" fill={CSS_VARS.accent} name="RL Agent" />
                <Bar dataKey="bh" fill={CSS_VARS.yellow} name="Buy & Hold" />
                <Bar dataKey="alpha" fill={CSS_VARS.green} name="Alpha" />
              </BarChart>
            ) : view === 'Sharpe' ? (
              <BarChart data={backtestData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,180,255,0.06)" />
                <XAxis dataKey="name" stroke={CSS_VARS.muted} tick={{ fill: CSS_VARS.muted, fontSize: 9 }} />
                <YAxis stroke={CSS_VARS.muted} tick={{ fill: CSS_VARS.muted, fontSize: 9 }} />
                <Tooltip {...TooltipProps} />
                <ReferenceLine y={0} stroke={CSS_VARS.muted} />
                <Bar dataKey="sharpe">
                  {backtestData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.sharpe > 0 ? CSS_VARS.green : CSS_VARS.red} />
                  ))}
                </Bar>
              </BarChart>
            ) : (
              <BarChart data={backtestData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,180,255,0.06)" />
                <XAxis dataKey="name" stroke={CSS_VARS.muted} tick={{ fill: CSS_VARS.muted, fontSize: 9 }} />
                <YAxis domain={[40, 65]} stroke={CSS_VARS.muted} tick={{ fill: CSS_VARS.muted, fontSize: 9 }} />
                <Tooltip {...TooltipProps} />
                <Bar dataKey="winRate" fill={CSS_VARS.yellow} />
              </BarChart>
            )}
          </ResponsiveContainer>
        </div>
      </Card>

      <Card glow>
        <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', marginBottom: 12 }}>
          <Btn variant="ghost" style={{ marginRight: 8 }}>Sort by Alpha ↓</Btn>
          <Btn variant="ghost">Filter ▾</Btn>
        </div>
        <DataTable
          columns={metricsColumns}
          data={backtestData}
          style={{ maxHeight: '400px' }}
        />
      </Card>
    </div>
  )
}

const RiskPage = () => {
  const varData = Array.from({ length: 40 }, (_, i) => ({
    x: (i - 20) * 0.5,
    y: Math.exp(-i * i / 100) * 1000
  }));

  const months = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'];
  const years = [2022, 2023, 2024];
  const heatmapData = years.map(year =>
    months.map((month, i) => ({
      year,
      month,
      value: (Math.random() - 0.5) * 20
    }))
  ).flat();

  return (
    <div className="fade-up" style={{ height: 'calc(100vh - 120px)', overflowY: 'auto' }}>
      <SectionHead
        "Risk Monitor"
        rightSlot={
          <>
            <Btn variant="warning">⚠ Set VaR Limit</Btn>
            <Btn variant="danger">🛑 Kill Switch</Btn>
            <Btn variant="ghost">↓ Risk Report</Btn>
          </>
        }
      />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 16, marginBottom: 20 }}>
        <StatCard title="Portfolio VaR (95%)" value="-$480" sub="Daily value at risk" color={CSS_VARS.red} />
        <StatCard title="Max Drawdown" value="-30.1%" sub="AAPL worst period" color={CSS_VARS.red} />
        <StatCard title="Beta vs SPY" value="1.24" sub="Slightly above market" color={CSS_VARS.yellow} />
        <StatCard title="Annualized Vol" value="18.4%" sub="Std deviation" color={CSS_VARS.muted} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 16, marginBottom: 20 }}>
        <Card glow>
          <CardTitle>Max Drawdown by Ticker</CardTitle>
          {TICKERS.map(ticker => (
            <RiskBar
              key={ticker}
              label={ticker}
              value={Math.abs(TICKER_META[ticker].dd)}
              max={35}
              color={Math.abs(TICKER_META[ticker].dd) > 25 ? CSS_VARS.red : CSS_VARS.yellow}
            />
          ))}
        </Card>

        <Card glow>
          <CardTitle>Correlation Matrix</CardTitle>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6,1fr)', fontSize: 9 }}>
            <div style={{ textAlign: 'center', padding: 8, color: CSS_VARS.muted }}>•</div>
            {TICKERS.map(ticker => (
              <div key={ticker} style={{ textAlign: 'center', padding: 8, color: CSS_VARS.muted }}>{ticker}</div>
            ))}
            {TICKERS.map((rowTicker, i) => (
              React.Children.toArray([TICKERS.map((colTicker, j) => {
                const corr = i === j ? 1 : 0.5 + Math.random() * 0.45;
                const opacity = corr;
                const bgColor = `rgba(0,229,160,${opacity})`;
                return (
                  <div
                    key={`${i}-${j}`}
                    style={{
                      textAlign: 'center',
                      padding: 8,
                      background: bgColor,
                      color: opacity > 0.7 ? '#000' : '#fff',
                      fontFamily: CSS_VARS.fontMono
                    }}
                  >
                    {corr.toFixed(2)}
                  </div>
                );
              }))]
            ))}
          </div>
        </Card>
      </div>

      <Card glow>
        <CardTitle>Return Distribution — All Tickers</CardTitle>
        <ResponsiveContainer width="100%" height={150}>
          <BarChart data={varData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,180,255,0.06)" />
            <XAxis dataKey="x" stroke={CSS_VARS.muted} tick={{ fill: CSS_VARS.muted, fontSize: 9 }} tickFormatter={(v) => `${v}%`} />
            <YAxis stroke={CSS_VARS.muted} tick={{ fill: CSS_VARS.muted, fontSize: 9 }} />
            <Tooltip {...TooltipProps} />
            <ReferenceLine x={0} stroke={CSS_VARS.muted} strokeDasharray="3 3" />
            <Bar dataKey="y" fill={CSS_VARS.accent} fillOpacity={0.7} />
          </BarChart>
        </ResponsiveContainer>
      </Card>
    </div>
  )
}

const AnalyticsPage = () => {
  const [view, setView] = useState('Equity Curves');

  const equityData = TICKERS.map(ticker =>
    Array.from({ length: 253 }, (_, i) => ({
      x: i,
      y: 100 + i * 0.1 + Math.random() * 10
    }))
  );

  const trainingData = Array.from({ length: 50 }, (_, i) => ({
    x: i,
    train: 48 + Math.random() * 10,
    val: 48 + Math.random() * 10
  }));

  const rewardData = Array.from({ length: 50 }, (_, i) => ({
    x: i,
    y: -50 + i * 3 + Math.random() * 20
  }));

  const shapData = [
    { label: 'RSI_14', value: 82 },
    { label: 'MACD', value: 74 },
    { label: 'VIX', value: 68 },
    { label: 'ADX', value: 55 },
    { label: 'Vol Ratio', value: 48 },
    { label: 'BB Width', value: 41 }
  ];

  return (
    <div className="fade-up" style={{ height: 'calc(100vh - 120px)', overflowY: 'auto' }}>
      <SectionHead
        "Advanced Analytics"
        rightSlot={
          <Btn variant="ghost">↓ Export Data</Btn>
        }
      />

      <Card glow style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', gap: 4, marginBottom: 16 }}>
          <Btn onClick={() => setView('Equity Curves')} variant={view === 'Equity Curves' ? 'active' : 'ghost'}>Equity Curves</Btn>
          <Btn onClick={() => setView('LSTM Training')} variant={view === 'LSTM Training' ? 'active' : 'ghost'}>LSTM Training</Btn>
          <Btn onClick={() => setView('RL Reward')} variant={view === 'RL Reward' ? 'active' : 'ghost'}>RL Reward</Btn>
        </div>
        <div style={{ height: 300 }}>
          <ResponsiveContainer width="100%" height="100%">
            {view === 'Equity Curves' ? (
              <LineChart data={equityData[0]}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,180,255,0.06)" />
                <XAxis dataKey="x" stroke={CSS_VARS.muted} tick={{ fill: CSS_VARS.muted, fontSize: 9 }} />
                <YAxis stroke={CSS_VARS.muted} tick={{ fill: CSS_VARS.muted, fontSize: 9 }} />
                <Tooltip {...TooltipProps} />
                <Line type="monotone" dataKey="y" stroke={CSS_VARS.accent} name="AAPL" />
                <Line type="monotone" dataKey="y" stroke={CSS_VARS.green} strokeDasharray="5 5" data={equityData[1]} name="SPY" />
                <Line type="monotone" dataKey="y" stroke={CSS_VARS.yellow} strokeDasharray="5 5" data={equityData[2]} name="QQQ" />
              </LineChart>
            ) : view === 'LSTM Training' ? (
              <LineChart data={trainingData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,180,255,0.06)" />
                <XAxis dataKey="x" stroke={CSS_VARS.muted} tick={{ fill: CSS_VARS.muted, fontSize: 9 }} />
                <YAxis domain={[48, 60]} stroke={CSS_VARS.muted} tick={{ fill: CSS_VARS.muted, fontSize: 9 }} />
                <Tooltip {...TooltipProps} />
                <ReferenceLine y={52} stroke={CSS_VARS.muted} strokeDasharray="3 3" label="Random" />
                <Line type="monotone" dataKey="train" stroke={CSS_VARS.accent} name="Train Acc" />
                <Line type="monotone" dataKey="val" stroke={CSS_VARS.yellow} strokeDasharray="5 5" name="Val Acc" />
              </LineChart>
            ) : (
              <LineChart data={rewardData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,180,255,0.06)" />
                <XAxis dataKey="x" stroke={CSS_VARS.muted} tick={{ fill: CSS_VARS.muted, fontSize: 9 }} />
                <YAxis stroke={CSS_VARS.muted} tick={{ fill: CSS_VARS.muted, fontSize: 9 }} />
                <Tooltip {...TooltipProps} />
                <ReferenceLine y={0} stroke={CSS_VARS.muted} strokeDasharray="3 3" />
                <Line type="monotone" dataKey="y" stroke={CSS_VARS.yellow} name="RL Reward" />
              </LineChart>
            )}
          </ResponsiveContainer>
        </div>
      </Card>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 16 }}>
        <Card glow>
          <CardTitle>Feature Importance (SHAP)</CardTitle>
          {shapData.map((item, i) => (
            <RiskBar
              key={i}
              label={item.label}
              value={item.value}
              max={100}
              color={CSS_VARS.accent}
            />
          ))}
        </Card>

        <Card glow>
          <CardTitle>Monthly Returns Heatmap (AAPL)</CardTitle>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(13,1fr)', fontSize: 9 }}>
            <div style={{ textAlign: 'center', padding: 4, color: CSS_VARS.muted }}>•</div>
            {months.map(month => (
              <div key={month} style={{ textAlign: 'center', padding: 4, color: CSS_VARS.muted }}>{month}</div>
            ))}
            {years.map(year =>
              months.map((month, i) => {
                const value = (Math.random() - 0.5) * 20;
                return (
                  <div
                    key={`${year}-${i}`}
                    style={{
                      textAlign: 'center',
                      padding: 4,
                      background: value > 0 ? `rgba(0,229,160,${Math.abs(value)/20})` : `rgba(255,64,96,${Math.abs(value)/20})`,
                      color: value > 0 ? '#000' : '#fff',
                      fontFamily: CSS_VARS.fontMono
                    }}
                  >
                    {value.toFixed(1)}%
                  </div>
                );
              })
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}

const AlertsPage = ({ alerts, setAlerts }) => {
  const [settings, setSettings] = useState({
    rsiOversold: true,
    rsiOverbought: true,
    maxDD: true,
    dailySummary: false,
    emailAlerts: false
  });

  const initialAlerts = [
    { id: 1, type: 'BUY', title: 'BUY AAPL', description: 'Strong buy signal detected', time: '14:32:15' },
    { id: 2, type: 'SELL', title: 'SELL NVDA', description: 'Overbought condition detected', time: '14:28:43' },
    { id: 3, type: 'INFO', title: 'Max Hold QQQ', description: 'Position approaching max hold period', time: '14:15:22' },
    { id: 4, type: 'INFO', title: 'Retrain Complete', description: 'LSTM model retraining finished', time: '13:45:10' },
    { id: 5, type: 'BUY', title: 'BUY SPY', description: 'RSI oversold signal triggered', time: '13:22:05' }
  ];

  useEffect(() => {
    setAlerts(initialAlerts);
  }, []);

  const removeAlert = (id) => {
    setAlerts(alerts.filter(alert => alert.id !== id));
  };

  const toggleSetting = (key) => {
    setSettings({...settings, [key]: !settings[key]});
  };

  return (
    <div className="fade-up" style={{ height: 'calc(100vh - 120px)', overflowY: 'auto' }}>
      <SectionHead
        "Alerts & Notifications"
        rightSlot={
          <>
            <Btn variant="danger" onClick={() => setAlerts([])}>Clear All</Btn>
            <Btn variant="primary">+ Add Rule</Btn>
            <Btn variant="ghost">⚙ Manage</Btn>
          </>
        }
      />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 16 }}>
        <Card glow>
          {alerts.length > 0 ? (
            alerts.map(alert => (
              <div
                key={alert.id}
                style={{
                  padding: 16,
                  borderLeft: `4px solid ${alert.type === 'BUY' ? CSS_VARS.green : alert.type === 'SELL' ? CSS_VARS.red : CSS_VARS.accent}`,
                  marginBottom: 12,
                  background: CSS_VARS.cardBg,
                  borderRadius: 8,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
                    <span style={{
                      fontSize: 16,
                      marginRight: 8,
                      color: alert.type === 'BUY' ? CSS_VARS.green : alert.type === 'SELL' ? CSS_VARS.red : CSS_VARS.accent
                    }}>
                      {alert.type === 'BUY' ? '▲' : alert.type === 'SELL' ? '▼' : '◉'}
                    </span>
                    <span style={{ fontWeight: 'bold' }}>{alert.title}</span>
                  </div>
                  <div style={{ fontSize: 12, color: CSS_VARS.muted, marginBottom: 4 }}>
                    {alert.description}
                  </div>
                  <div style={{ fontSize: 11, color: CSS_VARS.muted, fontFamily: CSS_VARS.fontMono }}>
                    {alert.time}
                  </div>
                </div>
                <Btn
                  variant="ghost"
                  style={{ padding: 4, minWidth: 24 }}
                  onClick={() => removeAlert(alert.id)}
                >
                  ×
                </Btn>
              </div>
            ))
          ) : (
            <div style={{
              textAlign: 'center',
              padding: 40,
              color: CSS_VARS.muted,
              fontFamily: CSS_VARS.fontMono,
              fontSize: 14
            }}>
              No active alerts
            </div>
          )}
        </Card>

        <Card glow>
          <CardTitle>Alert Configuration</CardTitle>
          <div style={{ display: 'grid', gap: 20 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 11, color: CSS_VARS.accent }}>RSI Oversold</div>
                <div style={{ fontSize: 9, color: CSS_VARS.muted }}>Alert when RSI < 30</div>
              </div>
              <Toggle checked={settings.rsiOversold} onChange={() => toggleSetting('rsiOversold')} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 11, color: CSS_VARS.accent }}>RSI Overbought</div>
                <div style={{ fontSize: 9, color: CSS_VARS.muted }}>Alert when RSI > 70</div>
              </div>
              <Toggle checked={settings.rsiOverbought} onChange={() => toggleSetting('rsiOverbought')} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 11, color: CSS_VARS.accent }}>Max Drawdown</div>
                <div style={{ fontSize: 9, color: CSS_VARS.muted }}>Alert when DD > 15%</div>
              </div>
              <Toggle checked={settings.maxDD} onChange={() => toggleSetting('maxDD')} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 11, color: CSS_VARS.accent }}>Daily Summary</div>
                <div style={{ fontSize: 9, color: CSS_VARS.muted }}>End-of-day report</div>
              </div>
              <Toggle checked={settings.dailySummary} onChange={() => toggleSetting('dailySummary')} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 11, color: CSS_VARS.accent }}>Email Alerts</div>
                <div style={{ fontSize: 9, color: CSS_VARS.muted }}>Send email notifications</div>
              </div>
              <Toggle checked={settings.emailAlerts} onChange={() => toggleSetting('emailAlerts')} />
            </div>
          </div>

          <div style={{ display: 'flex', gap: 8, marginTop: 24 }}>
            <Btn variant="primary">Save Settings</Btn>
            <Btn variant="ghost">Test Alert</Btn>
          </div>
        </Card>
      </div>
    </div>
  )
}

const SettingsPage = ({ apiStatus }) => {
  const [settings, setSettings] = useState({
    apiBaseUrl: 'http://localhost:8000',
    autoRefresh: '10 sec',
    websocketFeed: true,
    debugMode: false,
    initialCapital: '$10,000',
    commissionRate: '0.10%',
    maxHoldPeriod: '10 days',
    positionSizing: '75%',
    activeModel: 'LSTM + Attention',
    sequenceLength: '30 days',
    autoRetrain: false,
    useMPS: true,
    currency: 'USD ($)',
    chartStyle: 'Line',
    showTooltips: true,
    compactMode: false
  });

  const systemStatus = [
    { name: 'API Server', status: 'Online', color: CSS_VARS.green },
    { name: 'LSTM Models', status: '3 Loaded', color: CSS_VARS.green },
    { name: 'RL Agents', status: '3 Loaded', color: CSS_VARS.green },
    { name: 'WebSocket', status: 'Connected', color: CSS_VARS.accent }
  ];

  const toggleSetting = (key) => {
    setSettings({...settings, [key]: !settings[key]});
  };

  const selectOption = (key, value) => {
    setSettings({...settings, [key]: value});
  };

  return (
    <div className="fade-up" style={{ height: 'calc(100vh - 120px)', overflowY: 'auto' }}>
      <SectionHead
        "System Settings"
        rightSlot={
          <>
            <Btn variant="primary" onClick={() => alert('✓ Saved!')}>💾 Save All</Btn>
            <Btn variant="danger">Reset Defaults</Btn>
          </>
        }
      />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 16, marginBottom: 20 }}>
        <Card glow>
          <CardTitle>API Configuration</CardTitle>
          <div style={{ display: 'grid', gap: 16 }}>
            <div>
              <div style={{ fontSize: 11, color: CSS_VARS.muted, marginBottom: 4 }}>API Base URL</div>
              <input
                type="text"
                value={settings.apiBaseUrl}
                onChange={(e) => setSettings({...settings, apiBaseUrl: e.target.value})}
                style={{
                  width: '100%',
                  padding: 8,
                  background: CSS_VARS.sidebarBg,
                  border: `1px solid ${CSS_VARS.border}`,
                  borderRadius: 6,
                  color: CSS_VARS.text,
                  fontFamily: CSS_VARS.fontMono,
                  fontSize: 11
                }}
              />
            </div>

            <div>
              <div style={{ fontSize: 11, color: CSS_VARS.muted, marginBottom: 4 }}>Auto-refresh</div>
              <select
                value={settings.autoRefresh}
                onChange={(e) => selectOption('autoRefresh', e.target.value)}
                style={{
                  width: '100%',
                  padding: 8,
                  background: CSS_VARS.sidebarBg,
                  border: `1px solid ${CSS_VARS.border}`,
                  borderRadius: 6,
                  color: CSS_VARS.text,
                  fontFamily: CSS_VARS.fontMono,
                  fontSize: 11
                }}
              >
                <option>5 sec</option>
                <option>10 sec</option>
                <option>30 sec</option>
                <option>1 min</option>
              </select>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 11, color: CSS_VARS.muted }}>WebSocket Live Feed</div>
                <div style={{ fontSize: 9, color: CSS_VARS.muted }}>Real-time data streaming</div>
              </div>
              <Toggle checked={settings.websocketFeed} onChange={() => toggleSetting('websocketFeed')} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 11, color: CSS_VARS.muted }}>Debug Mode</div>
                <div style={{ fontSize: 9, color: CSS_VARS.muted }}>Verbose logging</div>
              </div>
              <Toggle checked={settings.debugMode} onChange={() => toggleSetting('debugMode')} />
            </div>
          </div>
        </Card>

        <Card glow>
          <CardTitle>Trading Parameters</CardTitle>
          <div style={{ display: 'grid', gap: 16 }}>
            <div>
              <div style={{ fontSize: 11, color: CSS_VARS.muted, marginBottom: 4 }}>Initial Capital</div>
              <input
                type="text"
                value={settings.initialCapital}
                onChange={(e) => setSettings({...settings, initialCapital: e.target.value})}
                style={{
                  width: '100%',
                  padding: 8,
                  background: CSS_VARS.sidebarBg,
                  border: `1px solid ${CSS_VARS.border}`,
                  borderRadius: 6,
                  color: CSS_VARS.text,
                  fontFamily: CSS_VARS.fontMono,
                  fontSize: 11
                }}
              />
            </div>

            <div>
              <div style={{ fontSize: 11, color: CSS_VARS.muted, marginBottom: 4 }}>Commission Rate</div>
              <select
                value={settings.commissionRate}
                onChange={(e) => selectOption('commissionRate', e.target.value)}
                style={{
                  width: '100%',
                  padding: 8,
                  background: CSS_VARS.sidebarBg,
                  border: `1px solid ${CSS_VARS.border}`,
                  borderRadius: 6,
                  color: CSS_VARS.text,
                  fontFamily: CSS_VARS.fontMono,
                  fontSize: 11
                }}
              >
                <option>0.05%</option>
                <option>0.10%</option>
                <option>0.25%</option>
              </select>
            </div>

            <div>
              <div style={{ fontSize: 11, color: CSS_VARS.muted, marginBottom: 4 }}>Max Hold Period</div>
              <select
                value={settings.maxHoldPeriod}
                onChange={(e) => selectOption('maxHoldPeriod', e.target.value)}
                style={{
                  width: '100%',
                  padding: 8,
                  background: CSS_VARS.sidebarBg,
                  border: `1px solid ${CSS_VARS.border}`,
                  borderRadius: 6,
                  color: CSS_VARS.text,
                  fontFamily: CSS_VARS.fontMono,
                  fontSize: 11
                }}
              >
                <option>5 days</option>
                <option>10 days</option>
                <option>20 days</option>
              </select>
            </div>

            <div>
              <div style={{ fontSize: 11, color: CSS_VARS.muted, marginBottom: 4 }}>Position Sizing</div>
              <select
                value={settings.positionSizing}
                onChange={(e) => selectOption('positionSizing', e.target.value)}
                style={{
                  width: '100%',
                  padding: 8,
                  background: CSS_VARS.sidebarBg,
                  border: `1px solid ${CSS_VARS.border}`,
                  borderRadius: 6,
                  color: CSS_VARS.text,
                  fontFamily: CSS_VARS.fontMono,
                  fontSize: 11
                }}
              >
                <option>50%</option>
                <option>75%</option>
                <option>95%</option>
              </select>
            </div>
          </div>
        </Card>

        <Card glow>
          <CardTitle>Model Configuration</CardTitle>
          <div style={{ display: 'grid', gap: 16 }}>
            <div>
              <div style={{ fontSize: 11, color: CSS_VARS.muted, marginBottom: 4 }}>Active Model</div>
              <select
                value={settings.activeModel}
                onChange={(e) => selectOption('activeModel', e.target.value)}
                style={{
                  width: '100%',
                  padding: 8,
                  background: CSS_VARS.sidebarBg,
                  border: `1px solid ${CSS_VARS.border}`,
                  borderRadius: 6,
                  color: CSS_VARS.text,
                  fontFamily: CSS_VARS.fontMono,
                  fontSize: 11
                }}
              >
                <option>LSTM + Attention</option>
                <option>Simple LSTM</option>
                <option>Transformer</option>
              </select>
            </div>

            <div>
              <div style={{ fontSize: 11, color: CSS_VARS.muted, marginBottom: 4 }}>Sequence Length</div>
              <select
                value={settings.sequenceLength}
                onChange={(e) => selectOption('sequenceLength', e.target.value)}
                style={{
                  width: '100%',
                  padding: 8,
                  background: CSS_VARS.sidebarBg,
                  border: `1px solid ${CSS_VARS.border}`,
                  borderRadius: 6,
                  color: CSS_VARS.text,
                  fontFamily: CSS_VARS.fontMono,
                  fontSize: 11
                }}
              >
                <option>30 days</option>
                <option>60 days</option>
                <option>90 days</option>
              </select>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 11, color: CSS_VARS.muted }}>Auto Retrain</div>
                <div style={{ fontSize: 9, color: CSS_VARS.muted }}>Retrain models periodically</div>
              </div>
              <Toggle checked={settings.autoRetrain} onChange={() => toggleSetting('autoRetrain')} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 11, color: CSS_VARS.muted }}>Use Apple MPS</div>
                <div style={{ fontSize: 9, color: CSS_VARS.muted }}>GPU acceleration on M1/M2/M3</div>
              </div>
              <Toggle checked={settings.useMPS} onChange={() => toggleSetting('useMPS')} />
            </div>
          </div>
        </Card>

        <Card glow>
          <CardTitle>Display Preferences</CardTitle>
          <div style={{ display: 'grid', gap: 16 }}>
            <div>
              <div style={{ fontSize: 11, color: CSS_VARS.muted, marginBottom: 4 }}>Currency</div>
              <select
                value={settings.currency}
                onChange={(e) => selectOption('currency', e.target.value)}
                style={{
                  width: '100%',
                  padding: 8,
                  background: CSS_VARS.sidebarBg,
                  border: `1px solid ${CSS_VARS.border}`,
                  borderRadius: 6,
                  color: CSS_VARS.text,
                  fontFamily: CSS_VARS.fontMono,
                  fontSize: 11
                }}
              >
                <option>USD ($)</option>
                <option>EUR (€)</option>
                <option>INR (₹)</option>
              </select>
            </div>

            <div>
              <div style={{ fontSize: 11, color: CSS_VARS.muted, marginBottom: 4 }}>Chart Style</div>
              <select
                value={settings.chartStyle}
                onChange={(e) => selectOption('chartStyle', e.target.value)}
                style={{
                  width: '100%',
                  padding: 8,
                  background: CSS_VARS.sidebarBg,
                  border: `1px solid ${CSS_VARS.border}`,
                  borderRadius: 6,
                  color: CSS_VARS.text,
                  fontFamily: CSS_VARS.fontMono,
                  fontSize: 11
                }}
              >
                <option>Line</option>
                <option>Area</option>
                <option>Candlestick</option>
              </select>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 11, color: CSS_VARS.muted }}>Show Tooltips</div>
                <div style={{ fontSize: 9, color: CSS_VARS.muted }}>Display chart tooltips</div>
              </div>
              <Toggle checked={settings.showTooltips} onChange={() => toggleSetting('showTooltips')} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 11, color: CSS_VARS.muted }}>Compact Mode</div>
                <div style={{ fontSize: 9, color: CSS_VARS.muted }}>Reduce spacing</div>
              </div>
              <Toggle checked={settings.compactMode} onChange={() => toggleSetting('compactMode')} />
            </div>
          </div>
        </Card>
      </div>

      <Card glow>
        <CardTitle>System Status</CardTitle>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 16 }}>
          {systemStatus.map((status, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center' }}>
              <div
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: 50,
                  background: status.color,
                  marginRight: 8,
                  animation: 'pulse 2s infinite'
                }}
              />
              <div>
                <div style={{ fontSize: 11, color: CSS_VARS.muted }}>{status.name}</div>
                <div style={{ fontSize: 11, fontFamily: CSS_VARS.fontMono }}>{status.status}</div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}

// Main App Component
export default function App() {
  const [page, setPage] = useState('Overview');
  const [activeTicker, setActiveTicker] = useState('SPY');
  const [selectedTicker, setSelectedTicker] = useState('SPY');
  const [apiStatus, setApiStatus] = useState('online');
  const [alerts, setAlerts] = useState([]);
  const [time, setTime] = useState(new Date().toLocaleTimeString('en-US', { hour12: false }));

  // Update time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date().toLocaleTimeString('en-US', { hour12: false }));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Simulate API status check
  useEffect(() => {
    const checkApi = () => {
      // Randomly simulate online/offline
      setApiStatus(Math.random() > 0.1 ? 'online' : 'offline');
    };
    checkApi();
    const interval = setInterval(checkApi, 10000);
    return () => clearInterval(interval);
  }, []);

  // Navigation items
  const navItems = [
    { id: 'Overview', label: 'Overview', icon: '📊' },
    { id: 'Signals', label: 'Signals', icon: '📡' },
    { id: 'Portfolio', label: 'Portfolio', icon: '💼' },
    { id: 'Backtest', label: 'Backtest', icon: '🔬' },
    { id: 'Risk', label: 'Risk', icon: '⚠️' },
    { id: 'Analytics', label: 'Analytics', icon: '📈' },
    { id: 'Alerts', label: 'Alerts', icon: '🔔' },
    { id: 'Settings', label: 'Settings', icon: '⚙️' }
  ];

  // Render current page
  const renderPage = () => {
    switch (page) {
      case 'Overview': return <OverviewPage activeTicker={activeTicker} setActiveTicker={setActiveTicker} />;
      case 'Signals': return <SignalsPage activeTicker={activeTicker} setActiveTicker={setActiveTicker} selectedTicker={selectedTicker} setSelectedTicker={setSelectedTicker} />;
      case 'Portfolio': return <PortfolioPage activeTicker={activeTicker} />;
      case 'Backtest': return <BacktestPage />;
      case 'Risk': return <RiskPage />;
      case 'Analytics': return <AnalyticsPage />;
      case 'Alerts': return <AlertsPage alerts={alerts} setAlerts={setAlerts} />;
      case 'Settings': return <SettingsPage apiStatus={apiStatus} />;
      default: return <OverviewPage activeTicker={activeTicker} setActiveTicker={setActiveTicker} />;
    }
  };

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '210px 1fr',
      gridTemplateRows: '52px 1fr',
      height: '100vh',
      background: CSS_VARS.bg
    }}>
      {/* Topbar */}
      <div style={{ gridRow: 1, gridColumn: '1 / -1', background: CSS_VARS.sidebarBg, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 20px', borderBottom: `1px solid ${CSS_VARS.border}` }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div style={{
            width: 8,
            height: 8,
            borderRadius: 50,
            background: CSS_VARS.accent,
            marginRight: 8,
            animation: 'pulse 2s infinite'
          }} />
          <span style={{ fontFamily: CSS_VARS.fontMono, fontSize: 14, color: CSS_VARS.accent }}>QUANTAI</span>
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          {TICKERS.slice(0, 4).map(ticker => (
            <div
              key={ticker}
              className={`ticker-pill ${activeTicker === ticker ? 'active' : ''}`}
              onClick={() => setActiveTicker(ticker)}
            >
              <span style={{ fontFamily: CSS_VARS.fontMono }}>{ticker}</span>
              <span style={{ marginLeft: 8, color: TICKER_META[ticker].change > 0 ? CSS_VARS.green : CSS_VARS.red }}>
                {TICKER_META[ticker].change > 0 ? '+' : ''}{TICKER_META[ticker].change}%
              </span>
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{
              width: 8,
              height: 8,
              borderRadius: 50,
              background: apiStatus === 'online' ? CSS_VARS.green : CSS_VARS.red,
              marginRight: 8
            }} />
            <span style={{ fontFamily: CSS_VARS.fontMono, fontSize: 11 }}>
              {apiStatus === 'online' ? 'API ONLINE' : 'API OFFLINE'}
            </span>
          </div>
          <div style={{ fontFamily: CSS_VARS.fontMono, fontSize: 11 }}>
            {time} EST
          </div>
        </div>
      </div>

      {/* Sidebar */}
      <div style={{ gridRow: 2, background: CSS_VARS.sidebarBg, padding: '20px', overflowY: 'auto' }}>
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontFamily: CSS_VARS.fontMono, fontSize: 11, color: CSS_VARS.muted, marginBottom: 12, textTransform: 'uppercase', letterSpacing: 1 }}>
            Navigation
          </div>
          <div style={{ display: 'grid', gap: 4 }}>
            {navItems.map(item => (
              <div
                key={item.id}
                className={`nav-item ${page === item.id ? 'active' : ''}`}
                onClick={() => setPage(item.id)}
                style={{ padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer' }}
              >
                <span style={{ fontSize: 16 }}>{item.icon}</span>
                <span>{item.label}</span>
                {item.label === 'Alerts' && alerts.length > 0 && (
                  <div style={{
                    background: CSS_VARS.red,
                    color: '#fff',
                    borderRadius: 10,
                    padding: '2px 6px',
                    fontSize: 10,
                    marginLeft: 'auto'
                  }}>
                    {alerts.length}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div style={{ borderBottom: `1px solid ${CSS_VARS.border}`, margin: '20px 0' }} />

        <div>
          <div style={{ fontFamily: CSS_VARS.fontMono, fontSize: 11, color: CSS_VARS.muted, marginBottom: 12, textTransform: 'uppercase', letterSpacing: 1 }}>
            Watchlist
          </div>
          <div style={{ display: 'grid', gap: 8 }}>
            {TICKERS.map(ticker => (
              <Card
                key={ticker}
                glow={activeTicker === ticker}
                style={{ padding: '12px', cursor: 'pointer', border: activeTicker === ticker ? `1px solid ${CSS_VARS.accent}` : 'none' }}
                onClick={() => setActiveTicker(ticker)}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <div style={{ fontFamily: CSS_VARS.fontMono, fontSize: 12, fontWeight: 'bold' }}>{ticker}</div>
                  <Badge action={TICKER_META[ticker].action} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontFamily: CSS_VARS.fontMono, fontSize: 11 }}>
                    ${TICKER_META[ticker].price}
                  </div>
                  <div style={{
                    fontFamily: CSS_VARS.fontMono,
                    fontSize: 10,
                    color: TICKER_META[ticker].change > 0 ? CSS_VARS.green : CSS_VARS.red
                  }}>
                    {TICKER_META[ticker].change > 0 ? '+' : ''}{TICKER_META[ticker].change}%
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ gridRow: 2, background: CSS_VARS.bg, overflow: 'hidden' }}>
        {renderPage()}
      </div>
    </div>
  );
}