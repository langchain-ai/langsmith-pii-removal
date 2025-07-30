from dotenv import load_dotenv
from contextlib import asynccontextmanager
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, List, TypedDict
from langsmith import Client
from langsmith.wrappers import wrap_openai
import langsmith as ls
from langsmith.anonymizer import create_anonymizer
import openai

load_dotenv(dotenv_path="./langgraph/.env", override=True)

# create an anonymizer that masks various PII patterns
anonymizer = create_anonymizer([
    # Email addresses
    { "pattern": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "replace": "[EMAIL_REDACTED]" },
    # IP addresses
    { "pattern": r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "replace": "[IP_REDACTED]" },
    # Phone numbers (various formats)
    { "pattern": r"(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", "replace": "[PHONE_REDACTED]" },
    # Credit card numbers
    { "pattern": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "replace": "[CC_REDACTED]" },
    # Social Security Numbers
    { "pattern": r"\b\d{3}-\d{2}-\d{4}\b", "replace": "[SSN_REDACTED]" },
    # Dates (MM/DD/YYYY or YYYY-MM-DD)
    { "pattern": r"\b\d{1,2}/\d{1,2}/\d{4}\b|\b\d{4}-\d{1,2}-\d{1,2}\b", "replace": "[DATE_REDACTED]" }
])

langsmith_client = Client(anonymizer=anonymizer)

# We wrap the OpenAI client so that we can pass the LangSmith client to the kwargs of the OpenAIAPI call
openai_client = wrap_openai(openai.Client())

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

SYSTEM_PROMPT = """
You are a helpful assistant that can answer questions and process requests.
"""

def llm_node(state: State) -> dict:
    """Process user input - PII is automatically masked by LangSmith"""
    last_message = state["messages"][-1]
    
    # The input has been automatically masked by LangSmith's anonymizer
    # We can see the masked version in the message content
    masked_input = last_message.content

    
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": masked_input}
        ],
        temperature=0,
        langsmith_extra={"client": langsmith_client}
    )
    
    return {"messages": [HumanMessage(content=response.choices[0].message.content)]}

builder = StateGraph(State)
builder.add_node("llm_node", llm_node)
builder.add_edge(START, "llm_node")
builder.add_edge("llm_node", END)
agent = builder.compile()

@asynccontextmanager
async def create_agent():
    with ls.tracing_context(client=langsmith_client):
        yield agent