from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
import os
import tempfile
import uuid
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import logging
from datetime import datetime
import json

from utils.rss_processor import RSSProcessor
from utils.text_extractor import TextExtractor
from utils.language_detector import LanguageDetector
from utils.summarizer import TextSummarizer
from utils.sentiment_analyzer import SentimentAnalyzer
from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize NLP components
rss_processor = RSSProcessor()
text_extractor = TextExtractor()
language_detector = LanguageDetector()
summarizer = TextSummarizer()
sentiment_analyzer = SentimentAnalyzer()

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_text():
    """Main analysis endpoint"""
    try:
        # Get input method and text
        input_method = request.form.get('input_method', 'text')
        text = ""
        error_message = None
        source_info = {}
        
        # Process based on input method
        if input_method == 'text':
            text = request.form.get('direct_text', '').strip()
            if not text:
                error_message = "Please enter some text to analyze."
            source_info = {'type': 'direct_text', 'source': 'User Input'}
                
        elif input_method == 'url':
            url = request.form.get('url', '').strip()
            if not url:
                error_message = "Please enter a valid URL."
            else:
                try:
                    text = text_extractor.extract_from_url(url)
                    if not text:
                        error_message = "Could not extract text from the provided URL."
                    else:
                        source_info = {'type': 'url', 'source': url}
                except Exception as e:
                    error_message = f"Error extracting text from URL: {str(e)}"
                    
        elif input_method == 'file':
            if 'file' not in request.files:
                error_message = "No file was uploaded."
            else:
                file = request.files['file']
                if file.filename == '':
                    error_message = "No file was selected."
                elif not allowed_file(file.filename):
                    error_message = "File type not supported. Please upload .txt or .pdf files only."
                else:
                    try:
                        # Save file temporarily
                        filename = secure_filename(file.filename)
                        unique_filename = f"{uuid.uuid4()}_{filename}"
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                        file.save(file_path)
                        
                        # Check file size
                        if os.path.getsize(file_path) > app.config['MAX_CONTENT_LENGTH']:
                            os.remove(file_path)
                            error_message = "File size too large. Maximum 16MB allowed."
                        else:
                            # Extract text based on file type
                            if filename.lower().endswith('.pdf'):
                                text = text_extractor.extract_from_pdf(file_path)
                            else:  # .txt file
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    text = f.read()
                            
                            # Clean up temporary file
                            os.remove(file_path)
                            
                            if not text:
                                error_message = "Could not extract text from the uploaded file."
                            else:
                                source_info = {'type': 'file', 'source': filename}
                                
                    except Exception as e:
                        error_message = f"Error processing file: {str(e)}"

        elif input_method == 'rss':
            rss_url = request.form.get('rss_url', '').strip()
            article_index = request.form.get('article_index')
            
            if not rss_url:
                error_message = "Please enter a valid RSS feed URL."
            else:
                try:
                    # Get RSS feed articles
                    articles = rss_processor.get_feed_articles(rss_url)
                    if not articles:
                        error_message = "Could not fetch articles from the RSS feed."
                    elif article_index is not None:
                        # Specific article selected
                        try:
                            idx = int(article_index)
                            if 0 <= idx < len(articles):
                                selected_article = articles[idx]
                                text = selected_article.get('content') or selected_article.get('summary', '')
                                source_info = {
                                    'type': 'rss',
                                    'source': rss_url,
                                    'article_title': selected_article.get('title', 'Unknown'),
                                    'article_url': selected_article.get('link', ''),
                                    'published': selected_article.get('published', '')
                                }
                            else:
                                error_message = "Invalid article selection."
                        except (ValueError, IndexError):
                            error_message = "Invalid article selection."
                    else:
                        # Show article list for selection
                        return render_template('index.html', 
                                             rss_articles=articles, 
                                             rss_url=rss_url,
                                             show_rss_selection=True)
                        
                except Exception as e:
                    error_message = f"Error processing RSS feed: {str(e)}"
        
        # Check for errors
        if error_message:
            return render_template('index.html', error=error_message)
        
        # Validate text length
        if len(text.strip()) < 50:
            return render_template('index.html', 
                                 error="Text is too short for meaningful analysis. Please provide at least 50 characters.")
        
        if len(text) > 50000:  # Limit very long texts
            text = text[:50000]
            flash("Text was truncated to 50,000 characters for processing.", "warning")
        
        # Perform analysis
        analysis_results = perform_analysis(text)
        
        # Add metadata
        analysis_results['metadata'] = {
            'input_method': input_method,
            'source_info': source_info,
            'text_length': len(text),
            'word_count': len(text.split()),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return render_template('results.html', 
                             original_text=text,  # Pass full text
                             full_text_length=len(text),
                             results=analysis_results)
        
    except RequestEntityTooLarge:
        return render_template('index.html', 
                             error="File size too large. Maximum 16MB allowed.")
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        return render_template('index.html', 
                             error=f"An unexpected error occurred: {str(e)}")

def perform_analysis(text):
    """Perform comprehensive text analysis"""
    results = {}
    
    try:
        # Language Detection
        try:
            detected_lang, confidence = language_detector.detect_language(text)
            results['language'] = {
                'code': detected_lang,
                'name': language_detector.get_language_name(detected_lang),
                'confidence': confidence,
                'supported': language_detector.is_supported(detected_lang)
            }
        except Exception as e:
            logger.error(f"Language detection error: {str(e)}")
            results['language'] = {
                'code': 'unknown',
                'name': 'Unknown',
                'confidence': 0.0,
                'supported': False,
                'error': str(e)
            }
        
        # Text Summarization
        try:
            summary = summarizer.summarize(text, results['language']['code'])
            results['summary'] = {
                'text': summary,
                'original_words': len(text.split()),
                'summary_words': len(summary.split()) if summary else 0,
                'compression_ratio': (len(summary.split()) / len(text.split()) * 100) if summary and text.split() else 0
            }
        except Exception as e:
            logger.error(f"Summarization error: {str(e)}")
            results['summary'] = {
                'text': None,
                'error': str(e),
                'original_words': len(text.split()),
                'summary_words': 0,
                'compression_ratio': 0
            }
        
        # Sentiment Analysis
        try:
            sentiment_result = sentiment_analyzer.analyze_sentiment(text, results['language']['code'])
            if sentiment_result:
                results['sentiment'] = sentiment_result
            else:
                results['sentiment'] = {
                    'label': 'Unknown',
                    'score': 0.0,
                    'confidence': 'Low',
                    'error': 'Could not analyze sentiment'
                }
        except Exception as e:
            logger.error(f"Sentiment analysis error: {str(e)}")
            results['sentiment'] = {
                'label': 'Unknown',
                'score': 0.0,
                'confidence': 'Low',
                'error': str(e)
            }
        
        # Text Statistics
        results['statistics'] = calculate_text_statistics(text)
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        results['error'] = str(e)
    
    return results

def calculate_text_statistics(text):
    """Calculate various text statistics"""
    try:
        words = text.split()
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        # Calculate reading time (average 200 words per minute)
        reading_time_minutes = len(words) / 200
        
        # Average word length
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        # Most frequent words (excluding common stop words)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'this', 'that', 'these', 'those'}
        
        clean_words = [word.lower().strip('.,!?;:"()[]{}') for word in words 
                      if word.lower().strip('.,!?;:"()[]{}') not in stop_words and len(word) > 3]
        
        from collections import Counter
        word_freq = Counter(clean_words).most_common(10)
        
        return {
            'total_characters': len(text),
            'total_words': len(words),
            'total_sentences': len(sentences),
            'total_paragraphs': len(paragraphs),
            'avg_word_length': round(avg_word_length, 1),
            'reading_time_minutes': round(reading_time_minutes, 1),
            'most_frequent_words': word_freq
        }
    except Exception as e:
        logger.error(f"Statistics calculation error: {str(e)}")
        return {
            'total_characters': len(text),
            'total_words': len(text.split()),
            'error': str(e)
        }

@app.route('/get_rss_articles', methods=['POST'])
def get_rss_articles():
    """Get articles from RSS feed for selection"""
    try:
        rss_url = request.form.get('rss_url', '').strip()
        if not rss_url:
            return jsonify({'error': 'RSS URL is required'}), 400
        
        articles = rss_processor.get_feed_articles(rss_url)
        return jsonify({'articles': articles})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """API endpoint for programmatic access"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Text field is required'}), 400
        
        text = data['text']
        if len(text.strip()) < 50:
            return jsonify({'error': 'Text too short for analysis'}), 400
        
        results = perform_analysis(text)
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(413)
def too_large(e):
    return render_template('index.html', 
                         error="File size too large. Maximum 16MB allowed."), 413

@app.errorhandler(500)
def internal_error(e):
    return render_template('index.html', 
                         error="An internal server error occurred. Please try again."), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
