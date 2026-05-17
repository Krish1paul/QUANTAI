import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import accuracy_score, classification_report
from sklearn.utils.class_weight import compute_class_weight
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import warnings
warnings.filterwarnings('ignore')

os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs("models", exist_ok=True)

# ── Config ───────────────────────────────────────────────────
SEQ_LEN    = 60      # 60 trading days lookback (~3 months)
BATCH_SIZE = 32
EPOCHS     = 50
LR         = 0.0005
DEVICE     = torch.device(
    "mps"  if torch.backends.mps.is_available()  else
    "cuda" if torch.cuda.is_available()           else
    "cpu"
)
print(f"Using device: {DEVICE}")

FEATURE_COLS = [
    'returns', 'log_returns', 'hl_spread',
    'rsi_14', 'rsi_7', 'macd', 'macd_sig', 'macd_diff', 'stoch_k',
    'bb_width', 'atr_14',
    'ema_9', 'ema_21', 'ema_50', 'sma_20', 'adx',
    'vol_ratio', 'vix'
]

# ── Dataset ──────────────────────────────────────────────────
class StockDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)
    def __len__(self): return len(self.X)
    def __getitem__(self, i): return self.X[i], self.y[i]

# ── Attention layer ──────────────────────────────────────────
class Attention(nn.Module):
    def __init__(self, hidden_size):
        super().__init__()
        self.attn    = nn.Linear(hidden_size, hidden_size)
        self.context = nn.Linear(hidden_size, 1, bias=False)

    def forward(self, lstm_out):
        # lstm_out: (batch, seq, hidden)
        attn_weights = torch.tanh(self.attn(lstm_out))
        attn_weights = self.context(attn_weights).squeeze(-1)
        attn_weights = torch.softmax(attn_weights, dim=1)
        # Weighted sum
        context = (lstm_out * attn_weights.unsqueeze(-1)).sum(dim=1)
        return context

# ── LSTM + Attention Model ───────────────────────────────────
class LSTMAttention(nn.Module):
    def __init__(self, input_size, hidden_size=256, num_layers=3, dropout=0.3):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout,
            bidirectional=True        # reads sequence forward AND backward
        )
        self.attention = Attention(hidden_size * 2)  # *2 for bidirectional
        self.dropout   = nn.Dropout(dropout)
        self.bn        = nn.BatchNorm1d(hidden_size * 2)
        self.fc1       = nn.Linear(hidden_size * 2, 128)
        self.fc2       = nn.Linear(128, 64)
        self.fc3       = nn.Linear(64, 1)
        self.relu      = nn.ReLU()
        self.sigmoid   = nn.Sigmoid()

    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        context     = self.attention(lstm_out)
        context     = self.bn(context)
        context     = self.dropout(context)
        out         = self.relu(self.fc1(context))
        out         = self.dropout(out)
        out         = self.relu(self.fc2(out))
        out         = self.fc3(out)
        return self.sigmoid(out).squeeze()

# ── Data preparation ─────────────────────────────────────────
def prepare_data(ticker="AAPL"):
    df = pd.read_csv(f"data/processed/features_daily_{ticker}.csv")

    available = [c for c in FEATURE_COLS if c in df.columns]
    print(f"  Using {len(available)}/{len(FEATURE_COLS)} features")

    X_raw = df[available].values.astype(np.float32)
    y_raw = df['target'].values.astype(np.float32)

    # RobustScaler handles outliers better than MinMax for financial data
    scaler   = RobustScaler()
    X_scaled = scaler.fit_transform(X_raw)

    # Build sequences
    X, y = [], []
    for i in range(SEQ_LEN, len(X_scaled)):
        X.append(X_scaled[i-SEQ_LEN:i])
        y.append(y_raw[i])
    X, y = np.array(X), np.array(y)

    # Chronological split
    n  = len(X)
    t1 = int(n * 0.70)
    t2 = int(n * 0.85)

    return (
        X[:t1], y[:t1],
        X[t1:t2], y[t1:t2],
        X[t2:],  y[t2:],
        scaler, len(available)
    )

# ── Training ─────────────────────────────────────────────────
def train(ticker="AAPL"):
    print(f"\n{'='*50}")
    print(f"Training LSTM+Attention for {ticker}")
    print(f"{'='*50}")

    X_train, y_train, X_val, y_val, X_test, y_test, scaler, n_feat = prepare_data(ticker)
    print(f"  Train: {len(X_train)} | Val: {len(X_val)} | Test: {len(X_test)}")

    # Handle class imbalance
    classes      = np.array([0, 1])
    class_weights = compute_class_weight('balanced', classes=classes, y=y_train)
    pos_weight    = torch.tensor([class_weights[1] / class_weights[0]],
                                  dtype=torch.float32).to(DEVICE)

    train_loader = DataLoader(StockDataset(X_train, y_train),
                              batch_size=BATCH_SIZE, shuffle=False)
    val_loader   = DataLoader(StockDataset(X_val, y_val),
                              batch_size=BATCH_SIZE, shuffle=False)

    model     = LSTMAttention(input_size=n_feat).to(DEVICE)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

    best_val_acc   = 0
    best_state     = None
    patience_count = 0
    PATIENCE       = 10   # stop if no improvement for 10 epochs

    for epoch in range(EPOCHS):
        # Train
        model.train()
        train_loss = 0
        for xb, yb in train_loader:
            xb, yb = xb.to(DEVICE), yb.to(DEVICE)
            optimizer.zero_grad()
            preds = model(xb)
            loss  = criterion(preds, yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            train_loss += loss.item()

        # Validate
        model.eval()
        val_preds, val_true = [], []
        with torch.no_grad():
            for xb, yb in val_loader:
                xb = xb.to(DEVICE)
                p  = torch.sigmoid(model(xb))
                val_preds.extend((p > 0.5).cpu().numpy())
                val_true.extend(yb.numpy())

        val_acc = accuracy_score(val_true, val_preds)
        scheduler.step()

        if (epoch + 1) % 10 == 0:
            print(f"  Epoch {epoch+1:02d}/{EPOCHS} | "
                  f"Loss: {train_loss/len(train_loader):.4f} | "
                  f"Val Acc: {val_acc:.4f}")

        # Save best
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_state   = {k: v.clone() for k, v in model.state_dict().items()}
            patience_count = 0
        else:
            patience_count += 1

        if patience_count >= PATIENCE:
            print(f"  Early stopping at epoch {epoch+1}")
            break

    # Test
    model.load_state_dict(best_state)
    model.eval()
    test_loader = DataLoader(StockDataset(X_test, y_test),
                             batch_size=BATCH_SIZE, shuffle=False)
    test_preds, test_true = [], []
    with torch.no_grad():
        for xb, yb in test_loader:
            xb = xb.to(DEVICE)
            p  = torch.sigmoid(model(xb))
            test_preds.extend((p > 0.5).cpu().numpy())
            test_true.extend(yb.numpy())

    test_acc = accuracy_score(test_true, test_preds)
    print(f"\n  Best Val Acc : {best_val_acc:.4f}")
    print(f"  Test Accuracy: {test_acc:.4f}")
    print(f"\n{classification_report(test_true, test_preds, target_names=['Down','Up'])}")

    # Save
    torch.save({
        'model_state':  best_state,
        'scaler':       scaler,
        'n_features':   n_feat,
        'seq_len':      SEQ_LEN,
        'feature_cols': FEATURE_COLS,
        'ticker':       ticker
    }, f"models/lstm_{ticker}.pt")
    print(f"  Saved → models/lstm_{ticker}.pt ✓")

    return test_acc

# ── Run ──────────────────────────────────────────────────────
results = {}
for ticker in ["AAPL", "MSFT", "NVDA", "SPY", "QQQ"]:
    results[ticker] = train(ticker)

print(f"\n{'='*50}")
print("Final Test Accuracies:")
for ticker, acc in results.items():
    bar    = '█' * int(acc * 40)
    flag   = '✓' if acc > 0.52 else '✗'
    print(f"  {ticker:5s}  {acc:.4f}  {bar} {flag}")
print('='*50)