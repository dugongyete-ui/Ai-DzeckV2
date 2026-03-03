from typing import Optional
import logging
import httpx
import re
from bs4 import BeautifulSoup
from app.domain.models.tool_result import ToolResult
from app.domain.models.search import SearchResults, SearchResultItem
from app.domain.external.search import SearchEngine

logger = logging.getLogger(__name__)

class BingSearchEngine(SearchEngine):
    """Web search engine implementation using DuckDuckGo HTML (reliable, no JS required).
    
    Previously used Bing scraping, but Bing blocks server-side requests via bot detection
    and JavaScript rendering. DuckDuckGo HTML provides equivalent functionality reliably.
    """
    
    def __init__(self):
        """Initialize search engine"""
        self.base_url = "https://html.duckduckgo.com/html/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        self.cookies = httpx.Cookies()
        
    async def search(
        self, 
        query: str, 
        date_range: Optional[str] = None
    ) -> ToolResult[SearchResults]:
        """Search web pages using DuckDuckGo HTML search
        
        Args:
            query: Search query, using 3-5 keywords
            date_range: (Optional) Time range filter for search results
            
        Returns:
            Search results
        """
        params = {
            "q": query,
            "b": "",
        }
        
        if date_range and date_range != "all":
            date_mapping = {
                "past_day": "d",
                "past_week": "w",
                "past_month": "m",
                "past_year": "y",
            }
            if date_range in date_mapping:
                params["df"] = date_mapping[date_range]
        
        try:
            async with httpx.AsyncClient(
                headers=self.headers,
                cookies=self.cookies,
                timeout=30.0,
                follow_redirects=True
            ) as client:
                response = await client.post(self.base_url, data=params)
                response.raise_for_status()
                
                self.cookies.update(response.cookies)
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                search_results = []
                
                result_items = soup.find_all('div', class_='result')
                if not result_items:
                    result_items = soup.find_all('div', class_='results_links')
                
                for item in result_items:
                    try:
                        title = ""
                        link = ""
                        snippet = ""
                        
                        title_tag = item.find('a', class_='result__a')
                        if not title_tag:
                            title_tag = item.find('a', class_='result__url')
                        if not title_tag:
                            all_links = item.find_all('a', href=True)
                            for a in all_links:
                                href = a.get('href', '')
                                if href.startswith('http') and 'duckduckgo' not in href:
                                    title_tag = a
                                    break
                        
                        if title_tag:
                            title = title_tag.get_text(strip=True)
                            link = title_tag.get('href', '')
                            if link.startswith('//duckduckgo.com/l/?uddg='):
                                import urllib.parse
                                parsed = urllib.parse.urlparse(link)
                                qs = urllib.parse.parse_qs(parsed.query)
                                link = qs.get('uddg', [link])[0]
                            elif not link.startswith('http'):
                                link = 'https://duckduckgo.com' + link
                        
                        if not title:
                            continue
                        
                        snippet_tag = item.find('a', class_='result__snippet')
                        if not snippet_tag:
                            snippet_tag = item.find('div', class_='result__snippet')
                        if snippet_tag:
                            snippet = snippet_tag.get_text(strip=True)
                        
                        if not snippet:
                            all_text = item.get_text(separator=' ', strip=True)
                            sentences = re.split(r'[.!?\n]', all_text)
                            for sentence in sentences:
                                clean = sentence.strip()
                                if len(clean) > 30 and clean != title:
                                    snippet = clean
                                    break
                        
                        is_ad = 'duckduckgo.com/y.js' in link or 'duckduckgo.com/l/?rut=' in link
                        if title and link and link.startswith('http') and not is_ad:
                            search_results.append(SearchResultItem(
                                title=title,
                                link=link,
                                snippet=snippet
                            ))
                    except Exception as e:
                        logger.warning(f"Failed to parse search result: {e}")
                        continue
                
                results = SearchResults(
                    query=query,
                    date_range=date_range,
                    total_results=len(search_results),
                    results=search_results
                )
                
                logger.info(f"Search for '{query}' returned {len(search_results)} results")
                return ToolResult(success=True, data=results)
                
        except Exception as e:
            logger.error(f"Search failed: {e}")
            error_results = SearchResults(
                query=query,
                date_range=date_range,
                total_results=0,
                results=[]
            )
            return ToolResult(
                success=False,
                message=f"Search failed: {e}",
                data=error_results
            )


if __name__ == "__main__":
    import asyncio
    
    async def test():
        engine = BingSearchEngine()
        result = await engine.search("Latest AI tools 2026")
        
        if result.success:
            print(f"Search successful! Found {len(result.data.results)} results")
            for i, item in enumerate(result.data.results[:3]):
                print(f"{i+1}. {item.title}")
                print(f"   {item.link}")
                print(f"   {item.snippet[:100]}")
                print()
        else:
            print(f"Search failed: {result.message}")
    
    asyncio.run(test())
