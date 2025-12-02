# App-Review-Insights-Analyser

An automated AI-powered system that transforms IND Money app reviews into actionable weekly insights using a 4-layer architecture with LLMs, HDBSCAN clustering, and automated reporting.

## 🎯 Overview

This system automatically:
1. **Scrapes** Google Play Store reviews (last 8-12 weeks)
2. **Analyzes** reviews using HDBSCAN clustering + LLM theme labeling
3. **Generates** a scannable weekly pulse note (≤250 words) with:
   - Top 3 themes
   - 3 representative user quotes
   - 3 actionable recommendations
4. **Drafts** an email ready to send to stakeholders

**Target Users:** Product/Growth teams, Support teams, Leadership

## 🏗️ Architecture

### 4-Layer Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Data Import & Validation                          │
│  ├─ Playwright Scraper (Google Play Store)                 │
│  ├─ Schema Validator                                        │
│  ├─ PII Detector (Presidio)                                │
│  └─ Deduplicator                                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Theme Extraction & Classification                 │
│  ├─ Embedding Generation (Sentence Transformers)           │
│  ├─ HDBSCAN Clustering                                      │
│  ├─ LLM Theme Labeling (LangChain + Gemini)               │
│  └─ Theme Enforcer (max 5 themes)                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Content Generation                                │
│  ├─ Quote Extraction (LLM)                                 │
│  ├─ Action Generator (Chain-of-Thought)                    │
│  └─ Pulse Assembler (≤250 words)                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: Distribution                                       │
│  ├─ Email Drafter                                           │
│  └─ PII Final Check                                         │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Setup

### Prerequisites

- Python 3.9+
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Installation

1. **Clone the repository**
```bash
cd "/Users/sneha/Desktop/INDMoney Review Analyser"
```

2. **Install dependencies**
```bash
python3 -m pip install -r requirements.txt --user
```

3. **Install Playwright browsers**
```bash
python3 -m playwright install chromium
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### Configuration

Edit `config.py` to customize:
- `APP_ID`: Target app ID (default: `in.indwealth`)
- `WEEKS_BACK`: Number of weeks to analyze (default: 12)
- `MAX_THEMES`: Maximum themes (default: 5)
- `MAX_QUOTES`: Number of quotes (default: 3)
- `MAX_ACTION_ITEMS`: Number of actions (default: 3)
- `MAX_WORD_COUNT`: Pulse word limit (default: 250)

## 📖 Usage

### Run Full Pipeline

```bash
python3 main.py
```

This will:
1. Scrape reviews from Google Play Store
2. Process and analyze them
3. Generate weekly pulse note
4. Create email draft

All outputs saved to `output/` directory.

### Run Individual Layers

**Layer 1: Scrape & Clean**
```bash
cd src/layer1_import
python3 scraper.py
python3 validator.py reviews_raw.csv reviews_validated.csv
python3 pii_detector.py reviews_validated.csv reviews_anonymized.csv
python3 deduplicator.py reviews_anonymized.csv reviews_clean.csv
```

**Layer 2: Theme Extraction**
```bash
cd src/layer2_themes
python3 embeddings.py reviews_clean.csv embeddings.pkl
python3 clustering.py embeddings.pkl reviews_clean.csv reviews_clustered.csv
python3 theme_labeler.py reviews_clustered.csv reviews_themed.csv
python3 theme_enforcer.py reviews_themed.csv reviews_final.csv
```

**Layer 3: Content Generation**
```bash
cd src/layer3_generation
python3 quote_extractor.py reviews_final.csv quotes.json 3
python3 action_generator.py reviews_final.csv quotes.json actions.json 3
python3 pulse_assembler.py reviews_final.csv quotes.json actions.json weekly_pulse.md
```

**Layer 4: Email Draft**
```bash
cd src/layer4_distribution
python3 email_drafter.py weekly_pulse.md email_draft.txt
```

## 📊 Theme Legend

The system categorizes reviews into up to 5 themes:

| Theme | Description | Example Issues |
|-------|-------------|----------------|
| **Features & Functionality** | Core app features, UI/UX, navigation | Missing features, confusing UI, broken functionality |
| **App Updates & Performance** | App stability, speed, crashes | Slow loading, frequent crashes, bugs after updates |
| **Transactions & Payments** | Payment processing, transaction issues | Failed payments, incorrect amounts, refund delays |
| **Customer Service & Support** | Support quality, response time | Slow responses, unhelpful support, unresolved issues |
| **Product Marketing & Communication** | Notifications, promotions, messaging | Spam notifications, misleading ads, poor communication |

## 📁 Output Files

After running the pipeline, check `output/` for:

- `reviews_clean_YYYYMMDD_HHMMSS.csv` - Cleaned review data
- `reviews_final_YYYYMMDD_HHMMSS.csv` - Reviews with theme labels
- `weekly_pulse_YYYYMMDD_HHMMSS.md` - Weekly pulse note
- `email_draft_YYYYMMDD_HHMMSS.txt` - Email draft
- `pipeline.log` - Execution logs

## 🔧 Troubleshooting

### Scraper Issues

**Problem:** Playwright fails to load reviews
- **Solution:** Check internet connection, try increasing `max_scrolls` parameter
- **Alternative:** Google may have changed their page structure. Update selectors in `scraper.py`

### API Rate Limits

**Problem:** Gemini API rate limit errors
- **Solution:** Add delays between API calls or use a paid API tier
- **Workaround:** Process reviews in smaller batches

### Clustering Issues

**Problem:** Too many or too few clusters
- **Solution:** Adjust `MIN_CLUSTER_SIZE` and `MIN_SAMPLES` in `config.py`
- **Recommended:** `MIN_CLUSTER_SIZE=5`, `MIN_SAMPLES=3`

### PII Detection

**Problem:** Presidio not detecting PII
- **Solution:** Ensure `presidio-analyzer` and `presidio-anonymizer` are installed
- **Note:** Download required NLP models: `python3 -m spacy download en_core_web_lg`

## 🧪 Testing

Run tests for individual layers:

```bash
# Layer 1 tests
pytest tests/test_layer1.py -v

# Layer 2 tests
pytest tests/test_layer2.py -v

# Layer 3 tests
pytest tests/test_layer3.py -v

# Layer 4 tests
pytest tests/test_layer4.py -v

# All tests
pytest tests/ -v
```

## 📝 Example Output

### Weekly Pulse Note

```markdown
# IND Money Weekly Review Pulse
**Week of December 02, 2024**

## 📊 Top 3 Themes

1. **App Updates & Performance** (45 reviews)
2. **Transactions & Payments** (32 reviews)
3. **Customer Service & Support** (28 reviews)

## 💬 What Users Are Saying

1. "App crashes frequently after the latest update. Very frustrating!"
2. "Payment failed but money was deducted. Support not responding."
3. "Great features but UI is confusing for new users."

## 🎯 Action Items

1. Prioritize stability fixes for the latest app version
2. Improve payment failure handling and refund process
3. Enhance customer support response time for payment issues
```

## 🔐 Privacy & Compliance

- **No PII in outputs**: All usernames, emails, phone numbers automatically removed
- **Public data only**: Scrapes only publicly visible reviews (no login required)
- **GDPR compliant**: No personal data storage or processing

## 🛠️ Tech Stack

- **Scraping**: Playwright, BeautifulSoup4
- **ML/AI**: Sentence Transformers, HDBSCAN, LangChain, Google Gemini
- **PII Detection**: Presidio
- **Data Processing**: Pandas, NumPy
- **Language**: Python 3.9+

## 📚 References

- [HDBSCAN Clustering](https://hdbscan.readthedocs.io/)
- [Sentence Transformers](https://www.sbert.net/)
- [LangChain](https://python.langchain.com/)
- [Presidio](https://microsoft.github.io/presidio/)

## 🤝 Contributing

This is a personal project for IND Money review analysis. For questions or suggestions, please open an issue.

## 📄 License

MIT License - See LICENSE file for details

---

**Built with ❤️ for better product insights** 
