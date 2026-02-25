from dotenv import load_dotenv
from contextlib import asynccontextmanager
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph, MessagesState
from langsmith import Client
from langsmith.anonymizer import create_anonymizer
import langsmith as ls
import os

load_dotenv(dotenv_path="../.env", override=True)

anonymizer = create_anonymizer([
    { "pattern": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "replace": "[EMAIL_REDACTED]" },
    { "pattern": r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "replace": "[IP_REDACTED]" },
    { "pattern": r"(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", "replace": "[PHONE_REDACTED]" },
    { "pattern": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "replace": "[CC_REDACTED]" },
    { "pattern": r"\b\d{3}-\d{2}-\d{4}\b", "replace": "[SSN_REDACTED]" },
    { "pattern": r"\b\d{1,2}/\d{1,2}/\d{4}\b|\b\d{4}-\d{1,2}-\d{1,2}\b", "replace": "[DATE_REDACTED]" },
])

langsmith_client = Client(anonymizer=anonymizer)

llm = ChatOpenAI(
    model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
    api_key=os.environ.get("OPENAI_API_KEY"),
    temperature=0
)

SYSTEM_PROMPT = "You are a helpful assistant."

def llm_node(state: MessagesState) -> dict:
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

builder = StateGraph(MessagesState)
builder.add_node("llm_node", llm_node)
builder.add_edge(START, "llm_node")
builder.add_edge("llm_node", END)
agent = builder.compile()

@asynccontextmanager
async def compile_agent():
    with ls.tracing_context(client=langsmith_client):
        yield agent
