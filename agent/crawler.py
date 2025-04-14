import requests
from bs4 import BeautifulSoup
import time
import random
import re
import json
import os
from urllib.parse import urljoin, urlparse

class HumanLikeWebExplorer:
    def __init__(self, max_depth=2, max_pages_per_level=3, delay_range=(1, 3)):
        """
        Initialize the human-like web explorer
        
        Parameters:
            max_depth: Maximum exploration depth
            max_pages_per_level: Maximum pages to explore per level
            delay_range: Delay range between requests in seconds, simulating human reading time
        """
        self.max_depth = max_depth
        self.max_pages_per_level = max_pages_per_level
        self.delay_range = delay_range
        self.visited_urls = set()
        self.content_store = {}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml",
            "Accept-Language": "en-US,en;q=0.9"
        }
    
    def is_relevant_url(self, url, base_domain):
        """Determine if a URL is relevant and worth visiting"""
        # Ensure the link is on the same domain
        if not urlparse(url).netloc.endswith(base_domain):
            return False
        
        # Avoid non-HTML content
        if re.search(r'\.(pdf|jpg|jpeg|png|gif|doc|docx|ppt|pptx|xls|xlsx|zip|rar)$', url.lower()):
            return False
            
        # Avoid irrelevant pages (can be customized for AIPI project)
        irrelevant_patterns = [
            '/login', '/signup', '/cart', '/search', 
            '/privacy-policy', '/terms-of-service'
        ]
        if any(pattern in url.lower() for pattern in irrelevant_patterns):
            return False
            
        return True
    
    def extract_content(self, url, soup):
        """Extract structured content from the page"""
        title = soup.title.string.strip() if soup.title else "No Title"
        
        # Find the main content area
        main_content = (
            soup.find("main") or 
            soup.find("article") or 
            soup.find("div", class_="content-area") or 
            soup.find("div", class_="entry-content") or
            soup.body
        )
        
        if main_content:
            # Clean up irrelevant content
            for tag in main_content(["script", "style", "nav", "footer", "aside"]):
                tag.decompose()
                
            # Extract content structure, simulating human understanding process
            content = {
                "url": url,
                "title": title,
                "headings": self._extract_headings(main_content),
                "paragraphs": [p.get_text(strip=True) for p in main_content.find_all('p') if p.get_text(strip=True)],
                "lists": self._extract_lists(main_content),
                "main_text": main_content.get_text(separator="\n", strip=True),
                "interesting_links": self._find_interesting_links(soup, url)
            }
            
            return content
        else:
            return {
                "url": url,
                "title": title,
                "main_text": soup.get_text(separator="\n", strip=True) if soup.body else "",
                "interesting_links": self._find_interesting_links(soup, url)
            }
    
    def _extract_headings(self, content):
        """Extract page heading hierarchy, simulating human understanding of page structure"""
        headings = []
        for h in content.find_all(['h1', 'h2', 'h3', 'h4']):
            headings.append({
                'level': int(h.name[1]),
                'text': h.get_text(strip=True)
            })
        return headings
    
    def _extract_lists(self, content):
        """Extract lists from the page"""
        lists = []
        for ul in content.find_all(['ul', 'ol']):
            items = [li.get_text(strip=True) for li in ul.find_all('li')]
            if items:  # Only add non-empty lists
                lists.append(items)
        return lists
    
    def _find_interesting_links(self, soup, current_url):
        """
        Find interesting links in the page, simulating human points of interest
        Prioritize content-relevant, descriptive links
        """
        links = []
        base_url = current_url
        base_domain = urlparse(current_url).netloc
        
        # Prioritize links in the main navigation
        nav_links = soup.find("nav")
        if nav_links:
            for a in nav_links.find_all("a", href=True):
                url = urljoin(base_url, a["href"])
                if self.is_relevant_url(url, base_domain):
                    links.append({
                        "url": url,
                        "text": a.get_text(strip=True),
                        "source": "navigation",
                        "priority": 1
                    })
        
        # Look for other links in the page
        for a in soup.find_all("a", href=True):
            if len(a.get_text(strip=True)) > 5:  # Links with substantial text are more likely important
                url = urljoin(base_url, a["href"])
                if self.is_relevant_url(url, base_domain) and url not in [l["url"] for l in links]:
                    # Analyze link text relevance
                    text = a.get_text(strip=True)
                    priority = 2
                    
                    # Education-related keywords increase priority
                    edu_keywords = ['course', 'program', 'degree', 'faculty', 'research', 
                                   'admission', 'application', 'student', 'certificate',
                                   'AIPI', 'AI', 'engineering', 'master']
                    if any(keyword.lower() in text.lower() for keyword in edu_keywords):
                        priority = 0
                    
                    links.append({
                        "url": url,
                        "text": text,
                        "source": "content",
                        "priority": priority
                    })
        
        # Sort by priority
        return sorted(links, key=lambda x: x["priority"])
    
    def explore_from_categories(self, url_groups):
        """
        Start exploration from categorized starting links
        """
        results_by_category = {}
        
        for category, urls in url_groups.items():
            print(f"\nStarting exploration for category: {category}")
            results_by_category[category] = {}
            
            for start_url in urls:
                # Skip already visited URLs
                if start_url in self.visited_urls:
                    print(f"Skipping already visited URL: {start_url}")
                    continue
                    
                print(f"\nStarting exploration from link: {start_url}")
                base_domain = urlparse(start_url).netloc
                queue = [(start_url, 0)]  # (url, depth)
                
                while queue:
                    current_url, depth = queue.pop(0)
                    
                    if current_url in self.visited_urls:
                        continue
                        
                    if depth > self.max_depth:
                        continue
                        
                    print(f"Exploring page (depth {depth}): {current_url}")
                    
                    try:
                        # Simulate human behavior: add random delay between requests
                        wait_time = random.uniform(*self.delay_range)
                        time.sleep(wait_time)
                        
                        # Get the page
                        response = requests.get(current_url, headers=self.headers, timeout=10)
                        response.raise_for_status()
                        
                        soup = BeautifulSoup(response.text, "html.parser")
                        
                        # Extract content and store
                        content = self.extract_content(current_url, soup)
                        self.content_store[current_url] = content
                        results_by_category[category][current_url] = content
                        self.visited_urls.add(current_url)
                        
                        # If not at max depth, collect links for the next layer
                        if depth < self.max_depth:
                            # Simulate human thinking: check the current page, select the most relevant links to continue exploring
                            links_count = len(content['interesting_links'])
                            print(f"  Found {links_count} interesting links on this page")
                            
                            # Calculate how many pages have already been added at this level
                            pages_at_next_level = sum(1 for _, d in queue if d == depth + 1)
                            
                            # Only add a limited number of pages to the next layer
                            remaining_slots = self.max_pages_per_level - pages_at_next_level
                            
                            if remaining_slots > 0:
                                for i, link in enumerate(content['interesting_links']):
                                    if i >= remaining_slots:
                                        break
                                        
                                    if link["url"] not in self.visited_urls:
                                        print(f"  - Planning to explore: {link['text']} ({link['url']})")
                                        queue.append((link["url"], depth + 1))
                    
                    except Exception as e:
                        print(f"Error visiting {current_url}: {e}")
        
        print(f"\nExploration complete! Visited {len(self.visited_urls)} pages in total")
        return results_by_category
    def save_results(self, results_by_category, output_dir="output"):
        """Save results to files"""
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
    
        # Save results for each category
        for category, results in results_by_category.items():
            # Create category directory
            category_dir = os.path.join(output_dir, category)
            os.makedirs(category_dir, exist_ok=True)

            # Save each page's full JSON content
            for url, content in results.items():
                # Create a safe filename based on URL
                filename = re.sub(r'[^\w]', '_', url) + '.json'
                filepath = os.path.join(category_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(content, f, ensure_ascii=False, indent=2)

            
            category_text = []
            for url, content in results.items():
                category_text.append(f"URL: {url}")
                category_text.append(f"Title: {content['title']}")

                
                if 'headings' in content and content['headings']:
                    category_text.append("Headings:")
                    for heading in content['headings']:
                        prefix = "  " * (heading['level'] - 1)
                        category_text.append(f"{prefix}- {heading['text']}")

             
                if 'paragraphs' in content and content['paragraphs']:
                    category_text.append("Paragraphs:")
                    
                    for p in content['paragraphs']:
                        category_text.append(p)
                        category_text.append("")

               
                if 'lists' in content and content['lists']:
                    category_text.append("Lists:")
                    for lst in content['lists']:
                        
                        category_text.append(", ".join(lst))
                        category_text.append("")

               
                if 'main_text' in content and content['main_text']:
                    category_text.append("Main Text:")
                    category_text.append(content['main_text'])

                category_text.append("\n" + "-"*50 + "\n")

          
            summary_filepath = os.path.join(output_dir, f"{category}_summary.txt")
            with open(summary_filepath, 'w', encoding='utf-8') as f:
                f.write("\n".join(category_text))


        index = {}
        for category, results in results_by_category.items():
            index[category] = list(results.keys())
        with open(os.path.join(output_dir, "index.json"), 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

        print(f"Results saved to directory {output_dir}")


if __name__ == "__main__":
    # Organize links by category
    url_groups = {
        "Program Overview": [
            "https://masters.pratt.duke.edu/ai/",
            "https://masters.pratt.duke.edu/ai/overview/",
            "https://masters.pratt.duke.edu/ai/info/"
        ],
        "Degree and Course Information": [
            "https://masters.pratt.duke.edu/programs/",
            "https://masters.pratt.duke.edu/programs/options/",
            "https://masters.pratt.duke.edu/programs/degree-requirements/",
            "https://masters.pratt.duke.edu/ai/degree/",
            "https://masters.pratt.duke.edu/ai/degree/#compare-online-and-on-campus",
            "https://masters.pratt.duke.edu/programs/certificates/",
            "https://masters.pratt.duke.edu/ai/certificate/",
            "https://masters.pratt.duke.edu/ai/courses/"
        ],
        "Admissions and Application": [
            "https://masters.pratt.duke.edu/admissions/",
            "https://masters.pratt.duke.edu/apply",
            "https://masters.pratt.duke.edu/apply/",
            "https://masters.pratt.duke.edu/admissions/admitted/",
            "https://masters.pratt.duke.edu/admissions/tuition-financial-aid/"
        ],
        "Faculty and Leadership": [
            "https://masters.pratt.duke.edu/ai/leadership-staff/",
            "https://masters.pratt.duke.edu/people/",
            "https://masters.pratt.duke.edu/people?s=&department=artificial-intelligence&group=faculty&submit=Filter"
        ],
        "Student Resources and Life": [
            "https://masters.pratt.duke.edu/life/students/",
            "https://masters.pratt.duke.edu/life/career-services/",
            "https://masters.pratt.duke.edu/life/"
        ],
        "Industry and Employer Relations": [
            "https://masters.pratt.duke.edu/industry/"
        ]
    }
    
    # Initialize explorer
    explorer = HumanLikeWebExplorer(
        max_depth=1,  # Only go one level deep from known links
        max_pages_per_level=2,  # Explore at most 2 pages per level
        delay_range=(1, 3)  # Delay 1-3 seconds between requests
    )
    
    # Start exploration
    results = explorer.explore_from_categories(url_groups)
    
    # Save results
    explorer.save_results(results, "duke_aipi_data")