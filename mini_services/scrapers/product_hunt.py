"""
Product Hunt Scraper for IndoGap - AI-Powered Opportunity Discovery Engine

This module provides functionality to scrape product data from Product Hunt,
extracting trending products, launch metrics, and user feedback signals.
"""
import re
import time
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, ScraperResult, ScraperError
from mini_services.models.startup import GlobalStartup, create_global_startup, StartupSource
from mini_services.config import get_settings

logger = logging.getLogger(__name__)


class ProductHuntScraper(BaseScraper):
    """
    Scraper for Product Hunt product data.
    
    Extracts information from:
    - Today's featured products
    - Product archives by date
    - Individual product pages
    
    Data extracted includes:
    - Product name and tagline
    - Description and features
    - Upvote count and comments
    - Categories and tags
    - Maker information
    - Launch date
    """
    
    def __init__(
        self,
        delay: float = None,
        timeout: int = None,
        max_retries: int = None,
    ):
        """
        Initialize Product Hunt scraper.
        
        Args:
            delay: Delay between requests
            timeout: Request timeout
            max_retries: Maximum retry attempts
        """
        settings = get_settings()
        
        super().__init__(
            name="product_hunt_scraper",
            base_url="https://www.producthunt.com",
            delay=delay or settings.product_hunt_scrape_delay,
            timeout=timeout or settings.request_timeout,
            max_retries=max_retries or settings.max_retries,
        )
        
        self.api_url = "https://api.producthunt.com/v2/api/graphql"
        
    def scrape(
        self,
        days: int = 7,
        min_upvotes: int = 100,
        include_details: bool = True,
    ) -> ScraperResult:
        """
        Scrape trending products from Product Hunt.
        
        Args:
            days: Number of days to scrape
            min_upvotes: Minimum upvote threshold
            include_details: Fetch detailed product info
            
        Returns:
            ScraperResult with product data
        """
        logger.info(f"Starting Product Hunt scrape (last {days} days)")
        
        result = ScraperResult(success=False)
        
        try:
            products = []
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Try API first (if key available)
            settings = get_settings()
            if settings.product_hunt_api_key:
                api_products = self._scrape_via_api(
                    start_date=start_date,
                    end_date=end_date,
                    min_upvotes=min_upvotes,
                )
                products.extend(api_products)
            
            # Fallback to web scraping if no API or to supplement
            if not products:
                web_products = self._scrape_via_web(
                    days=days,
                    min_upvotes=min_upvotes,
                )
                products.extend(web_products)
            
            # Remove duplicates by product name
            seen = set()
            unique_products = []
            for p in products:
                name = p.get('name', '').lower()
                if name and name not in seen:
                    seen.add(name)
                    unique_products.append(p)
            
            # Filter by minimum upvotes
            if min_upvotes > 0:
                unique_products = [p for p in unique_products 
                                 if p.get('upvotes', 0) >= min_upvotes]
            
            # Enrich with details if requested
            if include_details and unique_products:
                unique_products = self._enrich_products(unique_products)
            
            result.success = True
            result.data = unique_products
            result.metadata = {
                "days_scraped": days,
                "min_upvotes": min_upvotes,
                "total_products": len(unique_products),
            }
            
            logger.info(f"Successfully scraped {len(unique_products)} products from Product Hunt")
            
        except ScraperError as e:
            logger.error(f"Product Hunt scrape failed: {e.message}")
            result.add_error(e.message)
            
        except Exception as e:
            logger.error(f"Unexpected error during Product Hunt scrape: {str(e)}")
            result.add_error(str(e))
        
        return result
    
    def _scrape_via_api(
        self,
        start_date: datetime,
        end_date: datetime,
        min_upvotes: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Scrape using Product Hunt API (if available).
        
        Args:
            start_date: Start date for search
            end_date: End date for search
            min_upvotes: Minimum upvote threshold
            
        Returns:
            List of product data dictionaries
        """
        settings = get_settings()
        api_key = settings.product_hunt_api_key
        
        if not api_key:
            return []
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        query = """
        query($cursor: String) {
          posts(first: 50, after: $cursor, order: NEWEST) {
            pageInfo {
              hasNextPage
              endCursor
            }
            edges {
              node {
                id
                name
                tagline
                description
                url
                votesCount
                commentsCount
                publishedAt
                topics {
                  name
                }
                maker {
                  name
                }
              }
            }
          }
        }
        """
        
        products = []
        cursor = None
        max_pages = 10  # Limit API calls
        
        for _ in range(max_pages):
            try:
                variables = {"cursor": cursor} if cursor else {}
                self._ensure_client()  # Ensure client is created before using
                response = self.client.post(
                    self.api_url,
                    json={"query": query, "variables": variables},
                    headers=headers,
                )
                
                if response.status_code != 200:
                    break
                
                data = response.json()
                posts = data.get('data', {}).get('posts', {}).get('edges', [])
                
                if not posts:
                    break
                
                for edge in posts:
                    node = edge.get('node', {})
                    published = datetime.fromisoformat(
                        node.get('publishedAt', '').replace('Z', '+00:00')
                    )
                    
                    # Filter by date range
                    if published < start_date:
                        return products
                    
                    # Filter by upvotes
                    if node.get('votesCount', 0) < min_upvotes:
                        continue
                    
                    products.append({
                        'name': node.get('name', ''),
                        'tagline': node.get('tagline', ''),
                        'description': node.get('description', ''),
                        'url': f"https://www.producthunt.com{node.get('url', '')}",
                        'upvotes': node.get('votesCount', 0),
                        'comments': node.get('commentsCount', 0),
                        'published_at': published.isoformat(),
                        'topics': [t.get('name') for t in node.get('topics', [])],
                        'maker': node.get('maker', {}).get('name') if node.get('maker') else None,
                        'source': 'product_hunt_api',
                    })
                
                # Check for more pages
                page_info = data.get('data', {}).get('posts', {}).get('pageInfo', {})
                if not page_info.get('hasNextPage'):
                    break
                
                cursor = page_info.get('endCursor')
                
            except Exception as e:
                logger.warning(f"API request failed: {str(e)}")
                break
        
        return products
    
    def _scrape_via_web(
        self,
        days: int = 7,
        min_upvotes: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Scrape using web scraping as fallback.
        
        Args:
            days: Number of days to scrape
            min_upvotes: Minimum upvote threshold
            
        Returns:
            List of product data dictionaries
        """
        products = []
        
        # Calculate dates
        end_date = datetime.now()
        for i in range(days):
            date = end_date - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            try:
                # Try daily archive page
                url = f"{self.base_url}/archive/{date_str}"
                daily_products = self._scrape_daily_archive(url, min_upvotes)
                products.extend(daily_products)
                
                time.sleep(self.delay)
                
            except Exception as e:
                logger.warning(f"Failed to scrape {date_str}: {str(e)}")
                continue
        
        return products
    
    def _scrape_daily_archive(
        self,
        url: str,
        min_upvotes: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Scrape a single day's archive page.
        
        Args:
            url: Archive page URL
            min_upvotes: Minimum upvote threshold
            
        Returns:
            List of product data from the day
        """
        try:
            response = self._make_request(url)
            soup = BeautifulSoup(response.text, 'lxml')
            
            products = []
            
            # Find product items
            product_items = soup.find_all('div', class_=re.compile(r'item|product', re.I))
            
            for item in product_items:
                product = self._parse_product_item(item)
                if product and product.get('upvotes', 0) >= min_upvotes:
                    products.append(product)
            
            return products
            
        except Exception as e:
            logger.warning(f"Failed to scrape archive page: {str(e)}")
            return []
    
    def _parse_product_item(self, item: 'BeautifulSoup.Element') -> Optional[Dict[str, Any]]:
        """Parse a single product item from the page"""
        try:
            # Find product name
            name_elem = item.find(['h2', 'h3', 'span'], class_=re.compile(r'name|title', re.I))
            if not name_elem:
                return None
            
            name = name_elem.get_text(strip=True)
            if not name or len(name) > 200:
                return None
            
            # Find tagline
            tagline_elem = item.find(['p', 'span'], class_=re.compile(r'tagline|desc', re.I))
            tagline = tagline_elem.get_text(strip=True) if tagline_elem else ''
            
            # Find upvotes
            upvote_elem = item.find(['span', 'div'], class_=re.compile(r'vote|count', re.I))
            upvotes = 0
            if upvote_elem:
                upvote_text = upvote_elem.get_text(strip=True)
                match = re.search(r'[\d,]+', upvote_text.replace(',', ''))
                if match:
                    upvotes = int(match.group())
            
            # Find URL
            link_elem = item.find('a', href=re.compile(r'/posts/', re.I))
            url = ''
            if link_elem:
                href = link_elem.get('href', '')
                url = f"{self.base_url}{href}"
            
            # Find topics/tags
            topic_elems = item.find_all(['span', 'a'], class_=re.compile(r'topic|tag', re.I))
            topics = [t.get_text(strip=True) for t in topic_elems]
            
            return {
                'name': name,
                'tagline': tagline,
                'description': '',
                'url': url,
                'upvotes': upvotes,
                'comments': 0,
                'published_at': '',
                'topics': topics,
                'maker': None,
                'source': 'product_hunt_web',
            }
            
        except Exception:
            return None
    
    def _enrich_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich product data with additional details.
        
        Args:
            products: List of product data
            
        Returns:
            Enriched product data
        """
        enriched = []
        
        for idx, product in enumerate(products):
            logger.info(f"Enriching product {idx+1}/{len(products)}: {product.get('name', 'Unknown')}")
            
            try:
                if product.get('url'):
                    details = self._fetch_product_details(product['url'])
                    if details:
                        product.update(details)
                
                enriched.append(product)
                time.sleep(self.delay)
                
            except Exception as e:
                logger.warning(f"Failed to enrich {product.get('name')}: {str(e)}")
                enriched.append(product)
        
        return enriched
    
    def _fetch_product_details(self, product_url: str) -> Dict[str, Any]:
        """
        Fetch detailed product information.
        
        Args:
            product_url: URL to product page
            
        Returns:
            Dictionary with additional details
        """
        try:
            response = self._make_request(product_url)
            soup = BeautifulSoup(response.text, 'lxml')
            
            details = {}
            
            # Extract full description
            desc_elem = soup.find('div', class_=re.compile(r'desc|about', re.I))
            if desc_elem:
                details['description'] = desc_elem.get_text(strip=True)[:1000]
            
            # Extract maker info
            maker_elem = soup.find(['span', 'a'], class_=re.compile(r'maker|maker-name', re.I))
            if maker_elem:
                details['maker'] = maker_elem.get_text(strip=True)
            
            # Extract pricing info if available
            price_elem = soup.find(['span', 'div'], class_=re.compile(r'price|free|paid', re.I))
            if price_elem:
                details['pricing'] = price_elem.get_text(strip=True)
            
            # Extract website link
            website_elem = soup.find('a', href=re.compile(r'^https?://', re.I))
            if website_elem and not website_elem.get('href', '').startswith('https://www.producthunt.com'):
                details['website'] = website_elem.get('href')
            
            return details
            
        except Exception:
            return {}
    
    def get_trending_products(self, limit: int = 10) -> ScraperResult:
        """
        Get currently trending products.
        
        Args:
            limit: Maximum number of products to return
            
        Returns:
            ScraperResult with trending products
        """
        try:
            url = f"{self.base_url}"
            response = self._make_request(url)
            soup = BeautifulSoup(response.text, 'lxml')
            
            products = []
            
            # Find trending section
            trending = soup.find('section', class_=re.compile(r'trending|popular', re.I))
            if trending:
                product_items = trending.find_all(['div', 'article'], class_=re.compile(r'item', re.I))
                
                for item in product_items[:limit]:
                    product = self._parse_product_item(item)
                    if product:
                        products.append(product)
            
            return ScraperResult(
                success=True,
                data=products[:limit],
                metadata={"type": "trending", "limit": limit}
            )
            
        except Exception as e:
            return ScraperResult(
                success=False,
                errors=[str(e)],
                metadata={"type": "trending"}
            )
    
    def convert_to_startups(self, products: List[Dict[str, Any]]) -> List[GlobalStartup]:
        """
        Convert Product Hunt products to GlobalStartup format.
        
        Args:
            products: List of product data
            
        Returns:
            List of GlobalStartup objects
        """
        startups = []
        
        for product in products:
            try:
                startup = create_global_startup(
                    name=product.get('name', 'Unknown'),
                    description=product.get('tagline', '') or product.get('description', ''),
                    source=StartupSource.PRODUCT_HUNT,
                    short_description=product.get('tagline', '')[:200],
                    tags=product.get('topics', []),
                    website=product.get('website'),
                    source_id=product.get('url', '').split('/')[-1] if product.get('url') else None,
                    product_hunt_url=product.get('url'),
                    launch_date=datetime.fromisoformat(product.get('published_at', '')) 
                               if product.get('published_at') else None,
                    upvotes=product.get('upvotes'),
                )
                startups.append(startup)
            except Exception as e:
                logger.warning(f"Failed to convert product {product.get('name')}: {str(e)}")
                continue
        
        return startups


def create_product_hunt_scraper(**kwargs) -> ProductHuntScraper:
    """
    Factory function to create ProductHuntScraper.
    
    Args:
        **kwargs: Scraper configuration
        
    Returns:
        ProductHuntScraper instance
    """
    return ProductHuntScraper(**kwargs)
