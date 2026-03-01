"""
Yahoo Finance news scraper module.
Handles web scraping with retry logic and error handling.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class YahooFinanceScraper:
    """Scrapes news articles from Yahoo Finance for a given ticker."""

    RSS_URL = "https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
    QUOTE_URL = "https://finance.yahoo.com/quote/{ticker}/"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    def __init__(self, timeout: int = 10):
        """
        Initialize the scraper.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _fetch_page(self, url: str) -> str:
        """
        Fetch page content with retry logic.

        Args:
            url: URL to fetch

        Returns:
            Page HTML content

        Raises:
            requests.RequestException: On network failures after retries
        """
        logger.info(f"Fetching URL: {url}")
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    def scrape_news(self, ticker: str, max_articles: int = 10) -> List[Dict[str, str]]:
        """
        Scrape news articles for a given ticker.
        Uses RSS feed as primary source, falls back to quote page HTML parsing.

        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA', 'AAPL')
            max_articles: Maximum number of articles to retrieve

        Returns:
            List of article dictionaries containing headline, summary, link, and timestamp

        Raises:
            ValueError: If ticker is invalid or no articles found
            requests.RequestException: On network failures
        """
        if not ticker or not ticker.strip():
            raise ValueError("Ticker symbol cannot be empty")

        ticker = ticker.upper().strip()

        # Primary: RSS feed (reliable, structured data)
        articles = self._scrape_rss_feed(ticker)

        # Fallback: parse the main quote page
        if not articles:
            logger.warning(f"RSS feed returned no articles for {ticker}, trying quote page")
            articles = self._scrape_quote_page(ticker)

        if not articles:
            raise ValueError(f"No articles found for ticker {ticker}")

        logger.info(f"Successfully scraped {len(articles)} articles for {ticker}")
        return articles[:max_articles]

    def _scrape_rss_feed(self, ticker: str) -> List[Dict[str, str]]:
        """
        Scrape articles from Yahoo Finance RSS feed.

        Args:
            ticker: Stock ticker symbol

        Returns:
            List of articles from RSS feed
        """
        rss_url = self.RSS_URL.format(ticker=ticker)
        articles: List[Dict[str, str]] = []

        try:
            xml_content = self._fetch_page(rss_url)
            soup = BeautifulSoup(xml_content, 'xml')

            for item in soup.find_all('item'):
                title = item.find('title')
                link = item.find('link')
                description = item.find('description')

                if not title or not title.get_text(strip=True):
                    continue

                articles.append({
                    'headline': title.get_text(strip=True),
                    'summary': description.get_text(strip=True) if description else title.get_text(strip=True),
                    'link': link.get_text(strip=True) if link else "",
                    'ticker': ticker,
                    'timestamp': datetime.now().isoformat()
                })

            logger.info(f"Scraped {len(articles)} articles from RSS feed for {ticker}")
        except Exception as e:
            logger.warning(f"RSS feed scraping failed for {ticker}: {e}")

        return articles

    def _scrape_quote_page(self, ticker: str) -> List[Dict[str, str]]:
        """
        Fallback: parse news from the main quote page HTML.

        Args:
            ticker: Stock ticker symbol

        Returns:
            List of parsed articles
        """
        url = self.QUOTE_URL.format(ticker=ticker)
        articles: List[Dict[str, str]] = []

        try:
            html_content = self._fetch_page(url)
            soup = BeautifulSoup(html_content, 'lxml')

            # Yahoo Finance renders news items with h3 tags containing links
            for h3 in soup.find_all('h3'):
                link_elem = h3.find('a', href=True) or h3.find_parent('a', href=True)
                if not link_elem:
                    continue

                headline = h3.get_text(strip=True)
                if not headline or len(headline) < 10:
                    continue

                link = link_elem['href']
                if link and not link.startswith('http'):
                    link = f"https://finance.yahoo.com{link}"

                # Try to find a sibling paragraph as summary
                parent = h3.parent
                summary_elem = parent.find('p') if parent else None
                summary = summary_elem.get_text(strip=True) if summary_elem else headline

                articles.append({
                    'headline': headline,
                    'summary': summary,
                    'link': link,
                    'ticker': ticker,
                    'timestamp': datetime.now().isoformat()
                })

            logger.info(f"Scraped {len(articles)} articles from quote page for {ticker}")
        except Exception as e:
            logger.warning(f"Quote page scraping failed for {ticker}: {e}")

        return articles

    def close(self):
        """Close the session."""
        self.session.close()
