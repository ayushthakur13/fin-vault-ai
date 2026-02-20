"""
SEC EDGAR Data Fetcher
Retrieves financial data from SEC EDGAR database with proper rate limiting and caching
"""
import time
import requests
from typing import Dict, Optional
from diskcache import Cache

from app.config import (
    SEC_HEADERS,
    SEC_COMPANY_TICKERS_URL,
    SEC_COMPANY_FACTS_URL,
    SEC_SUBMISSIONS_URL,
    REQUEST_DELAY,
    MAX_RETRIES,
    CACHE_DIR,
)


class SECDataFetcher:
    """Fetches financial data from SEC EDGAR with caching and rate limiting"""
    
    def __init__(self, cache_hours: int = 24):
        """
        Initialize SEC Data Fetcher
        
        Args:
            cache_hours: Number of hours to cache responses (default: 24)
        """
        self.cache = Cache(str(CACHE_DIR))
        self.cache_ttl = cache_hours * 3600  # Convert to seconds
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, use_cache: bool = True) -> Optional[Dict]:
        """
        Make HTTP request to SEC with retries and caching
        
        Args:
            url: URL to fetch
            use_cache: Whether to use cached response
            
        Returns:
            JSON response as dictionary or None if failed
        """
        # Check cache first
        if use_cache and url in self.cache:
            print(f"📦 Using cached data for: {url}")
            return self.cache[url]
        
        # Make request with retries
        for attempt in range(MAX_RETRIES):
            try:
                self._rate_limit()
                print(f"🌐 Fetching: {url} (attempt {attempt + 1}/{MAX_RETRIES})")
                
                response = requests.get(url, headers=SEC_HEADERS, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                # Cache successful response
                self.cache.set(url, data, expire=self.cache_ttl)
                
                return data
                
            except requests.exceptions.RequestException as e:
                print(f"⚠️  Request failed: {e}")
                if attempt == MAX_RETRIES - 1:
                    print(f"❌ Failed to fetch {url} after {MAX_RETRIES} attempts")
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def get_company_tickers(self) -> Dict[str, Dict]:
        """
        Get mapping of all company tickers to CIK numbers
        
        Returns:
            Dictionary mapping ticker to company info (cik, name)
        """
        data = self._make_request(SEC_COMPANY_TICKERS_URL)
        
        if not data:
            return {}
        
        # Restructure data for easier lookup
        ticker_map = {}
        for entry in data.values():
            ticker = entry.get("ticker", "").upper()
            if ticker:
                ticker_map[ticker] = {
                    "cik": str(entry.get("cik_str", entry.get("cik", ""))).zfill(10),
                    "name": entry.get("title", ""),
                    "exchange": entry.get("exchange", "")
                }
        
        print(f"✅ Loaded {len(ticker_map)} company tickers")
        return ticker_map
    
    def get_cik_from_ticker(self, ticker: str) -> Optional[str]:
        """
        Get CIK number for a given ticker symbol
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            
        Returns:
            CIK number as zero-padded 10-digit string, or None if not found
        """
        ticker_map = self.get_company_tickers()
        company = ticker_map.get(ticker.upper())
        
        if company:
            print(f"✅ Found {ticker.upper()}: {company['name']} (CIK: {company['cik']})")
            return company['cik']
        else:
            print(f"❌ Ticker {ticker.upper()} not found")
            return None
    
    def get_company_facts(self, cik: str) -> Optional[Dict]:
        """
        Get all financial facts for a company by CIK
        
        Args:
            cik: Company CIK number (can be with or without leading zeros)
            
        Returns:
            Dictionary containing all company financial facts
        """
        # Ensure CIK is properly formatted
        cik = str(cik).zfill(10)
        url = SEC_COMPANY_FACTS_URL.format(cik=cik)
        
        data = self._make_request(url)
        
        if data:
            print(f"✅ Retrieved financial facts for CIK {cik}")
            return data
        else:
            print(f"❌ Failed to retrieve facts for CIK {cik}")
            return None
    
    def get_company_submissions(self, cik: str) -> Optional[Dict]:
        """
        Get all SEC submissions for a company
        
        Args:
            cik: Company CIK number
            
        Returns:
            Dictionary containing submission history
        """
        cik = str(cik).zfill(10)
        url = SEC_SUBMISSIONS_URL.format(cik=cik)
        
        data = self._make_request(url)
        
        if data:
            print(f"✅ Retrieved submissions for CIK {cik}")
            return data
        else:
            print(f"❌ Failed to retrieve submissions for CIK {cik}")
            return None
    
    def get_company_data_by_ticker(self, ticker: str) -> Optional[Dict]:
        """
        Convenience method to get company facts using ticker symbol
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Company financial facts or None
        """
        cik = self.get_cik_from_ticker(ticker)
        if cik:
            return self.get_company_facts(cik)
        return None
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
        print("🗑️  Cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "volume": self.cache.volume()
        }
