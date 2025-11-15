import feedparser
import requests
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class RSSProcessor:
    """Process RSS feeds and extract news articles"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def get_feed_articles(self, rss_url: str, max_articles: int = 20) -> List[Dict]:
        """
        Get articles from RSS feed
        
        Args:
            rss_url (str): RSS feed URL
            max_articles (int): Maximum number of articles to fetch
            
        Returns:
            List[Dict]: List of article dictionaries
        """
        try:
            logger.info(f"Fetching RSS feed: {rss_url}")
            
            # Parse RSS feed
            feed = feedparser.parse(rss_url)
            
            if feed.bozo and not feed.entries:
                raise Exception("Invalid RSS feed or no articles found")
            
            articles = []
            
            for i, entry in enumerate(feed.entries[:max_articles]):
                try:
                    # Extract article data
                    article = {
                        'title': entry.get('title', 'No Title'),
                        'link': entry.get('link', ''),
                        'summary': entry.get('summary', ''),
                        'content': self._extract_content(entry),
                        'published': self._format_published_date(entry.get('published_parsed')),
                        'author': entry.get('author', ''),
                        'tags': self._extract_tags(entry),
                        'index': i
                    }
                    
                    # Clean and validate article content
                    if article['content'] or article['summary']:
                        articles.append(article)
                        
                except Exception as e:
                    logger.warning(f"Error processing RSS article {i}: {str(e)}")
                    continue
            
            logger.info(f"Successfully fetched {len(articles)} articles from RSS feed")
            return articles
            
        except Exception as e:
            logger.error(f"RSS processing error: {str(e)}")
            raise Exception(f"Failed to process RSS feed: {str(e)}")
    
    def _extract_content(self, entry) -> str:
        """Extract the best available content from RSS entry"""
        # Try different content fields in order of preference
        content_fields = [
            'content',
            'summary_detail', 
            'description',
            'summary'
        ]
        
        content = ""
        
        for field in content_fields:
            if hasattr(entry, field):
                field_content = getattr(entry, field)
                
                if isinstance(field_content, list) and field_content:
                    # Handle content list (like entry.content)
                    content = field_content[0].get('value', '')
                elif isinstance(field_content, dict):
                    # Handle content dict (like summary_detail)
                    content = field_content.get('value', '')
                elif isinstance(field_content, str):
                    # Handle direct string content
                    content = field_content
                
                if content and len(content.strip()) > 100:
                    break
        
        # Clean HTML tags from content
        if content:
            content = self._clean_html(content)
        
        return content
    
    def _clean_html(self, html_content: str) -> str:
        """Remove HTML tags and clean content"""
        try:
            from bs4 import BeautifulSoup
            
            # Parse HTML and extract text
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for element in soup(['script', 'style']):
                element.decompose()
            
            # Get text and clean up
            text = soup.get_text()
            
            # Clean up whitespace
            import re
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text
            
        except Exception as e:
            logger.warning(f"HTML cleaning error: {str(e)}")
            return html_content
    
    def _format_published_date(self, published_parsed) -> str:
        """Format published date"""
        try:
            if published_parsed:
                dt = datetime(*published_parsed[:6])
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            return ''
        except Exception:
            return ''
    
    def _extract_tags(self, entry) -> List[str]:
        """Extract tags/categories from RSS entry"""
        tags = []
        try:
            if hasattr(entry, 'tags'):
                tags = [tag.get('term', '') for tag in entry.tags if tag.get('term')]
            elif hasattr(entry, 'category'):
                tags = [entry.category]
        except Exception:
            pass
        
        return tags
    
    def get_popular_rss_feeds(self) -> Dict[str, List[Dict[str, str]]]:
        """Get a list of popular RSS feeds by category"""
        return {
            'News': [
                {'name': 'BBC News', 'url': 'http://feeds.bbci.co.uk/news/rss.xml'},
                {'name': 'CNN', 'url': 'http://rss.cnn.com/rss/edition.rss'},
                {'name': 'Reuters', 'url': 'https://www.reuters.com/rssFeed/worldNews'},
                {'name': 'Associated Press', 'url': 'https://apnews.com/apf-topnews'},
            ],
            'Technology': [
                {'name': 'TechCrunch', 'url': 'https://techcrunch.com/feed/'},
                {'name': 'The Verge', 'url': 'https://www.theverge.com/rss/index.xml'},
                {'name': 'Ars Technica', 'url': 'http://feeds.arstechnica.com/arstechnica/index'},
                {'name': 'Wired', 'url': 'https://www.wired.com/feed/rss'},
            ],
            'Business': [
                {'name': 'Wall Street Journal', 'url': 'https://feeds.a.dj.com/rss/RSSWorldNews.xml'},
                {'name': 'Financial Times', 'url': 'https://www.ft.com/rss'},
                {'name': 'Bloomberg', 'url': 'https://feeds.bloomberg.com/markets/news.rss'},
                {'name': 'Forbes', 'url': 'https://www.forbes.com/real-time/feed2/'},
            ],
            'Science': [
                {'name': 'Scientific American', 'url': 'https://www.scientificamerican.com/xml/rss.xml'},
                {'name': 'Nature', 'url': 'https://www.nature.com/nature.rss'},
                {'name': 'Science Magazine', 'url': 'https://www.science.org/rss/news_current.xml'},
            ]
        }
