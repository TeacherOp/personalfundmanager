import json
import os
from pathlib import Path


class DataService:
    """Service for managing local JSON data files."""

    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / 'data'
        self.data_dir.mkdir(exist_ok=True)
        self._ensure_files_exist()

    def _ensure_files_exist(self):
        """Create default data files if they don't exist."""
        files = {
            'holdings.json': [],
            'buckets.json': [],
            'config.json': {
                'last_sync': None,
                'values_hidden': False,
                'groww_api_key': '',
                'groww_totp_secret': ''
            }
        }

        for filename, default_data in files.items():
            filepath = self.data_dir / filename
            if not filepath.exists():
                self._write_json(filepath, default_data)

    def _read_json(self, filepath):
        """Read JSON file."""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return None

    def _write_json(self, filepath, data):
        """Write JSON file with pretty formatting."""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def get_holdings(self):
        """Get all holdings."""
        return self._read_json(self.data_dir / 'holdings.json') or []

    def save_holdings(self, holdings):
        """Save holdings."""
        self._write_json(self.data_dir / 'holdings.json', holdings)

    def get_buckets(self):
        """Get all buckets."""
        return self._read_json(self.data_dir / 'buckets.json') or []

    def save_buckets(self, buckets):
        """Save buckets."""
        self._write_json(self.data_dir / 'buckets.json', buckets)

    def get_config(self):
        """Get app config."""
        return self._read_json(self.data_dir / 'config.json') or {}

    def save_config(self, config):
        """Save app config."""
        self._write_json(self.data_dir / 'config.json', config)

    def update_config(self, updates):
        """Update specific config values."""
        config = self.get_config()
        config.update(updates)
        self.save_config(config)
