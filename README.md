# 📈 Virtual Stock Trader

A command-line stock trading simulator written in Python. Buy and sell stocks with live market prices, track your portfolio, and monitor your net worth over time.

## Features

- 💵 Starts with **$100,000** in virtual cash
- 📊 Live stock price retrieval using Yahoo Finance (`yfinance`)
- 🛒 Buy and sell stocks (supports fractional shares)
- 📂 Persistent save file (`save.txt`)
- 📈 Portfolio value and net worth tracking
- 📜 Transaction history
- 📉 Gain/loss calculation for each holding
- 🔄 Refresh prices at any time

## Installation

Clone the repository:

```bash
git clone https://github.com/<your-username>/StockTradingSim.git
cd StockTrader
```

Create a virtual environment (recommended):

```bash
python -m venv .venv
```

Activate it:

### Windows

```bash
.venv\Scripts\activate
```

### macOS/Linux

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install yfinance
```

## Running

```bash
python main.py
```

## Commands

| Command | Description |
|---------|-------------|
| `buy <SYMBOL> <SHARES>` | Purchase shares of a stock |
| `sell <SYMBOL> <SHARES>` | Sell shares of a stock |
| `check [SYMBOL]` | Check the current price of a stock |
| `portfolio` | View your holdings and gain/loss |
| `refresh` | Refresh prices for all owned stocks |
| `history` | View net worth history |
| `help` | Show available commands |
| `quit` | Save and exit |

### Example

```text
> buy AAPL 5
Bought 5 share(s) of AAPL at $182.30 each.

> check AAPL
AAPL: $183.02 per share.

> portfolio
Portfolio:
  AAPL: 5.000000 share(s) @ $183.02 each = $915.10
Cash available: $99,088.50
Portfolio value: $915.10
Net worth: $100,003.60
```

## Project Structure

```
StockTrader/
│
├── main.py          # Main application
├── save.txt         # Saved portfolio and transaction data
├── README.md
└── .venv/           # Virtual environment (not included in Git)
```

## Data Stored

The simulator automatically saves:

- Available cash
- Portfolio holdings
- Average purchase price
- Cached stock prices
- Price history
- Transaction history
- Net worth history

No progress is lost between sessions.

## Technologies

- Python 3
- yfinance
- JSON

## Future Improvements

- [ ] Portfolio performance graphs
- [ ] Historical stock charts
- [ ] Watchlist
- [ ] Limit and stop orders
- [ ] Dividends
- [ ] Stock splits
- [ ] Multiple portfolios
- [ ] Market news integration
- [ ] Performance statistics
- [ ] GUI version

## Disclaimer

This project is for educational purposes only. It does **not** execute real trades or provide financial advice.
