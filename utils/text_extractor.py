import requests
from bs4 import BeautifulSoup
import pypdf
from urllib.parse import urlparse
import re
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class TextExtractor:
    """Extract text from various sources: URLs, PDFs"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def extract_from_url(self, url: str) -> Optional[str]:
        """Extract text content from a news article URL"""
        try:
            logger.info(f"Extracting text from URL: {url}")
            
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("Invalid URL format")
            
            # Make request with timeout
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'menu']):
                element.decompose()
            
            # Try different strategies to find article content
            article_text = self._extract_article_content(soup)
            
            if not article_text:
                # Fallback: get all paragraph text
                paragraphs = soup.find_all('p')
                article_text = '\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            
            # Clean up the text
            article_text = self._clean_text(article_text)
            
            logger.info(f"Successfully extracted {len(article_text)} characters")
            return article_text if len(article_text.strip()) > 50 else None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error extracting from URL: {str(e)}")
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Text extraction error: {str(e)}")
            raise Exception(f"Text extraction error: {str(e)}")
    
    def _extract_article_content(self, soup: BeautifulSoup) -> str:
        """Try various strategies to extract main article content"""
        
        # Strategy 1: Look for common article selectors
        article_selectors = [
            'article',
            '[role="main"]',
            '.post-content',
            '.entry-content',
            '.article-body',
            '.story-body',
            '.post-body',
            '.content',
            'main'
        ]
        
        for selector in article_selectors:
            elements = soup.select(selector)
            if elements:
                text = '\n'.join([elem.get_text().strip() for elem in elements])
                if len(text) > 200:  # Minimum length check
                    return text
        
        # Strategy 2: Look for div with most paragraph content
        divs = soup.find_all('div')
        best_div = None
        max_p_count = 0
        
        for div in divs:
            p_count = len(div.find_all('p'))
            if p_count > max_p_count:
                max_p_count = p_count
                best_div = div
        
        if best_div and max_p_count > 2:
            return best_div.get_text().strip()
        
        return ""
    
    def extract_from_pdf(self, pdf_path: str) -> Optional[str]:
        """Extract text from PDF file"""
        try:
            logger.info(f"Extracting text from PDF: {pdf_path}")
            
            text = ""
            reader = pypdf.PdfReader(pdf_path)
            
            # Extract text from all pages
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num}: {str(e)}")
                    continue
            
            # Clean up the text
            text = self._clean_text(text)
            
            logger.info(f"Successfully extracted {len(text)} characters from PDF")
            return text if len(text.strip()) > 50 else None
            
        except Exception as e:
            logger.error(f"PDF extraction error: {str(e)}")
            raise Exception(f"PDF extraction error: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,;:!?()-]', '', text)
        
        # Remove very short lines (likely navigation/menu items)
        lines = text.split('\n')
        cleaned_lines = [line.strip() for line in lines if len(line.strip()) > 10]
        
        return '\n'.join(cleaned_lines).strip()
