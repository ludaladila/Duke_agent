# Duke AIPI Intelligent Assistant

This is an intelligent assistant system developed based on LangChain and OpenAI GPT-4, specifically designed to answer questions about Duke University's AI Program for Innovation (AIPI). The assistant can provide comprehensive information including course details, faculty profiles, campus events, and more.

## Features

-  **AIPI Program Information**: Provides detailed information about Duke's AI Program for Innovation
-  **Course Information**: Queries detailed information about AI-related courses
-  **Faculty Information**: Retrieves information about Duke AIPI faculty members
-  **Campus Events**: Queries campus events for the next 50 days
-  **Web Scraping**: Capable of scraping information from specified URLs
-  **Smart Link Selection**: Intelligently selects relevant Pratt School webpages based on user queries

## Project Structure

```
agent/
├── tools/              # Various tool implementations
├── duke_aipi_data/     # AIPI related data
├── main.py            # Main program entry
├── crawler.py         # Web crawler implementation
└── prompt.py          # Prompt templates
```

## Installation Guide

1. Clone the repository:
```bash
git clone <https://github.com/Duke-AIPI-LLM-Course/project-2-small-ai.git>
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Unix/macOS
# or
.venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install langchain langchain-openai python-dotenv beautifulsoup4
```

4. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Set your OpenAI API key in the `.env` file:
```
OPENAI_API_KEY=your-api-key-here
DUKE_API_TOKEN=your-api-key-here
```

## Usage

1. Ensure you have completed the installation steps and activated the virtual environment

2. Run the main program:
```bash
python agent/main.py
```

3. Example query:
```python
result = process_query("Tell me about the AIPI program at Duke.")
print(result)
```

## Available Tools

1. **AIPI Program Information**  
  Provides detailed AIPI program information using Retrieval-Augmented Generation (RAG), including program details, degree options, courses, admissions requirements, etc.

2.  **Duke AI Courses**  
  Supports comprehensive inquiries into AI-related courses, including course overviews, specific course code lookups, and keyword searches.

3.  **AIPI Faculty**  
  Retrieves accurate information from Duke AIPI Engineering's faculty directory, capturing details like name, email, title, and department.

4.  **Campus Events**  
  Real-time querying of Duke University's official calendar API to fetch events over the next 50 days, with support for keyword filtering and detailed event information (title, description, date, time, location, and event URL).

5.  **Pratt Link Selector**  
  Leverages semantic matching to intelligently select relevant Pratt School web pages for quick access to important resources.

6.  **General Web Scraper**  
  Utilizes BeautifulSoup to scrape various types of web data, including page titles, paragraphs, lists, tables, and hyperlinks.

## Notes

- Ensure your OpenAI API key and DUKE API is properly set up before use
