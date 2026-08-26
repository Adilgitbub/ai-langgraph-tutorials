
import os
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

gamma_model = ChatOpenAI(
    base_url="http://localhost:12434/engines/v1",
    api_key="not-needed",
    model="ai/gemma4:E4B"
)

gamma_model1 = ChatGoogleGenerativeAI(
    model=os.getenv("GOOGLE_MODEL", "gemini-3.6-flash"),
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    max_retries=2
)

lamma_model = ChatOpenAI(
    base_url="http://localhost:12434/engines/v1",
    api_key="not-needed",
    model="ai/llama3.2:3B-Q4_K_M"
)