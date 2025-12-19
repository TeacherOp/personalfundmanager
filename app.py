from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
import json
import os

from services.groww_service import GrowwService
from services.data_service import DataService

app = Flask(__name__)

data_service = DataService()
groww_service = GrowwService()


@app.route('/')
def dashboard():
    """Main dashboard view."""
    holdings = data_service.get_holdings()
    buckets = data_service.get_buckets()
    config = data_service.get_config()

    # Calculate portfolio totals
    portfolio_stats = calculate_portfolio_stats(holdings, buckets)

    return render_template(
        'dashboard.html',
        holdings=holdings,
        buckets=buckets,
        stats=portfolio_stats,
        last_sync=config.get('last_sync'),
        values_hidden=config.get('values_hidden', False)
    )


@app.route('/api/sync', methods=['POST'])
def sync_holdings():
    """Sync holdings from Groww API."""
    try:
        groww_holdings = groww_service.fetch_holdings()

        if groww_holdings is None:
            return jsonify({'success': False, 'error': 'Failed to fetch from Groww'})

        current_holdings = data_service.get_holdings()
        updated_holdings = merge_holdings(current_holdings, groww_holdings)

        data_service.save_holdings(updated_holdings)
        data_service.update_config({'last_sync': datetime.now().isoformat()})

        return jsonify({'success': True, 'message': 'Sync completed'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/holding/<isin>/assign', methods=['POST'])
def assign_holding_to_bucket(isin):
    """Assign a holding to a bucket."""
    data = request.json
    bucket_id = data.get('bucket_id')

    holdings = data_service.get_holdings()

    for holding in holdings:
        if holding['isin'] == isin:
            holding['bucket_id'] = bucket_id
            holding['purchased_by'] = data.get('purchased_by', 'human')
            break

    data_service.save_holdings(holdings)
    return jsonify({'success': True})


@app.route('/api/bucket', methods=['POST'])
def create_bucket():
    """Create a new bucket."""
    data = request.json
    buckets = data_service.get_buckets()

    new_bucket = {
        'id': f"bucket_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        'name': data.get('name', 'Unnamed Bucket'),
        'philosophy': data.get('philosophy', ''),
        'description': data.get('description', ''),
        'growth_target': data.get('growth_target', 0),
        'created_at': datetime.now().isoformat(),
        'last_sync': None
    }

    buckets.append(new_bucket)
    data_service.save_buckets(buckets)

    return jsonify({'success': True, 'bucket': new_bucket})


@app.route('/api/bucket/<bucket_id>', methods=['PUT'])
def update_bucket(bucket_id):
    """Update a bucket."""
    data = request.json
    buckets = data_service.get_buckets()

    for bucket in buckets:
        if bucket['id'] == bucket_id:
            bucket['name'] = data.get('name', bucket['name'])
            bucket['philosophy'] = data.get('philosophy', bucket['philosophy'])
            bucket['description'] = data.get('description', bucket['description'])
            bucket['growth_target'] = data.get('growth_target', bucket['growth_target'])
            break

    data_service.save_buckets(buckets)
    return jsonify({'success': True})


@app.route('/api/bucket/<bucket_id>', methods=['DELETE'])
def delete_bucket(bucket_id):
    """Delete a bucket and unassign its holdings."""
    buckets = data_service.get_buckets()
    buckets = [b for b in buckets if b['id'] != bucket_id]
    data_service.save_buckets(buckets)

    # Unassign holdings from deleted bucket
    holdings = data_service.get_holdings()
    for holding in holdings:
        if holding.get('bucket_id') == bucket_id:
            holding['bucket_id'] = None
    data_service.save_holdings(holdings)

    return jsonify({'success': True})


@app.route('/api/toggle-values', methods=['POST'])
def toggle_values():
    """Toggle visibility of portfolio values."""
    config = data_service.get_config()
    config['values_hidden'] = not config.get('values_hidden', False)
    data_service.save_config(config)
    return jsonify({'success': True, 'hidden': config['values_hidden']})


def calculate_portfolio_stats(holdings, buckets):
    """Calculate portfolio and bucket statistics."""
    total_invested = 0
    total_current = 0
    bucket_stats = {}

    # Initialize bucket stats
    for bucket in buckets:
        bucket_stats[bucket['id']] = {
            'name': bucket['name'],
            'invested': 0,
            'current': 0,
            'growth_target': bucket.get('growth_target', 0),
            'holdings_count': 0
        }

    # Add unassigned bucket
    bucket_stats['unassigned'] = {
        'name': 'Unassigned',
        'invested': 0,
        'current': 0,
        'growth_target': 0,
        'holdings_count': 0
    }

    for holding in holdings:
        invested = holding.get('quantity', 0) * holding.get('average_price', 0)
        current = holding.get('quantity', 0) * holding.get('current_price', holding.get('average_price', 0))

        total_invested += invested
        total_current += current

        bucket_id = holding.get('bucket_id') or 'unassigned'
        if bucket_id in bucket_stats:
            bucket_stats[bucket_id]['invested'] += invested
            bucket_stats[bucket_id]['current'] += current
            bucket_stats[bucket_id]['holdings_count'] += 1

    # Calculate growth percentages
    for bucket_id, stats in bucket_stats.items():
        if stats['invested'] > 0:
            stats['growth'] = ((stats['current'] - stats['invested']) / stats['invested']) * 100
        else:
            stats['growth'] = 0

    total_growth = ((total_current - total_invested) / total_invested * 100) if total_invested > 0 else 0

    return {
        'total_invested': total_invested,
        'total_current': total_current,
        'total_growth': total_growth,
        'buckets': bucket_stats
    }


def merge_holdings(current_holdings, groww_holdings):
    """Merge Groww holdings with local data, preserving bucket assignments."""
    current_by_isin = {h['isin']: h for h in current_holdings}

    merged = []
    for gh in groww_holdings:
        isin = gh['isin']
        if isin in current_by_isin:
            # Update existing holding, keep bucket assignment
            existing = current_by_isin[isin]
            existing.update({
                'quantity': gh['quantity'],
                'average_price': gh['average_price'],
                'trading_symbol': gh['trading_symbol'],
                'current_price': gh.get('current_price', existing.get('current_price', gh['average_price']))
            })
            merged.append(existing)
        else:
            # New holding - mark as unmarked
            gh['bucket_id'] = None
            gh['purchased_by'] = None  # Unmarked - user will assign
            merged.append(gh)

    return merged


if __name__ == '__main__':
    app.run(debug=True, port=5000)
