from langchain.tools import BaseTool
from typing import Type, List
from pydantic import BaseModel
import json
from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()

class LinkSelectorInput(BaseModel):
    query: str

LINK_MAP = [
    {
        "title": "Apply",
        "url": "https://masters.pratt.duke.edu/apply/",
        "description": "Apply to Duke Pratt master's programs."
    },
    {
        "title": "Why Duke?",
        "url": "https://masters.pratt.duke.edu/admissions/",
        "description": "Why students choose Duke Pratt."
    },
    {
        "title": "How to Apply",
        "url": "https://masters.pratt.duke.edu/apply/",
        "description": "Step-by-step application instructions."
    },
    {
        "title": "Tuition & Financial Aid",
        "url": "https://masters.pratt.duke.edu/admissions/tuition-financial-aid/",
        "description": "Cost of attendance and financial aid options."
    },
    {
        "title": "Admitted Students",
        "url": "https://masters.pratt.duke.edu/admissions/admitted/",
        "description": "Resources and next steps for admitted students."
    },
    {
        "title": "Degree Programs",
        "url": "https://masters.pratt.duke.edu/programs/",
        "description": "Overview of available master's degree programs."
    },
    {
        "title": "Certificates & Specializations",
        "url": "https://masters.pratt.duke.edu/programs/certificates/",
        "description": "Certificate programs and academic specializations."
    },
    {
        "title": "Degree Requirements",
        "url": "https://masters.pratt.duke.edu/programs/degree-requirements/",
        "description": "Requirements to complete a Duke Pratt degree."
    },
    {
        "title": "Flexible Options",
        "url": "https://masters.pratt.duke.edu/programs/options/",
        "description": "Part-time, remote, or flexible schedule options."
    },
    {
        "title": "Life at Duke",
        "url": "https://masters.pratt.duke.edu/life/",
        "description": "Student life and resources at Duke University."
    }
]

class LLMPrattLinkSelector(BaseTool):
    name: str = "llm_pratt_link_selector"
    description: str = (
        "Use this tool to find the most relevant Pratt website link based on a user's question."
        "Uses LLM to semantically match questions to correct URLs."
    )
    args_schema: Type[BaseModel] = LinkSelectorInput
    def _run(self, query: str) -> str:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) 
        prompt = f"""
You are a helpful assistant. Based on the following user query, choose the most relevant link from the list.
User query: \"{query}\"

Here are the available links:
{json.dumps(LINK_MAP, indent=2)}

Respond with only the JSON of the best matching link from the list.
"""
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return json.dumps({"error": str(e)})

# Test 
if __name__ == "__main__":
    tool = LLMPrattLinkSelector()
    user_query = "I want to know what certificates are available."
    result = tool._run(user_query)
    print(result)