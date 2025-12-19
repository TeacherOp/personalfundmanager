"""
Groww API service for fetching holdings and market data.

Note: Requires growwapi package: pip install growwapi pyotp
"""

from pathlib import Path
import json
import os
from dotenv import load_dotenv

load_dotenv()


class GrowwService:
    """Service for interacting with Groww Trade API."""

    def __init__(self):
        self.config = self._load_config()
        self.api = None

    def _load_config(self):
        """Load Groww API config from env vars (priority) or config.json."""
        config = {}

        # Try loading from config.json first
        config_path = Path(__file__).parent.parent / 'data' / 'config.json'
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        # Environment variables override config.json
        if os.getenv('GROWW_API_KEY'):
            config['groww_api_key'] = os.getenv('GROWW_API_KEY')
        if os.getenv('GROWW_API_SECRET'):
            config['groww_api_secret'] = os.getenv('GROWW_API_SECRET')
        if os.getenv('GROWW_TOTP_SECRET'):
            config['groww_totp_secret'] = os.getenv('GROWW_TOTP_SECRET')

        return config

    def _get_access_token(self):
        """Get Groww API access token using API Secret or TOTP."""
        api_key = self.config.get('groww_api_key')
        api_secret = self.config.get('groww_api_secret')
        totp_secret = self.config.get('groww_totp_secret')

        if not api_key:
            print("GROWW_API_KEY not set")
            return None

        try:
            from growwapi import GrowwAPI

            # Method 1: API Key + Secret (requires daily approval on Groww dashboard)
            if api_secret:
                print("Authenticating with API Key + Secret...")
                access_token = GrowwAPI.get_access_token(api_key=api_key, secret=api_secret)
                return access_token

            # Method 2: TOTP (no daily approval needed)
            if totp_secret:
                import pyotp
                print("Authenticating with TOTP...")
                totp = pyotp.TOTP(totp_secret).now()
                access_token = GrowwAPI.get_access_token(api_key=api_key, totp=totp)
                return access_token

            print("Neither GROWW_API_SECRET nor GROWW_TOTP_SECRET is set")
            return None

        except ImportError as e:
            print(f"Missing package: {e}. Run: pip install growwapi pyotp")
            return None
        except Exception as e:
            print(f"Failed to get access token: {e}")
            return None

    def _init_api(self):
        """Initialize Groww API client."""
        if self.api is not None:
            return True

        access_token = self._get_access_token()
        if not access_token:
            return False

        try:
            from growwapi import GrowwAPI
            self.api = GrowwAPI(access_token)
            return True
        except Exception as e:
            print(f"Failed to initialize API: {e}")
            return False

    def fetch_holdings(self):
        """Fetch holdings from Groww API."""
        if not self._init_api():
            # Return mock data for testing without API
            return self._get_mock_holdings()

        try:
            response = self.api.get_holdings_for_user()

            # Response format: {"holdings": [...]}
            raw_holdings = response.get('holdings', []) if isinstance(response, dict) else response
            holdings = []

            for h in raw_holdings:
                holdings.append({
                    'isin': h.get('isin'),
                    'trading_symbol': h.get('trading_symbol'),
                    'quantity': h.get('quantity', 0),
                    'average_price': h.get('average_price', 0),
                    't1_quantity': h.get('t1_quantity', 0),
                    'pledge_quantity': h.get('pledge_quantity', 0)
                })

            # Fetch current prices
            holdings = self._enrich_with_prices(holdings)
            return holdings

        except Exception as e:
            print(f"Failed to fetch holdings: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _enrich_with_prices(self, holdings):
        """Add current prices to holdings."""
        if not self.api or not holdings:
            return holdings

        try:
            symbols = [(h['trading_symbol'].split('-')[0] if '-' in h['trading_symbol']
                       else 'NSE', h['trading_symbol']) for h in holdings]

            # Batch fetch LTP (max 50 at a time)
            for i in range(0, len(symbols), 50):
                batch = symbols[i:i+50]
                ltp_data = self.api.get_ltp(segment="CASH", exchange_trading_symbols=batch)

                for holding in holdings[i:i+50]:
                    key = f"NSE_{holding['trading_symbol']}"
                    if key in ltp_data:
                        holding['current_price'] = ltp_data[key]

        except Exception as e:
            print(f"Failed to fetch prices: {e}")

        return holdings

    def _get_mock_holdings(self):
        """Return mock holdings for testing without API."""
        return [
            {
                'isin': 'INE002A01018',
                'trading_symbol': 'RELIANCE',
                'quantity': 10,
                'average_price': 2450.50,
                'current_price': 2520.00,
                't1_quantity': 0,
                'pledge_quantity': 0
            },
            {
                'isin': 'INE467B01029',
                'trading_symbol': 'TATAELXSI',
                'quantity': 5,
                'average_price': 6800.00,
                'current_price': 7150.00,
                't1_quantity': 0,
                'pledge_quantity': 0
            },
            {
                'isin': 'INE009A01021',
                'trading_symbol': 'INFY',
                'quantity': 20,
                'average_price': 1520.00,
                'current_price': 1485.00,
                't1_quantity': 0,
                'pledge_quantity': 0
            },
            {
                'isin': 'INE040A01034',
                'trading_symbol': 'HDFCBANK',
                'quantity': 15,
                'average_price': 1650.00,
                'current_price': 1720.00,
                't1_quantity': 0,
                'pledge_quantity': 0
            }
        ]

    def fetch_ltp(self, symbols):
        """Fetch current LTP for given symbols."""
        if not self._init_api():
            return {}

        try:
            exchange_symbols = [('NSE', s) for s in symbols]
            return self.api.get_ltp(segment="CASH", exchange_trading_symbols=exchange_symbols)
        except Exception as e:
            print(f"Failed to fetch LTP: {e}")
            return {}
