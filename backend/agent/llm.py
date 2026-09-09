from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

load_dotenv()


def get_llm(provider: str = "groq"):
    if provider == "gemini":
        return ChatGoogleGenerativeAI(model="gemini-3.6-flash")
    if provider == "groq":
        return ChatGroq(model="openai/gpt-oss-120b", temperature=0)
    raise ValueError(f"unknown provider: {provider}")


def structured(provider: str, schema, messages, retries: int = 2):
    """Call the model with structured output, retrying if it returns prose instead."""
    llm = get_llm(provider).with_structured_output(schema)
    last = None
    for attempt in range(retries + 1):
        try:
            return llm.invoke(messages)
        except Exception as exc:
            last = exc
            if attempt < retries:
                messages = messages + [
                    ("user", "You must respond by calling the tool with the required fields. Do not write prose.")
                ]
    raise last