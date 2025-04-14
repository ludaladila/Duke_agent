from langchain.tools import BaseTool
from typing import Optional, Type
from pydantic import BaseModel
from bs4 import BeautifulSoup
import requests
import json

class WebScrapeInput(BaseModel):
    url: str

class GeneralWebScraper(BaseTool):
    name: str = "general_web_scraper"
    description: str = (
       "Scrapes the content of a web page. Provide a full URL. "
        "Returns title, text from paragraphs, and visible links."
    )
    args_schema: Type[BaseModel] = WebScrapeInput

    def _run(self, url: str) -> str:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; LangChainScraper/2.0)"}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # Title
            title = soup.title.get_text(strip=True) if soup.title else "No title"

            # Headings
            # Headings: Extract h1, h2, h3 text
            headings = {
            tag: [h.get_text(strip=True) for h in soup.find_all(tag)]
                for tag in ["h1", "h2", "h3"]
            }


            # Paragraphs
            paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]

            # Lists
            list_items = [li.get_text(strip=True) for li in soup.find_all("li")]

            # Tables (first 2 tables only)
            tables = []
            for table in soup.find_all("table")[:2]:
                rows = []
                for tr in table.find_all("tr"):
                    cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                    if cells:
                        rows.append(cells)
                if rows:
                    tables.append(rows)

            # Links
            links = [
                {"text": a.get_text(strip=True), "href": a.get("href")}
                for a in soup.find_all("a")
                if a.get("href") and a.get_text(strip=True)
            ]

            return json.dumps({
                "title": title,
                "headings": headings,
                "paragraphs": paragraphs[:20], 
                "lists": list_items[:20],
                "tables": tables,
                "links": links[:20]
            }, ensure_ascii=False, indent=2)

        except Exception as e:
            return f"Failed to scrape {url}: {e}"

if __name__ == "__main__":
    tool = GeneralWebScraper()
    url = "https://masters.pratt.duke.edu/"
    result = tool._run(url)
    print(result)