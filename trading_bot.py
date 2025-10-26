"""
Binance Futures Testnet - Simplified Trading Bot
Filename: trading_bot.py

Contents:
- BasicBot class: REST-based interaction with Binance Futures Testnet (USDT-M)
- CLI: argparse interface to place MARKET, LIMIT, or TWAP orders (TWAP = bonus)
- Logging: logs requests, responses, and errors to a file (logs/trading_bot.log)

Usage (high level):
1. Create a Binance Futures Testnet account and generate API key/secret.
   - Testnet base URL: https://testnet.binancefuture.com
2. Export your credentials into environment variables (recommended):
   - BINANCE_API_KEY, BINANCE_API_SECRET
3. Run the script:
   python trading_bot.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

For TWAP example:
   python trading_bot.py --symbol BTCUSDT --side SELL --type TWAP --quantity 0.01 --twap_slices 5 --twap_interval 2

Notes:
- This script uses the REST API and signs requests using HMAC SHA256.
- It targets the USDT-M futures endpoints under the testnet base URL above.
- Do NOT use mainnet API keys on testnet or vice versa.

"""

import os
import time
import hmac
import hashlib
import logging
import argparse
import requests
from urllib.parse import urlencode

# Logging setup
LOG_DIR = 'logs'
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'trading_bot.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DEFAULT_TESTNET_BASE = 'https://testnet.binancefuture.com'

class BasicBot:
    def __init__(self, api_key: str, api_secret: str, base_url: str = DEFAULT_TESTNET_BASE):
        """Initialize bot with API credentials and testnet base URL.
        Uses REST signed endpoints for Binance Futures (USDT-M).
        """
        self.api_key = api_key
        self.api_secret = api_secret.encode('utf-8')
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({'X-MBX-APIKEY': self.api_key})
        logger.info('BasicBot initialized with base_url=%s', self.base_url)

    def _sign_payload(self, params: dict) -> str:
        query = urlencode(params)
        signature = hmac.new(self.api_secret, query.encode('utf-8'), hashlib.sha256).hexdigest()
        return query + '&signature=' + signature

    def _send_signed_request(self, method: str, path: str, params: dict):
        params = params or {}
        params['timestamp'] = int(time.time() * 1000)
        signed_query = self._sign_payload(params)
        url = f"{self.base_url}{path}"
        logger.info('REQUEST -> %s %s?%s', method.upper(), url, signed_query)
        try:
            if method.upper() == 'POST':
                response = self.session.post(url + '?' + signed_query, timeout=10)
            elif method.upper() == 'GET':
                response = self.session.get(url + '?' + signed_query, timeout=10)
            else:
                raise ValueError('Unsupported HTTP method: ' + method)
            logger.info('RESPONSE <- %s %s', response.status_code, response.text)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.exception('HTTP error during signed request: %s', e)
            raise

    def place_market_order(self, symbol: str, side: str, quantity: float, reduce_only: bool = False):
        """Place a MARKET order on futures.
        side: 'BUY' or 'SELL'
        symbol: e.g., 'BTCUSDT'
        quantity: in contract size (for USDT-M use quantity in units)
        """
        path = '/fapi/v1/order'
        params = {
            'symbol': symbol.upper(),
            'side': side.upper(),
            'type': 'MARKET',
            'quantity': str(quantity),
            'reduceOnly': str(reduce_only).lower()
        }
        return self._send_signed_request('POST', path, params)

    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float, time_in_force: str = 'GTC', reduce_only: bool = False):
        path = '/fapi/v1/order'
        params = {
            'symbol': symbol.upper(),
            'side': side.upper(),
            'type': 'LIMIT',
            'timeInForce': time_in_force,
            'quantity': str(quantity),
            'price': str(price),
            'reduceOnly': str(reduce_only).lower()
        }
        return self._send_signed_request('POST', path, params)

    def place_stop_limit(self, symbol: str, side: str, quantity: float, stopPrice: float, price: float, time_in_force: str = 'GTC'):
        """Place a STOP order (stopPrice triggers a LIMIT)."
        Note: futures supports types like STOP and STOP_MARKET depending on desired execution.
        """
        path = '/fapi/v1/order'
        params = {
            'symbol': symbol.upper(),
            'side': side.upper(),
            'type': 'STOP',
            'stopPrice': str(stopPrice),
            'price': str(price),
            'timeInForce': time_in_force,
            'quantity': str(quantity)
        }
        return self._send_signed_request('POST', path, params)

    def place_twap(self, symbol: str, side: str, quantity: float, slices: int = 5, interval: float = 1.0):
        """Simple TWAP implementation: split quantity into `slices` equal orders, placed every `interval` seconds.
        This executes MARKET orders each slice to approximate TWAP. Simpler than actual exchange TWAP algos.
        Returns list of responses.
        """
        if slices <= 0:
            raise ValueError('slices must be >= 1')
        slice_qty = float(quantity) / slices
        responses = []
        logger.info('Starting TWAP: %s %s total_qty=%s slices=%d interval=%s', side, symbol, quantity, slices, interval)
        for i in range(slices):
            logger.info('TWAP slice %d/%d: qty=%s', i+1, slices, slice_qty)
            try:
                resp = self.place_market_order(symbol, side, round(slice_qty, 8))
                responses.append(resp)
            except Exception as e:
                logger.exception('Error executing TWAP slice %d: %s', i+1, e)
                responses.append({'error': str(e)})
            if i < slices - 1:
                time.sleep(interval)
        return responses


def parse_args():
    parser = argparse.ArgumentParser(description='Simplified Binance Futures Testnet Trading Bot')
    parser.add_argument('--api-key', type=str, default=os.getenv('BINANCE_API_KEY'), help='Binance API Key (or set BINANCE_API_KEY)')
    parser.add_argument('--api-secret', type=str, default=os.getenv('BINANCE_API_SECRET'), help='Binance API Secret (or set BINANCE_API_SECRET)')
    parser.add_argument('--base-url', type=str, default=os.getenv('BINANCE_TESTNET_BASE', DEFAULT_TESTNET_BASE), help='Testnet base URL')

    parser.add_argument('--symbol', required=True, type=str, help='Trading symbol, e.g. BTCUSDT')
    parser.add_argument('--side', required=True, choices=['BUY', 'SELL', 'buy', 'sell'], help='Order side')
    parser.add_argument('--type', required=True, choices=['MARKET', 'LIMIT', 'TWAP', 'STOP'], help='Order type')
    parser.add_argument('--quantity', required=True, type=float, help='Quantity (contracts/units)')
    parser.add_argument('--price', type=float, help='Price for LIMIT or STOP orders')
    parser.add_argument('--stop-price', type=float, help='Stop price for STOP orders')
    parser.add_argument('--time-in-force', default='GTC', help='Time in force for LIMIT orders (default GTC)')

    # TWAP params
    parser.add_argument('--twap-slices', type=int, default=5, help='Number of slices for TWAP')
    parser.add_argument('--twap-interval', type=float, default=1.0, help='Interval in seconds between TWAP slices')

    return parser.parse_args()


def validate_args(args):
    if not args.api_key or not args.api_secret:
        raise SystemExit('API key and secret are required. Set via --api-key/--api-secret or environment variables.')
    if args.type == 'LIMIT' and args.price is None:
        raise SystemExit('LIMIT orders require --price')
    if args.type == 'STOP' and (args.stop_price is None or args.price is None):
        raise SystemExit('STOP orders require both --stop-price and --price')
    if args.quantity <= 0:
        raise SystemExit('quantity must be positive')


def main():
    args = parse_args()
    try:
        validate_args(args)
    except SystemExit as e:
        logger.error('Argument validation failed: %s', e)
        raise

    bot = BasicBot(args.api_key, args.api_secret, base_url=args.base_url)

    side = args.side.upper()
    try:
        if args.type == 'MARKET':
            resp = bot.place_market_order(args.symbol, side, args.quantity)
            print('Order response:', resp)
        elif args.type == 'LIMIT':
            resp = bot.place_limit_order(args.symbol, side, args.quantity, args.price, time_in_force=args.time_in_force)
            print('Order response:', resp)
        elif args.type == 'STOP':
            resp = bot.place_stop_limit(args.symbol, side, args.quantity, args.stop_price, args.price, time_in_force=args.time_in_force)
            print('Order response:', resp)
        elif args.type == 'TWAP':
            resp = bot.place_twap(args.symbol, side, args.quantity, slices=args.twap_slices, interval=args.twap_interval)
            print('TWAP responses:')
            for r in resp:
                print(r)
        else:
            logger.error('Unsupported order type: %s', args.type)
    except Exception as e:
        logger.exception('Error executing order: %s', e)
        print('Execution failed:', str(e))


if __name__ == '__main__':
    main()
