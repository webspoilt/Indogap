"""
Y Combinator Scraper for IndoGap - AI-Powered Opportunity Discovery Engine

This module provides functionality to scrape company data from Y Combinator's
public directory, extracting batch information, company details, and metadata.
"""
import re
import time
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, ScraperResult, ScraperError, create_scraper
from mini_services.models.startup import GlobalStartup, create_global_startup, StartupSource
from mini_services.config import get_settings

logger = logging.getLogger(__name__)


class YCombinatorScraper(BaseScraper):
    """
    Scraper for Y Combinator company data.
    
    Extracts information from:
    - YC Companies Directory: https://www.ycombinator.com/companies
    - Individual company pages
    
    Data extracted includes:
    - Company name and description
    - Batch information (W24, S25, etc.)
    - Tags and industries
    - Website URL
    - Company URL on YC
    """
    
    def __init__(
        self,
        delay: float = None,
        timeout: int = None,
        max_retries: int = None,
        headless: bool = True,
    ):
        """
        Initialize YC scraper.
        
        Args:
            delay: Delay between requests (uses config default if None)
            timeout: Request timeout (uses config default if None)
            max_retries: Maximum retry attempts (uses config default if None)
            headless: Use simple HTTP requests (False enables JavaScript rendering)
        """
        settings = get_settings()
        
        super().__init__(
            name="yc_scraper",
            base_url="https://www.ycombinator.com",
            delay=delay or settings.yc_scrape_delay,
            timeout=timeout or settings.request_timeout,
            max_retries=max_retries or settings.max_retries,
        )
        
        self.headless = headless
        self.companies_url = f"{self.base_url}/companies"
        
    def scrape(
        self,
        batch: Optional[str] = None,
        limit: Optional[int] = None,
        include_details: bool = False,
    ) -> ScraperResult:
        """
        Scrape YC company data.
        
        Args:
            batch: Specific batch to scrape (e.g., "W24", "S25")
            limit: Maximum number of companies to scrape
            include_details: Fetch detailed company page info
            
        Returns:
            ScraperResult with list of GlobalStartup objects
        """
        logger.info(f"Starting YC scrape for batch: {batch or 'all'}")
        
        result = ScraperResult(success=False)
        
        try:
            # Build URL with batch filter if specified
            url = self.companies_url
            if batch:
                url = f"{self.companies_url}?batch={batch}"
            
            # Make request
            response = self._make_request(url)
            
            # Parse companies
            companies = self.parse_response(response)
            
            # Validate and clean
            companies = self.validate_data(companies)
            
            # Enrich with detailed info if requested
            if include_details and companies:
                companies = self._enrich_companies(companies, limit=limit)
            
            # Convert to GlobalStartup objects
            startups = self._convert_to_startups(companies, batch=batch)
            
            result.success = True
            result.data = [s.to_dict() for s in startups]
            result.metadata = {
                "batch": batch,
                "total_scraped": len(startups),
                "include_details": include_details,
            }
            
            logger.info(f"Successfully scraped {len(startups)} companies from YC")
            
        except ScraperError as e:
            logger.error(f"YC scrape failed: {e.message}")
            result.add_error(e.message)
            
        except Exception as e:
            logger.error(f"Unexpected error during YC scrape: {str(e)}")
            result.add_error(str(e))
        
        return result
    
    def parse_response(self, response: httpx.Response) -> List[Dict[str, Any]]:
        """
        Parse YC companies page response.
        
        Args:
            response: HTTP response from YC companies page
            
        Returns:
            List of company data dictionaries
        """
        soup = BeautifulSoup(response.text, 'lxml')
        companies = []
        
        # YC uses different HTML structures across time
        # Try multiple selectors to find company cards
        
        # Method 1: Look for company cards in the listing
        company_cards = soup.find_all('div', class_=re.compile(r'company', re.I))
        
        if not company_cards:
            # Method 2: Look for links to company pages
            company_links = soup.find_all('a', href=re.compile(r'/companies/'))
            
            for link in company_links:
                company_data = self._extract_from_link(link, soup)
                if company_data:
                    companies.append(company_data)
        
        if not companies:
            # Method 3: Parse page structure directly
            companies = self._parse_page_structure(soup)
        
        # If still no companies, log warning
        if not companies:
            logger.warning("No companies found with standard selectors, trying fallback")
            companies = self._fallback_parse(soup)
        
        return companies
    
    def _extract_from_link(
        self,
        link: 'BeautifulSoup.Element',
        soup: BeautifulSoup
    ) -> Optional[Dict[str, Any]]:
        """Extract company data from a link element"""
        try:
            # Navigate to parent container
            parent = link.find_parent('div')
            if not parent:
                return None
            
            company_data = {
                'name': link.get_text(strip=True),
                'yc_url': f"{self.base_url}{link.get('href', '')}",
                'description': '',
                'tags': [],
                'batch': '',
            }
            
            # Try to find description nearby
            desc_elem = parent.find('p') or parent.find('div', class_=re.compile(r'desc', re.I))
            if desc_elem:
                company_data['description'] = desc_elem.get_text(strip=True)
            
            # Try to find tags
            tag_elems = parent.find_all(['span', 'a'], class_=re.compile(r'tag|label', re.I))
            company_data['tags'] = [t.get_text(strip=True) for t in tag_elems]
            
            return company_data
            
        except Exception:
            return None
    
    def _parse_page_structure(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse YC companies page structure"""
        companies = []
        
        # Look for the main companies container
        main_content = soup.find('main') or soup.find('div', id='content')
        if not main_content:
            return companies
        
        # Find all company entries
        # YC structure varies, so we try multiple patterns
        company_sections = main_content.find_all(['div', 'section', 'article'])
        
        for section in company_sections:
            company_data = self._extract_from_section(section)
            if company_data and company_data.get('name'):
                companies.append(company_data)
        
        return companies
    
    def _extract_from_section(self, section: 'BeautifulSoup.Element') -> Optional[Dict[str, Any]]:
        """Extract company data from a section element"""
        try:
            # Look for company name in headings
            heading = section.find(['h2', 'h3', 'h4'])
            if not heading:
                return None
            
            name = heading.get_text(strip=True)
            if not name or len(name) > 200:
                return None
            
            company_data = {
                'name': name,
                'yc_url': '',
                'description': '',
                'tags': [],
                'batch': '',
            }
            
            # Find YC URL
            link = section.find('a', href=re.compile(r'/companies/'))
            if link:
                href = link.get('href', '')
                company_data['yc_url'] = f"{self.base_url}{href}"
            
            # Find description
            desc_elem = section.find('p')
            if desc_elem:
                company_data['description'] = desc_elem.get_text(strip=True)
            
            # Find tags
            tag_elems = section.find_all(['span', 'a'], class_=re.compile(r'tag', re.I))
            company_data['tags'] = [t.get_text(strip=True) for t in tag_elems]
            
            return company_data
            
        except Exception:
            return None
    
    def _fallback_parse(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Fallback parsing when standard methods fail.
        
        Uses text pattern matching to find company information.
        """
        companies = []
        text = soup.get_text()
        
        # Look for company name patterns
        # YC companies typically have names in headings
        headings = soup.find_all(['h1', 'h2', 'h3'])
        
        for heading in headings:
            name = heading.get_text(strip=True)
            # Filter out non-company names
            if self._is_likely_company_name(name):
                company_data = {
                    'name': name,
                    'yc_url': '',
                    'description': '',
                    'tags': [],
                    'batch': self._extract_batch_from_page(soup),
                }
                companies.append(company_data)
        
        return companies
    
    def _is_likely_company_name(self, name: str) -> bool:
        """Check if text looks like a company name"""
        if not name or len(name) < 2 or len(name) > 100:
            return False
        
        # Skip common non-company text
        skip_words = [
            'y combinator', 'companies', 'startups', 'batch', 'about',
            'contact', 'privacy', 'terms', 'faq', 'help'
        ]
        
        name_lower = name.lower()
        for word in skip_words:
            if word in name_lower:
                return False
        
        # Company names typically don't contain spaces at the beginning/end
        if name != name.strip():
            return False
        
        # Should have at least one letter
        if not re.search(r'[a-zA-Z]', name):
            return False
        
        return True
    
    def _extract_batch_from_page(self, soup: BeautifulSoup) -> str:
        """Extract batch information from page"""
        # Look for batch indicators in the page
        batch_patterns = [
            r'(W|S|F)\d{2}',  # W24, S25, F23
        ]
        
        text = soup.get_text()
        for pattern in batch_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group()
        
        return ''
    
    def _enrich_companies(
        self,
        companies: List[Dict[str, Any]],
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Enrich company data with detailed information.
        
        Fetches individual company pages to get more details.
        
        Args:
            companies: List of company data
            limit: Maximum companies to enrich
            
        Returns:
            Enriched company data
        """
        if limit:
            companies = companies[:limit]
        
        enriched = []
        
        for idx, company in enumerate(companies):
            logger.info(f"Enriching company {idx+1}/{len(companies)}: {company.get('name', 'Unknown')}")
            
            try:
                if company.get('yc_url'):
                    details = self._fetch_company_details(company['yc_url'])
                    if details:
                        company.update(details)
                        
                enriched.append(company)
                
                # Respect rate limiting
                time.sleep(self.delay)
                
            except Exception as e:
                logger.warning(f"Failed to enrich {company.get('name')}: {str(e)}")
                enriched.append(company)
        
        return enriched
    
    def _fetch_company_details(self, company_url: str) -> Dict[str, Any]:
        """
        Fetch detailed company information from YC page.
        
        Args:
            company_url: URL to YC company page
            
        Returns:
            Dictionary with additional company details
        """
        try:
            response = self._make_request(company_url)
            soup = BeautifulSoup(response.text, 'lxml')
            
            details = {}
            
            # Extract long description
            desc_elem = soup.find('div', class_=re.compile(r'desc', re.I))
            if desc_elem:
                details['long_description'] = desc_elem.get_text(strip=True)
            
            # Extract external website
            # Look for links that are not YC internal links
            website_links = soup.find_all('a', href=re.compile(r'^https?://'))
            for link in website_links:
                href = link.get('href', '')
                # Skip YC, social media, and common footer links
                if 'ycombinator.com' not in href and \
                   'twitter.com' not in href and \
                   'linkedin.com' not in href and \
                   'facebook.com' not in href and \
                   'instagram.com' not in href:
                    details['website'] = href
                    break
            
            # Extract additional metadata
            meta_elems = soup.find_all(['meta', 'span', 'div'], 
                                       class_=re.compile(r'meta|info', re.I))
            for elem in meta_elems:
                text = elem.get_text(strip=True)
                if 'founded' in text.lower():
                    details['founded'] = text
                elif 'team' in text.lower():
                    details['team_size'] = text
            
            return details
            
        except Exception:
            return {}
    
    def _convert_to_startups(
        self,
        companies: List[Dict[str, Any]],
        batch: Optional[str] = None
    ) -> List[GlobalStartup]:
        """
        Convert scraped data to GlobalStartup objects.
        
        Args:
            companies: List of company data dictionaries
            batch: Batch to assign (if not in data)
            
        Returns:
            List of GlobalStartup objects
        """
        startups = []
        
        for company in companies:
            try:
                startup = create_global_startup(
                    name=company.get('name', 'Unknown'),
                    description=company.get('description', ''),
                    source=StartupSource.Y_COMBINATOR,
                    short_description=company.get('description', ''),
                    tags=company.get('tags', []),
                    website=company.get('website'),
                    batch=batch or company.get('batch'),
                    source_id=company.get('yc_url', '').split('/')[-1] if company.get('yc_url') else None,
                    yc_url=company.get('yc_url'),
                )
                startups.append(startup)
            except Exception as e:
                logger.warning(f"Failed to create startup from {company.get('name')}: {str(e)}")
                continue
        
        return startups
    
    def get_available_batches(self) -> List[str]:
        """
        Get list of available YC batches.
        
        Returns:
            List of batch codes (e.g., ['W24', 'S25', 'W23', ...])
        """
        try:
            response = self._make_request(self.companies_url)
            soup = BeautifulSoup(response.text, 'lxml')
            
            batches = set()
            
            # Look for batch filter options
            batch_select = soup.find('select', id='batch')
            if batch_select:
                options = batch_select.find_all('option')
                for option in options:
                    value = option.get('value', '')
                    if re.match(r'^[WSF]\d{2}$', value):
                        batches.add(value)
            
            # Also look for batch links in the page
            batch_links = soup.find_all('a', href=re.compile(r'batch='))
            for link in batch_links:
                href = link.get('href', '')
                match = re.search(r'batch=([WSF]\d{2})', href)
                if match:
                    batches.add(match.group(1))
            
            return sorted(batches, key=self._batch_sort_key, reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to get batches: {str(e)}")
            return []
    
    def _batch_sort_key(self, batch: str) -> tuple:
        """Generate sort key for batch codes"""
        # Sort by season (W > S > F) then by year
        season_order = {'W': 0, 'S': 1, 'F': 2}
        match = re.match(r'([WSF])(\d{2})', batch)
        if match:
            season = match.group(1)
            year = int(match.group(2))
            return (-year, season_order.get(season, 0))
        return (0, 0)
    
    def scrape_batch_range(
        self,
        start_batch: str = "W20",
        end_batch: str = "W24",
        **kwargs
    ) -> ScraperResult:
        """
        Scrape multiple consecutive batches.
        
        Args:
            start_batch: Starting batch code
            end_batch: Ending batch code
            **kwargs: Additional scrape parameters
            
        Returns:
            Combined ScraperResult for all batches
        """
        all_companies = []
        all_errors = []
        total_scraped = 0
        
        # Get all available batches
        available_batches = self.get_available_batches()
        
        # Filter to requested range
        in_range = False
        target_batches = []
        
        for batch in available_batches:
            if batch == start_batch:
                in_range = True
            if in_range:
                target_batches.append(batch)
            if batch == end_batch:
                break
        
        if not target_batches:
            # If range not found, use recent batches
            target_batches = available_batches[:5]
        
        logger.info(f"Scraping batches: {target_batches}")
        
        for batch in target_batches:
            result = self.scrape(batch=batch, **kwargs)
            
            if result.success and result.data:
                all_companies.extend(result.data)
                total_scraped += result.count
            
            all_errors.extend(result.errors)
        
        return ScraperResult(
            success=len(all_errors) == 0,
            data=all_companies if all_companies else None,
            errors=all_errors,
            metadata={
                "batches_scraped": target_batches,
                "total_companies": total_scraped,
            }
        )


def create_yc_scraper(**kwargs) -> YCombinatorScraper:
    """
    Factory function to create YCombinatorScraper.
    
    Args:
        **kwargs: Scraper configuration
        
    Returns:
        YCombinatorScraper instance
    """
    return YCombinatorScraper(**kwargs)
