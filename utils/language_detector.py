from langdetect import detect, detect_langs, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
from typing import Tuple, Optional
import re
import logging

logger = logging.getLogger(__name__)

# Set seed for reproducible results
DetectorFactory.seed = 0

class LanguageDetector:
    """Detect language of input text"""
    
    def __init__(self):
        self.language_names = {
            'en': 'English',
            'es': 'Spanish', 
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'ur': 'Urdu',
            'zh': 'Chinese',
            'ja': 'Japanese',
            'ko': 'Korean',
            'ru': 'Russian',
            'tr': 'Turkish',
            'nl': 'Dutch',
            'sv': 'Swedish',
            'da': 'Danish',
            'no': 'Norwegian',
            'fi': 'Finnish',
            'pl': 'Polish'
        }
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detect language of the given text
        
        Args:
            text (str): Input text
            
        Returns:
            Tuple[str, float]: (language_code, confidence)
        """
        try:
            # Clean text for better detection
            clean_text = self._clean_text_for_detection(text)
            
            if len(clean_text.strip()) < 20:
                return 'unknown', 0.0
            
            # Get language with confidence
            languages = detect_langs(clean_text)
            
            if languages:
                primary_lang = languages[0]
                lang_code = primary_lang.lang
                confidence = primary_lang.prob
                
                logger.info(f"Detected language: {lang_code} (confidence: {confidence:.2f})")
                return lang_code, confidence
            else:
                return 'unknown', 0.0
                
        except LangDetectException:
            # Fallback: try simple detection
            try:
                lang_code = detect(clean_text)
                logger.info(f"Fallback detection: {lang_code}")
                return lang_code, 0.5  # Medium confidence for simple detection
            except:
                return 'unknown', 0.0
        except Exception as e:
            logger.error(f"Language detection error: {str(e)}")
            return 'unknown', 0.0
    
    def get_language_name(self, lang_code: str) -> str:
        """Get full language name from language code"""
        return self.language_names.get(lang_code, lang_code.upper())
    
    def is_supported(self, lang_code: str) -> bool:
        """Check if language is supported by the models"""
        supported_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ar', 'hi', 'ur', 'zh']
        return lang_code in supported_languages
    
    def _clean_text_for_detection(self, text: str) -> str:
        """Clean text to improve language detection accuracy"""
        if not text:
            return ""
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove numbers and special characters for better language detection
        text = re.sub(r'\d+', '', text)
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
