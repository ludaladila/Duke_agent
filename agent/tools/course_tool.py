from langchain.tools import BaseTool
from typing import Optional, Type, Any, List, Dict
from pydantic import BaseModel, Field
import requests
from bs4 import BeautifulSoup
import re
import time
import json

# Pre-compile the regular expression once for performance.
COURSE_REGEX = re.compile(r'([A-Z]+\s*\d+(?:\.\d+)?(?:\s*D?)?):\s*(.*)')

class CourseToolInput(BaseModel):
    """
    Input model for the course tool.
    
    query: The search query or request type.
           Can be "summary" for all courses summary, 
           a specific course code (e.g. "AIPI 540"), 
           or a search term (e.g. "machine learning").
    """
    query: str = Field(description="Course code, search term, or 'summary' for all courses")

class CourseInfoTool(BaseTool):
    """A tool for accessing information about Duke University's AI courses.
    
    This tool can provide a summary of all courses, details about specific courses by code,
    or search for courses by keyword.
    """
    
    name: str = "duke_ai_course_info"
    description: str = (
        "Provides information about Duke University's AI courses. You can:\n"
        "1. Get a summary of all courses by querying 'summary'\n"
        "2. Get details about a specific course by providing its code (e.g., 'AIPI 540')\n"
        "3. Search for courses containing a keyword (e.g., 'machine learning', 'deep')"
    )
    args_schema: Type[BaseModel] = CourseToolInput

    _cache: Any = None
    _cache_time: Optional[float] = None
    _cache_expiry: int = 3600  # Cache for one hour

    def _run(self, query: str) -> str:
        """
        Processes the user's query and returns appropriate course information.
        
        Args:
            query: Can be "summary" for all courses, a course code (e.g., "AIPI 540"),
                  or a search term (e.g., "machine learning")
        
        Returns:
            Formatted course information based on the query.
        """
        # First, ensure we have the course data (either from cache or by fetching it)
        course_data = self._get_course_data()
        
        # If there was an error fetching the data
        if isinstance(course_data, str) and course_data.startswith("Failed to scrape"):
            return course_data
            
        # Process based on query type
        if query.lower() == "summary":
            # Return a summary of all courses
            return self._generate_summary(course_data)
            
        elif re.match(r'^[A-Z]+\s*\d+', query):
            # This looks like a course code query
            return self._get_course_by_code(course_data, query)
            
        else:
            # This is a search term
            return self._search_courses(course_data, query)

    def _get_course_data(self) -> Dict:
        """
        Gets course data from cache or by scraping the webpage.
        Returns a dictionary of course data or an error message.
        """
        current_time = time.time()
        if self._cache and self._cache_time and (current_time - self._cache_time) < self._cache_expiry:
            return self._cache
            
        url = "https://masters.pratt.duke.edu/ai/courses/"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; AIPIWebScraper/1.0)"}
    
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            course_data = {
                "categories": {},
                "courses_by_code": {}
            }
            
            # Scrape each section representing a course category.
            sections = soup.find_all("section", class_="stripe-accordions")
            for section in sections:
                category_elem = section.find("h2")
                if not category_elem:
                    continue
                category_title = category_elem.get_text(strip=True)
                course_data["categories"][category_title] = []
                
                # Each course is contained in an <li> with class "accordion".
                accordion_items = section.find_all("li", class_="accordion")
                for item in accordion_items:
                    title_elem = item.find("h3", class_="title--small")
                    if not title_elem:
                        continue
                    course_title = title_elem.get_text(strip=True)
                    
                    # Get course description.
                    desc_elem = item.find("div", class_="accordion__text")
                    course_description = desc_elem.get_text(strip=True) if desc_elem else ""
                    
                    # Parse course code and name.
                    code_match = COURSE_REGEX.match(course_title)
                    if code_match:
                        course_code = code_match.group(1).strip()
                        course_name = code_match.group(2).strip()
                    else:
                        course_code = ""
                        course_name = course_title
                        
                    course_info = {
                        "code": course_code,
                        "name": course_name,
                        "description": course_description,
                        "category": category_title
                    }
                    
                    course_data["categories"][category_title].append(course_info)
                    if course_code:
                        course_data["courses_by_code"][course_code] = course_info
            
            course_data["total_courses"] = len(course_data["courses_by_code"])
            course_data["total_categories"] = len(course_data["categories"])
            
            # Cache the result
            self._cache = course_data
            self._cache_time = current_time
            
            return course_data
            
        except Exception as e:
            return f"Failed to scrape the courses page: {str(e)}"

    def _generate_summary(self, course_data: Dict) -> str:
        """
        Generates a summary of all courses organized by category.
        """
        total_courses = course_data.get("total_courses", 0)
        total_categories = course_data.get("total_categories", 0)
        summary_lines = [
            f"Duke AI Program offers {total_courses} courses across {total_categories} categories:",
        ]
        
        for category, courses in course_data.get("categories", {}).items():
            summary_lines.append(f"\n## {category} ({len(courses)} courses)")
            for course in courses:
                if course['code']:  # Only include courses with codes
                    summary_lines.append(f"- {course['code']}: {course['name']}")
        
        summary_lines.append("\nTo get detailed information about a specific course, please query with the course code (e.g., 'AIPI 540').")
        return "\n".join(summary_lines)

    def _get_course_by_code(self, course_data: Dict, code: str) -> str:
        """
        Gets detailed information about a specific course by its code.
        """
        # Normalize the course code (remove extra spaces)
        normalized_code = re.sub(r'\s+', ' ', code.strip().upper())
        
        # Try to find the exact match first
        course = course_data.get("courses_by_code", {}).get(normalized_code)
        
        # If not found, try partial matching (case insensitive)
        if not course:
            for course_code, course_info in course_data.get("courses_by_code", {}).items():
                if normalized_code in course_code:
                    course = course_info
                    break
        
        if course:
            return f"""
## {course['code']}: {course['name']}

**Category:** {course['category']}

**Description:**
{course['description']}
"""
        else:
            return f"Course with code '{code}' not found. Try querying 'summary' to see all available courses."

    def _search_courses(self, course_data: Dict, query: str) -> str:
        """
        Searches for courses containing the query term in code, name, or description.
        """
        query_lower = query.lower()
        matching_courses = []
        
        for course_code, course in course_data.get("courses_by_code", {}).items():
            if (query_lower in course_code.lower() or 
                query_lower in course['name'].lower() or 
                query_lower in course['description'].lower()):
                matching_courses.append(course)
        
        if matching_courses:
            result_lines = [f"Found {len(matching_courses)} courses matching '{query}':\n"]
            
            for i, course in enumerate(matching_courses, 1):
                result_lines.append(f"{i}. {course['code']}: {course['name']}")
                result_lines.append(f"   Category: {course['category']}")
                
                # Add a brief excerpt from the description that contains the search term
                if query_lower in course['description'].lower():
                    description = course['description']
                    # Find the position of the search term
                    pos = description.lower().find(query_lower)
                    # Extract a snippet around the search term
                    start = max(0, pos - 50)
                    end = min(len(description), pos + len(query) + 100)
                    # Adjust to avoid cutting words
                    if start > 0:
                        while start > 0 and description[start] != ' ':
                            start -= 1
                    if end < len(description):
                        while end < len(description) and description[end] != ' ':
                            end += 1
                    
                    snippet = description[start:end]
                    if start > 0:
                        snippet = "..." + snippet
                    if end < len(description):
                        snippet = snippet + "..."
                    
                    result_lines.append(f"   Context: {snippet}")
                
                result_lines.append("")  # Empty line between courses
            
            result_lines.append("\nFor detailed information on a specific course, query with its course code.")
            return "\n".join(result_lines)
        else:
            return f"No courses found matching '{query}'. Try querying 'summary' to see all available courses."

if __name__ == "__main__":
    tool = CourseInfoTool()
    # Test summary
    print(tool._run("summary"))
    # Test course lookup
    print(tool._run("AIPI 540"))
    # Test search
    print(tool._run("machine learning"))