from google import genai
from dotenv import load_dotenv
from agent.main import process_query
import os

def get_gemini_response(prompt, chatbot_answer):
    client = genai.Client(api_key=os.getenv("GEM_KEY"))
    
    # Prompting Gemini to grade the chatbot's answer
    grade_prompt = f"""
    Please grade the following answer to the question on a scale of 1-10 based on the quality of the answer. 
    Just return a number.
    
    Prompt: {prompt}
    Chatbot's Answer: {chatbot_answer}
    
    Grade this response (1-10):
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=grade_prompt
    )
    
    return response.text

if __name__ == "__main__":
    load_dotenv()
    queries = ["Give me details about Dr. Bent", "What are the Duke events on April 16th?", "Tell me about the LLM course", 
               'How long is the AIPI program?']
    s = []
    for q in queries:
        print("User input:", q)
        result = process_query(q)
        print("Agent answer:\n", result)
        gemini_grade = get_gemini_response(q, result)
        s.append(int(gemini_grade))
    print(s)
    print("Average Grade:", sum(s)/len(s))
    
