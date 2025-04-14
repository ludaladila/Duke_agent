import requests
from bs4 import BeautifulSoup
import json

def extract_leadership_staff_info(html):
    soup = BeautifulSoup(html, 'html.parser')
    results = []

    # Iterate over all staff info blocks
    for article in soup.find_all("article", class_="faculty-overview"):
        # Extract name
        h3 = article.find("h3")
        if h3:
            a_tag = h3.find("a")
            name = a_tag.get_text(strip=True) if a_tag else h3.get_text(strip=True)
        else:
            name = ""

        # Extract email
        email_tag = article.find("a", class_="faculty-overview__email")
        email = email_tag.get_text(strip=True) if email_tag else ""

        # Extract description (e.g. title, department)
        p_tag = article.find("p")
        description = p_tag.get_text(strip=True) if p_tag else ""

        results.append({
            "name": name,
            "email": email,
            "description": description
        })

    return results

def leadership_staff_agent_tool(_):
    url = "https://masters.pratt.duke.edu/people?s=&department=artificial-intelligence&group=faculty&submit=Filter"
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/115.0.0.0 Safari/537.36")
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as err:
        return f"Error fetching {url}: {err}"

    staff_info = extract_leadership_staff_info(response.text)
    return json.dumps(staff_info, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    data = leadership_staff_agent_tool(None)
    print(data)
