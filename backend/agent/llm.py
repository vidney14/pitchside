from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

load_dotenv()  # reads .env into environment variables


def get_llm(provider: str = "gemini"):
    if provider == "gemini":
        return ChatGoogleGenerativeAI(model="gemini-3.6-flash")
    if provider == "groq":
        return ChatGroq(model="openai/gpt-oss-120b", temperature=0)
    raise ValueError(f"unknown provider: {provider}")