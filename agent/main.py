# Import the existing tools and modules
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from tools.pratt_tool import LLMPrattLinkSelector
from tools.webscrape_tool import GeneralWebScraper
from tools.duke_event_tool import search_campus_events
from tools.AIPI_faculty_tool import leadership_staff_agent_tool
from tools.course_tool import CourseInfoTool
# Import the new AIPI RAG tool
from tools.AIPI_rag_tool import aipi_rag_tool

# Import prompt template
from prompt import AGENT_PROMPT_TEMPLATE

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if API key is available
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not found. Please make sure it's set in your .env file or environment variables.")

# Initialize the LLM
llm = ChatOpenAI(
    model="gpt-4",
    temperature=0,
    api_key=api_key
)

# Create memory for conversation context
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
course_tool_instance = CourseInfoTool()  # Initialize the course tool

# Define the tools (now including the AIPI RAG tool)
tools = [
    Tool(
        name="Campus Events",
        func=search_campus_events,
        description="Useful for answering questions about events happening on Duke's campus in the future 50 days, including academic events, sports, and social gatherings."
    ),
    Tool(
        name="Duke Faculty",
        func=leadership_staff_agent_tool,
        description="Useful for fetching Duke Engineering faculty and leadership information from the website."
    ),
    Tool(
        name="Duke AI Courses",
        func=course_tool_instance._run,
        description="Scrapes Duke University's AI courses page to retrieve course information, including course codes, names, and descriptions."
    ),
    Tool(
        name="Pratt Link Selector",
        func=LLMPrattLinkSelector()._run,
        description="Find the most relevant Duke Pratt URL given a user query."
    ),
    Tool(
        name="General Web Scraper",
        func=GeneralWebScraper()._run,
        description="Scrapes any webpage given a full URL."
    ),
    Tool(
        name="AIPI Program Information",
        func=aipi_rag_tool,
        description="Retrieves detailed information about Duke's AI Program for Innovation (AIPI), including program details, degree options, courses, admissions, faculty, and student resources."
    )
]

# Create the agent
agent = create_react_agent(llm, tools, AGENT_PROMPT_TEMPLATE)

# Create an agent executor
agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True,
    handle_parsing_errors=True
)

# Function to process user queries
def process_query(user_query):
    try:
        response = agent_executor.invoke({"input": user_query})
        return response["output"]
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

if __name__ == "__main__":
    # Example query: requesting AIPI program information
    test_query = "Tell me about the AIPI program at Duke."
    print("User input:", test_query)
    result = process_query(test_query)
    print("Agent answer:\n", result)