"""
Web Summarizer - Intelligent Web Content Analysis Module.
"""
import requests
from bs4 import BeautifulSoup
import re
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class WebSummarizer:
    """Intelligent web content summarization engine."""
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; SecondBrainBot/1.0; +http://example.com/bot)"
        }
        # Common content wrappers in news/tech sites
        self.content_classes = [
            "article-content",
            "post-content",
            "entry-content",
            "article-body",
            "content-body",
            "story-body",
            "article-text",
            "story-content"
        ]

    async def fetch_and_summarize(self, url: str) -> str:
        """
        Fetch content from URL and generate an intelligent summary.
        
        Args:
            url: The URL to fetch and summarize
            
        Returns:
            A concise summary of the content
        """
        try:
            response = requests.get(url, timeout=10, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Try to find main content
            content = self._extract_main_content(soup)
            if not content:
                # Fallback to all paragraphs if no main content found
                content = ' '.join([p.get_text() for p in soup.find_all("p")])
            
            # Get title if available
            title = self._extract_title(soup)
            
            # Generate summary
            summary = self.summarize_text(content)
            
            if title:
                return f"{title}\n\nKey points: {summary}"
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing {url}: {str(e)}")
            return f"Unable to summarize content from {url} — {str(e)}"

    def _extract_main_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract the main content from the parsed HTML."""
        # Try to find content by common class names
        for class_name in self.content_classes:
            content_div = soup.find(class_=class_name)
            if content_div:
                return content_div.get_text()
        
        # Try article tag
        article = soup.find('article')
        if article:
            return article.get_text()
            
        return None

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract the article title."""
        # Try meta title first
        meta_title = soup.find("meta", property="og:title")
        if meta_title:
            return meta_title.get("content")
            
        # Try h1
        h1 = soup.find("h1")
        if h1:
            return h1.get_text().strip()
            
        # Try title tag
        title = soup.find("title")
        if title:
            return title.get_text().strip()
            
        return None

    def summarize_text(self, text: str) -> str:
        """
        Generate an intelligent summary of the text.
        
        Args:
            text: The text to summarize
            
        Returns:
            A concise summary
        """
        # Clean the text
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Remove very short sentences and clean up
        sentences = [s.strip() for s in sentences if len(s.split()) > 5]
        
        # Select key sentences (first 3 by default)
        selected = sentences[:3] if len(sentences) > 3 else sentences
        
        # Join sentences and clean up
        summary = ' '.join(selected).strip()
        
        # Truncate if too long
        if len(summary) > 500:
            summary = summary[:497] + "..."
            
        return summary 