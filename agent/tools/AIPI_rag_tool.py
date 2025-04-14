import os
import glob
from typing import Dict, List, Any, Optional
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from langchain_openai import OpenAIEmbeddings
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

class AIPIRagTool:
    """Tool for retrieving information about Duke's AIPI program using RAG."""
    
    def __init__(self, data_dir="duke_aipi_data", api_key=None):
        """
        Initialize the AIPI RAG tool
        
        Parameters:
            data_dir: Directory containing the scraped AIPI data
            api_key: OpenAI API key (optional, will use environment variable if not provided)
        """
        self.data_dir = data_dir
        
        # Get API key from parameter or environment variable
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please provide it as a parameter or set the OPENAI_API_KEY environment variable.")
        
        # Initialize with explicit API key
        self.embeddings = OpenAIEmbeddings(api_key=self.api_key)
        self.llm = ChatOpenAI(model="gpt-4", api_key=self.api_key)
        self.vector_store = None
        self.retriever = None
        self.qa_chain = None
        
        # Initialize on creation
        self._initialize_vector_store()
        
    def _initialize_vector_store(self):
        """Load and index all AIPI data files"""
        # Check if the data directory exists
        if not os.path.exists(self.data_dir):
            raise FileNotFoundError(f"Data directory {self.data_dir} not found")
        
        # Collect all summary text files
        text_files = glob.glob(os.path.join(self.data_dir, "*_summary.txt"))
        if not text_files:
            raise FileNotFoundError(f"No summary text files found in {self.data_dir}")
        
        # Load and chunk all documents
        all_texts = []
        for file_path in text_files:
            category = os.path.basename(file_path).replace("_summary.txt", "")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Split the content into sections by the separator
                sections = content.split("-" * 50)
                for section in sections:
                    if section.strip():
                        all_texts.append(f"[Category: {category}]\n{section.strip()}")
        
        # Create text chunks for better retrieval
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        
        chunks = text_splitter.create_documents(all_texts)
        
        # Create vector store
        self.vector_store = FAISS.from_documents(chunks, self.embeddings)
        
        # Create basic retriever
        basic_retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )
        
        # Enhance with multi-query retriever for better results
        self.retriever = MultiQueryRetriever.from_llm(
            retriever=basic_retriever,
            llm=self.llm
        )
        
        # Create QA chain
        template = """You are a helpful assistant for Duke University's AI Program for Innovation (AIPI).
        Use the following pieces of retrieved context to answer the question.
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        Make your answers complete and informative.
        
        Context: {context}
        
        Question: {question}
        
        Answer:"""
        
        PROMPT = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": PROMPT}
        )
        
    def _run(self, query: str) -> str:
        """
        Run the AIPI RAG tool to answer a query
        
        Parameters:
            query: User query about Duke AIPI program
        
        Returns:
            Answer to the query
        """
        if not self.qa_chain:
            self._initialize_vector_store()
            
        # Use invoke instead of __call__ to avoid deprecation warning
        result = self.qa_chain.invoke({"query": query})
        
        # Format the answer with sources
        answer = result["result"]
        
        # Add source information
        source_texts = []
        for doc in result["source_documents"]:
            if doc.page_content:
                source_line = doc.page_content.split("\n")[0]
                # If the first line is the category label
                if source_line.startswith("[Category:"):
                    category = source_line.replace("[Category:", "").replace("]", "").strip()
                    # Extract URL if present
                    url_match = None
                    for line in doc.page_content.split("\n"):
                        if line.startswith("URL:"):
                            url_match = line.replace("URL:", "").strip()
                            break
                    
                    if url_match and category and url_match not in source_texts:
                        source_texts.append(f"- {category}: {url_match}")
        
        # Only include sources if there are any
        if source_texts:
            answer += "\n\nSources:\n" + "\n".join(source_texts)
            
        return answer

    def get_category_info(self, category: str) -> str:
        """
        Get information about a specific category
        
        Parameters:
            category: Category name
        
        Returns:
            Information about the category
        """
        # Check if the summary file exists
        summary_file = os.path.join(self.data_dir, f"{category}_summary.txt")
        if not os.path.exists(summary_file):
            return f"No information found for category: {category}"
        
        # Read the summary file
        with open(summary_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return f"Information about {category}:\n\n{content}"
    
    def list_categories(self) -> List[str]:
        """
        List all available categories
        
        Returns:
            List of categories
        """
        # Get all summary files
        summary_files = glob.glob(os.path.join(self.data_dir, "*_summary.txt"))
        categories = [os.path.basename(f).replace("_summary.txt", "") for f in summary_files]
        return categories


def aipi_rag_tool(query: str) -> str:
    """
    Function to use with LangChain Tool
    
    Parameters:
        query: User query about Duke AIPI program
    
    Returns:
        Answer to the query
    """
    try:
        # Get API key from environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "Error: OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
        
        tool = AIPIRagTool(api_key=api_key)
        return tool._run(query)
    except Exception as e:
        return f"Error retrieving AIPI information: {str(e)}"

if __name__ == "__main__":
    # Example usage
    query = "What are the requirements for the AIPI program?"
    print(aipi_rag_tool(query))