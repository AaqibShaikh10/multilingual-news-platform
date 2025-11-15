from transformers import pipeline
import torch
from typing import Dict, Optional
import warnings
import logging

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Perform sentiment analysis on multilingual text with proper text chunking"""
    
    def __init__(self):
        self.device = 0 if torch.cuda.is_available() else -1
        self.analyzers = {}
        self._load_models()
    
    def _load_models(self):
        """Load sentiment analysis models with proper truncation settings"""
        try:
            logger.info("Loading sentiment analysis models...")
            
            # Try to load multilingual sentiment model
            try:
                self.analyzers['multilingual'] = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-xlm-roberta-base-sentiment",
                    device=self.device,
                    truncation=True,
                    max_length=512,
                    padding=True
                )
                logger.info("Successfully loaded multilingual sentiment model")
            except Exception as e:
                logger.warning(f"Could not load multilingual sentiment model: {str(e)}")
            
            # English-specific model (more accurate for English)
            try:
                self.analyzers['english'] = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                    device=self.device,
                    truncation=True,
                    max_length=512,
                    padding=True
                )
                logger.info("Successfully loaded English sentiment model")
            except Exception as e:
                logger.warning(f"Could not load English sentiment model: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error loading sentiment models: {str(e)}")
            # Fallback to basic model
            try:
                self.analyzers['basic'] = pipeline(
                    "sentiment-analysis",
                    model="distilbert-base-uncased-finetuned-sst-2-english",
                    device=self.device,
                    truncation=True,
                    max_length=512,
                    padding=True
                )
                logger.info("Loaded fallback sentiment model")
            except Exception as e2:
                logger.error(f"Failed to load fallback sentiment model: {str(e2)}")
                self.analyzers = {}
    
    def analyze_sentiment(self, text: str, language: str = 'en') -> Optional[Dict]:
        """
        Analyze sentiment with automatic text chunking for long content
        
        Args:
            text (str): Input text
            language (str): Language code
            
        Returns:
            Optional[Dict]: Dictionary with 'label', 'score', and 'confidence'
        """
        try:
            if not text or len(text.strip()) < 10:
                return None
            
            # Choose appropriate model
            model_key = self._select_model(language)
            
            if model_key not in self.analyzers:
                logger.error("No sentiment models available")
                return None
            
            # Get the analyzer
            analyzer = self.analyzers[model_key]
            
            # Clean and prepare text
            clean_text = self._clean_text(text)
            
            # Check text length and decide processing method
            words = clean_text.split()
            
            if len(words) <= 300:  # Short text - direct analysis
                return self._analyze_short_text(clean_text, analyzer)
            else:  # Long text - chunk analysis
                return self._analyze_long_text(clean_text, analyzer)
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {str(e)}")
            return None
    
    def _analyze_short_text(self, text: str, analyzer) -> Optional[Dict]:
        """Analyze short text directly"""
        try:
            # Ensure text is within limits
            words = text.split()
            if len(words) > 300:
                text = ' '.join(words[:300])
            
            logger.info(f"Analyzing short text ({len(words)} words)")
            
            # Analyze sentiment
            result = analyzer(text)
            
            # Process result
            if isinstance(result, list):
                result = result[0]
            
            # Normalize labels
            label = self._normalize_label(result['label'])
            score = result['score']
            
            logger.info(f"Sentiment result: {label} (confidence: {score:.3f})")
            
            return {
                'label': label,
                'score': score,
                'confidence': self._get_confidence_level(score)
            }
            
        except Exception as e:
            logger.error(f"Short text analysis error: {str(e)}")
            return None
    
    def _analyze_long_text(self, text: str, analyzer) -> Optional[Dict]:
        """Analyze long text by splitting into chunks"""
        try:
            words = text.split()
            chunk_size = 250  # Conservative chunk size to avoid token limits
            
            # Split into chunks
            chunks = []
            for i in range(0, len(words), chunk_size):
                chunk = ' '.join(words[i:i + chunk_size])
                chunks.append(chunk)
            
            logger.info(f"Analyzing long text ({len(words)} words) in {len(chunks)} chunks")
            
            results = []
            sentiment_scores = {'Positive': [], 'Negative': [], 'Neutral': []}
            
            # Analyze each chunk
            for i, chunk in enumerate(chunks):
                try:
                    result = analyzer(chunk)
                    if isinstance(result, list):
                        result = result[0]
                    
                    label = self._normalize_label(result['label'])
                    score = result['score']
                    
                    sentiment_scores[label].append(score)
                    results.append({'label': label, 'score': score})
                    
                    logger.info(f"Chunk {i+1}/{len(chunks)}: {label} ({score:.3f})")
                    
                except Exception as e:
                    logger.warning(f"Error processing chunk {i+1}: {str(e)}")
                    continue
            
            if not results:
                logger.error("No chunks could be processed")
                return None
            
            # Calculate overall sentiment
            # Method: Average scores for each sentiment, then pick highest
            avg_scores = {}
            for sentiment, scores in sentiment_scores.items():
                if scores:
                    avg_scores[sentiment] = sum(scores) / len(scores)
                else:
                    avg_scores[sentiment] = 0.0
            
            # Find dominant sentiment
            dominant_sentiment = max(avg_scores, key=avg_scores.get)
            dominant_score = avg_scores[dominant_sentiment]
            
            logger.info(f"Overall sentiment: {dominant_sentiment} (score: {dominant_score:.3f}) from {len(results)} chunks")
            
            return {
                'label': dominant_sentiment,
                'score': dominant_score,
                'confidence': self._get_confidence_level(dominant_score),
                'chunks_analyzed': len(results),
                'method': 'chunked_analysis'
            }
            
        except Exception as e:
            logger.error(f"Long text analysis error: {str(e)}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean text for sentiment analysis"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        import re
        text = re.sub(r'\s+', ' ', text)
        
        # Remove very long URLs
        text = re.sub(r'http[s]?://\S+', '[URL]', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '[EMAIL]', text)
        
        return text.strip()
    
    def _select_model(self, language: str) -> str:
        """Select the best model for the given language"""
        if language == 'en' and 'english' in self.analyzers:
            return 'english'
        elif 'multilingual' in self.analyzers:
            return 'multilingual'
        elif 'basic' in self.analyzers:
            return 'basic'
        else:
            return list(self.analyzers.keys())[0] if self.analyzers else None
    
    def _normalize_label(self, label: str) -> str:
        """Normalize sentiment labels to standard format"""
        label_lower = label.lower()
        
        if 'pos' in label_lower or label_lower in ['label_2', '2']:
            return 'Positive'
        elif 'neg' in label_lower or label_lower in ['label_0', '0']:
            return 'Negative'
        else:
            return 'Neutral'
    
    def _get_confidence_level(self, score: float) -> str:
        """Convert numerical score to confidence level"""
        if score >= 0.8:
            return 'High'
        elif score >= 0.6:
            return 'Medium'
        else:
            return 'Low'
