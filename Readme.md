# Personal Fund Manager

A DIY "mutual fund" experiment - building a personal portfolio manager powered by AI agents.

## Disclaimer

This is a personal experiment, not financial advice. Stock market investments are subject to market risks. The AI suggestions (when implemented) are for educational purposes - always do your own research before making investment decisions.

## The Idea

Mutual funds are essentially buckets of stocks with different weightages, managed by a fund manager. What if you could build your own "fund" - managed and suggested by AI agents, using your own investment philosophy?

This project connects to the Groww Trade API to:
- Sync your real stock holdings
- Organize them into "buckets" (like mini-funds) based on investment themes
- Track performance against targets
- Eventually: Let AI agents analyze and suggest portfolio changes

**Goal:** Beat FD returns by 50% over 6 months.

## Current Status

### Done
- [x] Flask app with dark-themed dashboard
- [x] Groww API integration (sync real holdings)
- [x] Portfolio overview with total value, invested amount, P&L
- [x] Bucket system (create, edit, delete themed portfolios)
- [x] Assign holdings to buckets with "Human" or "AI" purchase tags
- [x] Hide/Show values toggle (for screenshots)
- [x] Holdings table with individual stock P&L
- [x] Filter holdings by bucket
- [x] Local JSON storage (no external DB needed)

### Coming Next
- [ ] AI agent for daily portfolio analysis
- [ ] News/sentiment analysis for held stocks
- [ ] Bucket rebalancing suggestions
- [ ] Historical performance tracking
- [ ] Charts and visualizations
- [ ] AI-powered buy/sell recommendations
- [ ] Automated order execution (with approval)

## Tech Stack

- **Backend:** Python, Flask
- **Frontend:** Jinja2 templates, vanilla JS
- **API:** Groww Trade API
- **Storage:** Local JSON files
- **AI:** Claude API (coming soon)

## Setup

```bash
# Clone the repo
git clone https://github.com/yourusername/personalfundmanager.git
cd personalfundmanager

# Create virtual environment
python -m venv growenv
source growenv/bin/activate  # On Windows: growenv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.template .env
# Edit .env with your Groww API credentials

# Run the app
python app.py
# Open http://localhost:5000
```

## Environment Variables

```
GROWW_API_KEY=your-api-key
GROWW_API_SECRET=your-api-secret
```

Get your API credentials from: https://groww.in/trade-api/api-keys

**Note:** API Key + Secret method requires daily approval on the Groww dashboard.

## Project Structure

```
personalfundmanager/
├── app.py                 # Flask routes & logic
├── requirements.txt       # Python dependencies
├── templates/
│   ├── base.html          # Base template
│   └── dashboard.html     # Main dashboard
├── static/
│   ├── css/style.css      # Dark theme styling
│   └── js/main.js         # Frontend interactions
├── data/                  # Local JSON storage (gitignored)
│   ├── holdings.json      # Synced holdings + bucket assignments
│   ├── buckets.json       # User-defined buckets
│   └── config.json        # App configuration
├── services/
│   ├── data_service.py    # JSON file operations
│   └── groww_service.py   # Groww API wrapper
└── CLAUDE.md              # AI assistant context
```

## License

YOLO
