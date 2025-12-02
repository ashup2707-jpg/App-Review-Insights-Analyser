# IND Money Review Analyzer

An automated AI-powered system that transforms IND Money app reviews from Google Play Store into actionable weekly product insights. The system uses a 4-layer architecture with LLMs, HDBSCAN clustering, and automated email distribution.

## 🎯 What This Project Does

This system automatically:
1. **Scrapes** Google Play Store reviews (last 8-12 weeks) using `google-play-scraper`
2. **Cleans & Validates** reviews (removes PII, deduplicates, validates schema)
3. **Analyzes** reviews using:
   - Sentiment analysis (LLM-powered)
   - Embedding generation (Sentence Transformers)
   - HDBSCAN clustering
   - LLM-based theme labeling (max 5 themes)
4. **Generates** a scannable weekly pulse note (≤250 words) with:
   - Sentiment metrics (Positive/Neutral/Negative %)
   - Top themes with review counts
   - 3 representative user quotes
   - 3 actionable recommendations
5. **Drafts & Sends** a professional email to stakeholders (Product Managers, CEOs)

**Target Audience:** Product/Growth teams, Support teams, Leadership (CEO/CXO)

---

## 🏗️ Architecture: 4-Layer Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Data Import & Validation                          │
│  ├─ Google Play Scraper (google-play-scraper)             │
│  ├─ Schema Validator                                        │
│  ├─ PII Detector (Presidio)                                │
│  └─ Deduplicator                                            │
│  Output: reviews_clean_YYYYMMDD_HHMMSS.csv                │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Theme Extraction & Classification                 │
│  ├─ Sentiment Analyzer (LLM)                               │
│  ├─ Embedding Generation (Sentence Transformers)           │
│  ├─ HDBSCAN Clustering                                      │
│  ├─ LLM Theme Labeling (LangChain + Gemini)               │
│  └─ Theme Enforcer (max 5 themes)                          │
│  Output: reviews_final_YYYYMMDD_HHMMSS.csv                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Content Generation                                │
│  ├─ Quote Extractor (LLM)                                 │
│  ├─ Action Generator (Chain-of-Thought)                    │
│  └─ Pulse Assembler (≤250 words)                           │
│  Output: weekly_pulse_YYYYMMDD_HHMMSS.md                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: Distribution                                       │
│  ├─ Email Drafter (Professional PM/CEO tone)              │
│  └─ SMTP Email Sender (Gmail/Other)                        │
│  Output: email_draft_YYYYMMDD_HHMMSS.txt + Email Sent      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
INDMoney Review Analyser/
├── main.py                          # Main pipeline orchestrator
├── config.py                        # Configuration (API keys, settings)
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── .gitignore                       # Git ignore rules
│
├── src/                             # Source code (4 layers)
│   ├── layer1_import/               # Layer 1: Data Import & Validation
│   │   ├── gplay_simple_scraper.py # Google Play scraper (primary)
│   │   ├── scraper.py              # Legacy Playwright scraper
│   │   ├── validator.py            # Schema validation
│   │   ├── pii_detector.py         # PII detection & anonymization
│   │   └── deduplicator.py         # Remove duplicate reviews
│   │
│   ├── layer2_themes/              # Layer 2: Theme Extraction
│   │   ├── sentiment.py            # Sentiment analysis (LLM)
│   │   ├── embeddings.py           # Generate embeddings
│   │   ├── clustering.py           # HDBSCAN clustering
│   │   ├── theme_labeler.py        # LLM theme labeling
│   │   └── theme_enforcer.py       # Enforce max 5 themes
│   │
│   ├── layer3_generation/           # Layer 3: Content Generation
│   │   ├── quote_extractor.py      # Extract top quotes (LLM)
│   │   ├── action_generator.py     # Generate action items (LLM)
│   │   └── pulse_assembler.py       # Assemble weekly pulse note
│   │
│   └── layer4_distribution/         # Layer 4: Distribution
│       └── email_drafter.py        # Draft & send email via SMTP
│
├── output/                          # Generated outputs (gitignored)
│   ├── reviews_raw_*.csv           # Raw scraped reviews
│   ├── reviews_clean_*.csv         # Cleaned reviews (Layer 1 output)
│   ├── reviews_final_*.csv         # Reviews with themes (Layer 2 output)
│   ├── weekly_pulse_*.md           # Weekly pulse note (Layer 3 output)
│   ├── email_draft_*.txt           # Email draft (Layer 4 output)
│   └── pipeline.log                 # Execution logs
│
├── utils/                           # Utility modules
│   └── logger.py                    # Logging setup
│
└── tests/                           # Unit tests (if any)
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Google Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))
- Gmail account (for email sending) or any SMTP server

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd "INDMoney Review Analyser"
```

2. **Install dependencies**
```bash
python3 -m pip install -r requirements.txt --user
```

3. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env and add:
# - GOOGLE_API_KEY (Gemini API key)
# - EMAIL_ADDRESS (Gmail sender)
# - EMAIL_PASSWORD (Gmail app password)
# - EMAIL_RECIPIENT (recipient email)
# - ENABLE_EMAIL_SENDING=1
```

### Configuration

Edit `.env` file:

```bash
# Required: Gemini API for LLM features
GOOGLE_API_KEY=your_gemini_api_key_here

# Email Configuration (for automated sending)
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
EMAIL_RECIPIENT=recipient@example.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
ENABLE_EMAIL_SENDING=1
```

Or edit `config.py` to customize:
- `APP_ID`: Target app ID (default: `in.indwealth`)
- `WEEKS_BACK`: Number of weeks to analyze (default: 12)
- `MAX_THEMES`: Maximum themes (default: 5)
- `MAX_QUOTES`: Number of quotes (default: 3)
- `MAX_ACTION_ITEMS`: Number of actions (default: 3)
- `MAX_WORD_COUNT`: Pulse word limit (default: 250)

---

## 📖 Usage

### Run Full Pipeline

```bash
python3 main.py
```

This will:
1. Scrape reviews from Google Play Store (using `google-play-scraper`)
2. Clean, validate, and deduplicate reviews
3. Analyze sentiment, generate embeddings, cluster, and label themes
4. Extract quotes, generate actions, and assemble weekly pulse
5. Draft and send email to configured recipient

**All outputs saved to `output/` directory:**
- `reviews_raw_YYYYMMDD_HHMMSS.csv` - Raw scraped reviews
- `reviews_clean_YYYYMMDD_HHMMSS.csv` - Cleaned reviews
- `reviews_final_YYYYMMDD_HHMMSS.csv` - Reviews with theme labels
- `weekly_pulse_YYYYMMDD_HHMMSS.md` - Weekly pulse note
- `email_draft_YYYYMMDD_HHMMSS.txt` - Email draft
- `pipeline.log` - Execution logs

### Run Individual Layers

**Layer 1: Scrape & Clean**
```bash
python3 -m src.layer1_import.gplay_simple_scraper --count 20 --weeks-back 12
```

**Layer 2-4:** Use `main.py` with breakpoints or run individual modules (see code for details)

---

## 📊 Output Format

### Weekly Pulse Note (`weekly_pulse_*.md`)

```markdown
# IND Money Weekly Review Pulse
**Week of December 02, 2025**

## 📈 Sentiment Overview
- **Positive**: 59 (45%)
- **Neutral**: 19 (14%)
- **Negative**: 51 (39%)

## 📊 Top Themes & Issues
1. **Features & Functionality**: Positive User Experience (12 reviews)
2. **Features & Functionality**: US Stock Charts (10 reviews)
3. **Features & Functionality**: Positive User Feedback (5 reviews)

## 💬 What Users Are Saying
1. "Good app no hidden charges except ₹299 for instant deposit..."
2. "The daily time frame charts in the US market don't seem to show accurate data..."
3. "Love the app. Especially for US investing. Feedback: Please add XIRR..."

## 🎯 Action Items
1. Implement XIRR calculation for stock performance tracking...
2. Investigate and resolve inaccuracies in US stock charts...
3. Evaluate the impact of brokerage fees on user satisfaction...
```

### Email Draft (`email_draft_*.txt`)

Professional email format optimized for Product Managers and CEOs, including:
- Executive summary
- Key metrics (sentiment breakdown)
- Top themes with review counts
- Exact user quotes
- Actionable recommendations

---

## 🔧 Troubleshooting

### API Key Issues

**Problem:** `403 Your API key was reported as leaked` or `400 API key expired`
- **Solution:** Generate a new Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
- **Update:** Replace `GOOGLE_API_KEY` in `.env`

### Email Not Sending

**Problem:** Email draft created but not sent
- **Check:** `ENABLE_EMAIL_SENDING=1` in `.env`
- **Check:** `EMAIL_ADDRESS` and `EMAIL_PASSWORD` are correct
- **Check:** Gmail app password (not regular password) - [Create App Password](https://myaccount.google.com/apppasswords)
- **Check:** `output/pipeline.log` for SMTP errors

### Scraper Issues

**Problem:** No reviews scraped or low quality
- **Solution:** Uses `google-play-scraper` library (more reliable than DOM scraping)
- **Check:** Internet connection and Google Play Store accessibility
- **Note:** Legacy `scraper.py` (Playwright) still available but not recommended

### Clustering Issues

**Problem:** Too many "Miscellaneous" reviews
- **Solution:** Adjust `MIN_CLUSTER_SIZE` and `MIN_SAMPLES` in `config.py`
- **Recommended:** `MIN_CLUSTER_SIZE=5`, `MIN_SAMPLES=3`
- **Note:** With small datasets (<20 reviews), clustering may assign many to "Miscellaneous"

---

## 🛠️ Tech Stack

- **Scraping**: `google-play-scraper` (primary), Playwright (legacy)
- **ML/AI**: Sentence Transformers, HDBSCAN, LangChain, Google Gemini
- **PII Detection**: Presidio
- **Data Processing**: Pandas, NumPy
- **Email**: SMTP (smtplib)
- **Language**: Python 3.9+

---

## 🔐 Privacy & Compliance

- **No PII in outputs**: All usernames, emails, phone numbers automatically removed via Presidio
- **Public data only**: Scrapes only publicly visible reviews (no login required)
- **GDPR compliant**: No personal data storage or processing beyond anonymization

---

## 📚 Key Features Implemented

✅ **Google Play Scraper**: Reliable review scraping using `google-play-scraper`  
✅ **Sentiment Analysis**: LLM-powered sentiment classification  
✅ **Theme Clustering**: HDBSCAN + LLM labeling (max 5 themes)  
✅ **Professional Email**: PM/CEO-focused tone with metrics, quotes, actions  
✅ **Email Automation**: SMTP integration for automatic delivery  
✅ **PII Removal**: Presidio-based anonymization  
✅ **4-Layer Architecture**: Clean separation of concerns  

---

## 🤝 Contributing

This is a personal project for IND Money review analysis. For questions or suggestions, please open an issue.

---

## 📄 License

MIT License - See LICENSE file for details

---

**Built with ❤️ for better product insights**
