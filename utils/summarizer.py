from transformers import pipeline
import torch
from typing import Optional
import warnings
import logging

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

class TextSummarizer:
    """Generate summaries using transformer models"""
    
    def __init__(self):
        self.device = 0 if torch.cuda.is_available() else -1
        self.summarizers = {}
        self._load_models()
    
    def _load_models(self):
        """Load summarization models for different languages"""
        try:
            logger.info("Loading summarization models...")
            
            # Universal model that works well for multiple languages
            self.summarizers['universal'] = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=self.device
            )
            
            logger.info("Successfully loaded universal summarization model")
            
            # Try to load multilingual model
            try:
                self.summarizers['multilingual'] = pipeline(
                    "summarization", 
                    model="csebuetnlp/mT5_multilingual_XLSum",
                    device=self.device
                )
                logger.info("Successfully loaded multilingual summarization model")
            except Exception as e:
                logger.warning(f"Could not load multilingual model: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error loading summarization models: {str(e)}")
            # Fallback to a lighter model
            try:
                self.summarizers['universal'] = pipeline(
                    "summarization",
                    model="sshleifer/distilbart-cnn-12-6",
                    device=self.device
                )
                logger.info("Loaded fallback summarization model")
            except Exception as e2:
                logger.error(f"Failed to load fallback model: {str(e2)}")
                self.summarizers = {}
    
    def summarize(self, text: str, language: str = 'en', max_length: int = 150, min_length: int = 30) -> Optional[str]:
        """
        Generate summary of the input text
        
        Args:
            text (str): Input text to summarize
            language (str): Language code
            max_length (int): Maximum summary length
            min_length (int): Minimum summary length
            
        Returns:
            Optional[str]: Generated summary
        """
        try:
            if not text or len(text.strip()) < 100:
                return "Text too short for summarization."
            
            # Choose appropriate model based on language
            model_key = self._select_model(language)
            
            if model_key not in self.summarizers:
                return "Summarization model not available."
            
            # Prepare text for summarization
            prepared_text = self._prepare_text(text)
            
            # Generate summary
            summarizer = self.summarizers[model_key]
            
            # Adjust parameters based on text length
            text_length = len(prepared_text.split())
            if text_length < 200:
                max_length = min(max_length, text_length // 2)
                min_length = min(min_length, max_length // 2)
            
            logger.info(f"Generating summary for {text_length} words using {model_key} model")
            
            result = summarizer(
                prepared_text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False,
                truncation=True
            )
            
            summary = result[0]['summary_text']
            
            # Post-process summary
            summary = self._post_process_summary(summary)
            
            logger.info(f"Generated summary: {len(summary)} characters")
            return summary
            
        except Exception as e:
            logger.error(f"Summarization error: {str(e)}")
            return self._extractive_fallback(text)
    
    def _select_model(self, language: str) -> str:
        """Select the best model for the given language"""
        # For non-English languages, prefer multilingual model if available
        if language != 'en' and 'multilingual' in self.summarizers:
            return 'multilingual'
        elif 'universal' in self.summarizers:
            return 'universal'
        else:
            return list(self.summarizers.keys())[0] if self.summarizers else None
    
    def _prepare_text(self, text: str) -> str:
        """Prepare text for summarization"""
        # Limit text length to avoid model limits
        words = text.split()
        if len(words) > 1000:
            text = ' '.join(words[:1000])
        
        # Clean up the text
        text = text.replace('\n', ' ').strip()
        
        return text
    
    def _post_process_summary(self, summary: str) -> str:
        """Post-process the generated summary"""
        # Remove incomplete sentences at the end
        sentences = summary.split('.')
        if len(sentences) > 1 and len(sentences[-1].strip()) < 10:
            summary = '.'.join(sentences[:-1]) + '.'
        
        # Ensure proper capitalization
        if summary and not summary[0].isupper():
            summary = summary[0].upper() + summary[1:]
        
        return summary.strip()
    
    def _extractive_fallback(self, text: str) -> str:
        """Simple extractive summarization as fallback"""
        try:
            sentences = text.split('.')
            # Take first 3 sentences as a simple summary
            if len(sentences) >= 3:
                summary = '. '.join(sentences[:3]) + '.'
                return summary
            else:
                return text[:300] + "..." if len(text) > 300 else text
        except:
            return "Unable to generate summary."
