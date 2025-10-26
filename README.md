# Binance Futures Trading Bot (Testnet)

A **simplified Python trading bot** for Binance Futures Testnet (USDT-M) that supports **MARKET, LIMIT, STOP, and TWAP orders**. Built with a command-line interface, robust logging, error handling, **mock mode**, and unit tests.

---

## Features

* Place MARKET, LIMIT, STOP, and TWAP orders on Binance Futures Testnet.
* CLI for easy input and order management.
* Logs API requests, responses, and errors in `logs/` folder.
* Mock mode to simulate trades for testing without real funds.
* Unit tests for MARKET, LIMIT, and TWAP flows.

## Tech Stack

* Python 3.x
* requests
* argparse
* pytest
* Binance Futures Testnet API

## Installation

1. Clone the repository:

```bash
git clone <your-repo-url>
cd binance-futures-trading-bot
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. (Optional) Set up a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

## Setup Binance Testnet API Keys

1. Register and activate a Binance Futures Testnet account.
2. Generate API key and secret.
3. Export credentials as environment variables:

```bash
export BINANCE_API_KEY='your_key'
export BINANCE_API_SECRET='your_secret'
```

## Usage Examples

### Market Order

```bash
python trading_bot.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### Limit Order

```bash
python trading_bot.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 1500.0
```

### Stop Order

```bash
python trading_bot.py --symbol BTCUSDT --side BUY --type STOP --quantity 0.001 --price 30000 --stop-price 29950
```

### TWAP Order (Bonus)

```bash
python trading_bot.py --symbol BTCUSDT --side SELL --type TWAP --quantity 0.003 --twap-slices 3 --twap-interval 1
```

## Mock Mode

For testing and generating logs without hitting the Testnet:

```python
bot = BasicBotMock(mock=True)
```

## Running Unit Tests

1. Install pytest:

```bash
pip install pytest
```

2. Run tests:

```bash
pytest -q
```

Or run directly without pytest:

```bash
python tests/test_trading_bot.py
```

## Logs

All API requests and responses are logged in `logs/trading_bot.log`. Mock mode logs are also saved for verification.

## Folder Structure

```
binance-futures-trading-bot/
├── trading_bot.py
├── tests/
│   └── test_trading_bot.py
├── logs/
│   └── sample_trading_bot.log
├── requirements.txt
└── README.md
```
