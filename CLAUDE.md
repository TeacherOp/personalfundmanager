# Personal Fund Manager - Development Guide

## Project Overview
AI-powered personal portfolio management system using Groww Trade API for execution.

---

## Groww Trade API - Complete Reference

### Installation
```bash
pip install growwapi
pip install pyotp  # For TOTP authentication
```

**Requirements:** Python 3.9+, Active Groww Trading API subscription

---

### Authentication

**Method 1: API Key + Secret (Requires daily approval)**
```python
from growwapi import GrowwAPI
access_token = GrowwAPI.get_access_token(api_key=api_key, secret=secret)
groww = GrowwAPI(access_token)
```

**Method 2: TOTP (No expiry, recommended)**
```python
import pyotp
totp = pyotp.TOTP(totp_secret).now()
access_token = GrowwAPI.get_access_token(api_key=api_key, totp=totp)
groww = GrowwAPI(access_token)
```

Generate keys at: https://groww.in/trade-api/api-keys

---

### Rate Limits

| Operation Type | Per Second | Per Minute |
|---------------|------------|------------|
| Orders (Create/Modify/Cancel) | 15 | 250 |
| Live Data (Quote, LTP, OHLC) | 10 | 300 |
| Non-Trading (Status, Holdings, Margin) | 20 | 500 |

---

## API Methods Reference

### 1. Instruments (Stock/Symbol Lookup)

```python
# Get all instruments as DataFrame
instruments_df = groww.get_all_instruments()

# Lookup by Groww symbol
instrument = groww.get_instrument_by_groww_symbol("NSE-RELIANCE")

# Lookup by exchange + trading symbol
instrument = groww.get_instrument_by_exchange_and_trading_symbol(
    exchange="NSE",
    trading_symbol="RELIANCE"
)

# Lookup by exchange token
instrument = groww.get_instrument_by_exchange_token("2885")
```

**Instrument CSV columns:** exchange, trading_symbol, instrument_type, exchange_token, etc.

---

### 2. Live Market Data

```python
# Get full quote (price, bid/ask, OHLC, volume, 52-week highs/lows)
quote = groww.get_quote(
    exchange="NSE",
    segment="CASH",
    trading_symbol="RELIANCE"
)

# Get LTP for multiple instruments (max 50)
ltp_data = groww.get_ltp(
    segment="CASH",
    exchange_trading_symbols=[("NSE", "RELIANCE"), ("NSE", "TCS")]
)

# Get OHLC for multiple instruments (max 50)
ohlc_data = groww.get_ohlc(
    segment="CASH",
    exchange_trading_symbols=[("NSE", "RELIANCE"), ("NSE", "TCS")]
)

# Get option chain with Greeks
option_chain = groww.get_option_chain(
    exchange="NSE",
    underlying="NIFTY",
    expiry_date="2024-01-25"
)

# Get Greeks for specific contract
greeks = groww.get_greeks(
    exchange="NSE",
    underlying="NIFTY",
    trading_symbol="NIFTY24JAN22000CE",
    expiry="2024-01-25"
)
```

**Quote Response includes:** LTP, bid/ask depth, OHLC, volume, market_cap, 52_week_high/low, circuit_limits

---

### 3. Historical Data

```python
# Get historical candle data
candles = groww.get_historical_candles(
    trading_symbol="RELIANCE",
    exchange="NSE",
    segment="CASH",
    start_time="2024-01-01 09:15:00",  # or epoch milliseconds
    end_time="2024-01-31 15:30:00",
    interval_in_minutes="1day"
)
```

**Candle Response:** [timestamp, open, high, low, close, volume]

**Data Limits:**

| Interval | Max Request Duration | Historical Access |
|----------|---------------------|-------------------|
| 1 min | 7 days | Last 3 months |
| 5 min | 15 days | Last 3 months |
| 10 min | 30 days | Last 3 months |
| 1 hour | 150 days | Last 3 months |
| 4 hours | 365 days | Last 3 months |
| 1 day | 1080 days (~3 years) | Complete history |
| 1 week | No limit | Complete history |

---

### 4. Orders

```python
# Place order
order = groww.place_order(
    trading_symbol="RELIANCE",
    quantity=10,
    validity="DAY",
    exchange="NSE",
    segment="CASH",
    product="CNC",           # CNC (delivery), MIS (intraday), NRML (F&O)
    order_type="LIMIT",      # LIMIT, MARKET, SL, SL_M
    transaction_type="BUY",  # BUY or SELL
    price=2500.50,           # Required for LIMIT orders
    trigger_price=None       # Required for SL orders
)

# Modify order
groww.modify_order(
    groww_order_id="order_id",
    segment="CASH",
    quantity=15,
    order_type="LIMIT",
    price=2510.00
)

# Cancel order
groww.cancel_order(segment="CASH", groww_order_id="order_id")

# Get order status
status = groww.get_order_status(segment="CASH", groww_order_id="order_id")

# Get all orders for today
orders = groww.get_order_list(segment="CASH", page_number=1, page_size=100)

# Get trade executions for an order
trades = groww.get_trade_list_for_order(
    segment="CASH",
    groww_order_id="order_id"
)
```

**Order Status Values:** NEW, ACKED, TRIGGER_PENDING, APPROVED, REJECTED, FAILED, EXECUTED, CANCELLED, COMPLETED

---

### 5. Smart Orders (GTT & OCO)

```python
# Create GTT (Good Till Triggered)
gtt_order = groww.create_smart_order(
    smart_order_type="GTT",
    reference_id="unique_ref_123",
    segment="CASH",
    trading_symbol="RELIANCE",
    trigger_price="2600.00",
    trigger_direction="UP",  # or "DOWN"
    order={
        "order_type": "LIMIT",
        "price": "2605.00",
        "transaction_type": "SELL",
        "quantity": 10
    }
)

# Create OCO (One Cancels Other) - Target + Stoploss
oco_order = groww.create_smart_order(
    smart_order_type="OCO",
    segment="FNO",  # OCO not supported for CASH currently
    trading_symbol="NIFTY24JANFUT",
    net_position_quantity=50,
    quantity=50,
    target={
        "trigger_price": "22000.00",
        "order_type": "LIMIT",
        "price": "22005.00"
    },
    stop_loss={
        "trigger_price": "21500.00",
        "order_type": "SL_M"
    }
)

# Get/Modify/Cancel smart orders
smart_order = groww.get_smart_order(smart_order_id="id")
groww.modify_smart_order(smart_order_id="id", quantity=20)
groww.cancel_smart_order(smart_order_id="id")
```

**Smart Order Status:** ACTIVE, TRIGGERED, CANCELLED, EXPIRED, FAILED, COMPLETED

---

### 6. Portfolio - Holdings & Positions

```python
# Get holdings (long-term delivery stocks in DEMAT)
holdings = groww.get_holdings_for_user()
```
**Holdings Response:**
- `isin`, `trading_symbol`, `quantity`, `average_price`
- `pledge_quantity`, `t1_quantity`, `demat_free_quantity`

```python
# Get all positions
positions = groww.get_positions_for_user(segment="CASH")  # or "FNO", "COMMODITY"

# Get position for specific symbol
position = groww.get_position_for_trading_symbol(
    trading_symbol="RELIANCE",
    segment="CASH"
)
```
**Positions Response:**
- `trading_symbol`, `segment`, `exchange`, `quantity`, `product`
- `credit_quantity`, `credit_price`, `debit_quantity`, `debit_price`
- `realised_pnl`, `net_price`

---

### 7. Margin

```python
# Get available margin
margin = groww.get_available_margin_details()
```
**Response:** `clear_cash`, `net_margin_used`, `collateral_available`, segment-wise breakdowns

```python
# Calculate margin for order(s)
margin_required = groww.get_order_margin_details(
    segment="CASH",
    orders=[{
        "trading_symbol": "RELIANCE",
        "quantity": 10,
        "exchange": "NSE",
        "segment": "CASH",
        "product": "CNC",
        "order_type": "LIMIT",
        "transaction_type": "BUY",
        "price": 2500.00
    }]
)
```
**Response:** `total_requirement`, `span_required`, `exposure_required`, `brokerage_and_charges`

---

### 8. User Profile

```python
user = groww.get_user_profile()
```
**Response:** `vendor_user_id`, `ucc`, `nse_enabled`, `bse_enabled`, `ddpi_enabled`, `active_segments`

---

### 9. Real-Time WebSocket Feed

```python
from growwapi import GrowwFeed

feed = GrowwFeed(access_token)

# Subscribe to LTP (max 1000 instruments)
def on_ltp_update(data):
    print(data)

feed.subscribe_ltp(
    instruments_list=[("NSE", "RELIANCE"), ("NSE", "TCS")],
    on_data_received=on_ltp_update
)

# Subscribe to market depth
feed.subscribe_market_depth(instruments_list)

# Subscribe to index values
feed.subscribe_index_value(instruments_list)

# Subscribe to order updates
feed.subscribe_equity_order_updates(on_data_received=callback)
feed.subscribe_fno_order_updates(on_data_received=callback)

# Subscribe to position updates
feed.subscribe_fno_position_updates(on_data_received=callback)

# Start consuming (blocking)
feed.consume()

# OR polling mode
feed.subscribe_ltp(instruments_list)
ltp_data = feed.get_ltp()  # Poll current values

# Unsubscribe
feed.unsubscribe_ltp(instruments_list)
```

---

### 10. Backtesting APIs

```python
# Get available expiries for derivatives
expiries = groww.get_expiries(
    exchange="NSE",
    underlying_symbol="NIFTY",
    year=2024,
    month=1
)

# Get contracts for expiry
contracts = groww.get_contracts(
    exchange="NSE",
    underlying_symbol="NIFTY",
    expiry_date="2024-01-25"
)

# Get historical candles (includes OI for F&O)
candles = groww.get_historical_candles(
    exchange="NSE",
    segment="FNO",
    groww_symbol="NIFTY24JANFUT",
    start_time="2024-01-01 09:15:00",
    end_time="2024-01-15 15:30:00",
    candle_interval="5minute"
)
```

---

## Constants Reference

### Exchanges
- `NSE` - National Stock Exchange
- `BSE` - Bombay Stock Exchange
- `MCX` - Multi Commodity Exchange

### Segments
- `CASH` - Regular equity delivery
- `FNO` - Futures & Options
- `COMMODITY` - Commodity derivatives

### Order Types
- `LIMIT` - Exact price, may not fill immediately
- `MARKET` - Best available price, immediate execution
- `SL` - Stop Loss limit order
- `SL_M` - Stop Loss market order

### Product Types
- `CNC` - Cash and Carry (delivery)
- `MIS` - Margin Intraday Square-off
- `NRML` - Regular margin (overnight positions)

### Transaction Types
- `BUY` - Long position
- `SELL` - Short position

### Validity
- `DAY` - Valid until market close

### Candle Intervals
`1minute`, `2minute`, `3minute`, `5minute`, `10minute`, `15minute`, `30minute`, `1hour`, `4hour`, `1day`, `1week`, `1month`

### Instrument Types
- `EQ` - Equity
- `IDX` - Index
- `FUT` - Futures
- `CE` - Call Option
- `PE` - Put Option

---

## Exception Handling

```python
from growwapi.groww.exceptions import (
    GrowwAPIAuthenticationException,
    GrowwAPIAuthorisationException,
    GrowwAPIBadRequestException,
    GrowwAPINotFoundException,
    GrowwAPIRateLimitException,
    GrowwAPITimeoutException,
    GrowwFeedException,
    GrowwFeedConnectionException,
    GrowwFeedNotSubscribedException
)

try:
    order = groww.place_order(...)
except GrowwAPIRateLimitException as e:
    print(f"Rate limited: {e.msg}, code: {e.code}")
    time.sleep(1)
except GrowwAPIBadRequestException as e:
    print(f"Invalid request: {e.msg}")
```

---

## Project Structure

```
personalfundmanager/
├── app.py                    # Flask app entry point
├── requirements.txt          # Python dependencies
├── templates/
│   ├── base.html            # Base template with header, modal, toast
│   └── dashboard.html       # Main dashboard view
├── static/
│   ├── css/style.css        # Dark theme styling
│   └── js/main.js           # Frontend interactions
├── data/
│   ├── holdings.json        # Stock holdings (synced from Groww + bucket assignments)
│   ├── buckets.json         # User-defined buckets
│   └── config.json          # App config (API keys, last sync, etc.)
├── services/
│   ├── __init__.py
│   ├── data_service.py      # JSON file read/write operations
│   └── groww_service.py     # Groww API integration
└── CLAUDE.md                # This file
```

## Running the App

```bash
# Install dependencies
pip install -r requirements.txt

# Add Groww API credentials to data/config.json
# {
#   "groww_api_key": "your-api-key",
#   "groww_totp_secret": "your-totp-secret"
# }

# Run the app
python app.py

# Open http://localhost:5000
```

## Data Models

### Holding (holdings.json)
```json
{
  "isin": "INE002A01018",
  "trading_symbol": "RELIANCE",
  "quantity": 10,
  "average_price": 2450.50,
  "current_price": 2520.00,
  "bucket_id": "bucket_20241220123456",
  "purchased_by": "human"  // "human", "ai", or null (unmarked)
}
```

### Bucket (buckets.json)
```json
{
  "id": "bucket_20241220123456",
  "name": "Tech Growth",
  "philosophy": "Long-term bets on Indian tech",
  "description": "Focus on IT services and product companies",
  "growth_target": 20,
  "created_at": "2024-12-20T12:34:56",
  "last_sync": null
}
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Dashboard view |
| POST | `/api/sync` | Sync holdings from Groww |
| POST | `/api/holding/<isin>/assign` | Assign holding to bucket |
| POST | `/api/bucket` | Create new bucket |
| PUT | `/api/bucket/<id>` | Update bucket |
| DELETE | `/api/bucket/<id>` | Delete bucket |
| POST | `/api/toggle-values` | Toggle value visibility |

---

## Project Architecture Notes

- Keep code files under 300 lines, split into logical modules
- Use `claude-sonnet-4-5-20250929` for any Claude API calls
- Never run tests automatically - user will test manually
- Ask clarifying questions before making assumptions
