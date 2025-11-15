# Multilingual News Analysis Platform

A Flask web application that analyzes news content in multiple languages using language detection, abstractive summarization, and sentiment analysis.

## Features

- Language detection with confidence scoring for 10+ languages (en, es, fr, de, it, pt, ar, hi, ur, zh)
- Abstractive text summarization using Hugging Face transformers with multilingual model support
- Sentiment analysis with confidence-based classification (High/Medium/Low)
- Multiple input methods: direct text, URL content extraction, PDF file upload, RSS feed processing
- Responsive web interface with real-time validation and tabbed results display
- Production-ready health endpoint and structured logging

## Architecture

The application uses Flask app factory pattern with a Config class for configuration management. The processing pipeline follows this flow: Input → Text Extraction → Language Detection → Summarization → Sentiment Analysis → Results. The tech stack includes Flask 2.3.3, transformers 4.33.2, langdetect, BeautifulSoup4, pypdf, and feedparser. Model selection follows a hierarchy: Universal → Multilingual → Fallback with automatic GPU detection.

## Directory Structure

```
multilingual-news-platform/
├── app.py                          # Flask application factory and routes
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
├── utils/
│   ├── language_detector.py        # Language detection with langdetect
│   ├── summarizer.py               # Text summarization with transformers
│   ├── sentiment_analyzer.py      # Sentiment analysis with multilingual support
│   ├── text_extractor.py           # URL and PDF text extraction
│   └── rss_processor.py            # RSS feed parsing
├── templates/
│   ├── base.html                   # Base template with Bootstrap
│   ├── index.html                  # Main page with input form
│   └── results.html                # Analysis results display
├── static/
│   ├── js/
│   │   └── main.js                 # Frontend validation and UI logic
│   └── css/
│       └── style.css               # Custom Bootstrap styles
└── uploads/                        # Temporary file uploads (gitignored)
```

## Setup

### Virtual Environment

Linux/macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### Environment Variables

- `SECRET_KEY`: Flask secret key (auto-generated fallback)
- `FLASK_ENV`: Set to "development" or "production"
- `FLASK_DEBUG`: Enable/disable debug mode
- `TRANSFORMERS_CACHE`: Model cache directory (default: ./model_cache)
- `HF_HOME`: Hugging Face cache directory (default: ./model_cache)
- `HF_DATASETS_CACHE`: Dataset cache directory (default: ./model_cache)
- `PORT`: Application port (default: 5000)

### Model Cache Pre-warming

Pre-download models to avoid delay on first request:
```bash
python -c "from utils.summarizer import TextSummarizer; from utils.sentiment_analyzer import SentimentAnalyzer"
```

## Running

Development:
```bash
export FLASK_APP=app.py
flask run
```

Production:
```bash
gunicorn -w 2 -k gthread -b 0.0.0.0:$PORT app:app
```

Health check: GET `/health` returns JSON with timestamp and environment.

## Usage

### Web Interface

Choose an input method and provide content:

- Text: Direct text input (50-50,000 chars, truncates with warning)
- URL: Fetches and cleans HTML content, falls back to paragraph extraction
- File: Upload .txt or .pdf files (max 16MB, PDF via pypdf)
- RSS: Parse RSS feeds, select specific article by index or get article list

Results display in tabbed interface showing language detection, summary, sentiment, statistics, and original text.

### API Examples

Text analysis:
```bash
curl -X POST -F "input_method=text" \
     -F "direct_text=Your news article content here..." \
     http://localhost:5000/analyze
```

URL analysis:
```bash
curl -X POST -F "input_method=url" \
     -F "url=https://example.com/news/article" \
     http://localhost:5000/analyze
```

File analysis:
```bash
curl -X POST -F "input_method=file" \
     -F "file=@document.pdf" \
     http://localhost:5000/analyze
```

RSS analysis:
```bash
curl -X POST -F "input_method=rss" \
     -F "rss_url=https://techcrunch.com/feed/" \
     http://localhost:5000/analyze
```

For specific RSS article selection, add `-F "article_index=2"`.

## Configuration

File uploads limited to 16MB max size, .txt/.pdf extensions only. Text validation requires 50 character minimum and 50,000 character maximum with automatic truncation. Model selection follows language-based hierarchy: Universal → Multilingual → Fallback. GPU detection is automatic with CPU fallback. Cache directories configurable via TRANSFORMERS_CACHE, HF_HOME, HF_DATASETS_CACHE. Temporary uploads stored in ./uploads directory.

## Deployment

Use `/health` endpoint for readiness/liveness probes in containerized deployments. Set cache environment variables to writable volume paths and persist model cache to avoid repeated downloads. Transformers models require significant memory and CPU resources. Start with 2 gunicorn workers using gthread mode for optimal performance. Production logging configured at INFO level with structured output.

## Troubleshooting

Model download delays typically result from cache environment variables or network connectivity issues. Out of memory errors can be resolved by forcing CPU mode, reducing workers, or using default summary lengths. Extraction failures often stem from URL accessibility, PDF format compatibility, or robots.txt restrictions. 413 RequestEntityTooLarge errors require adjusting MAX_CONTENT_LENGTH in config.py. Slow first requests are normal as models download on initial use.

## Security

Set a strong SECRET_KEY environment variable in production. Server-side validation enforces file types and sizes. Upload files are temporary and not persisted. Use reverse proxy like nginx for HTTPS termination in production deployments.