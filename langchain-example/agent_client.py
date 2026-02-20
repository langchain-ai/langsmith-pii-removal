"""LangSmith Client anonymizer approach — masks PII at the tracing layer.

Sits on top of everything: inputs, outputs, tool calls, tool results,
and any additional nodes in a multi-node graph. One config covers all.
"""
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from langsmith import Client
from langsmith.anonymizer import create_anonymizer
import langsmith as ls

import importlib.util, pathlib
_spec = importlib.util.spec_from_file_location("tools", pathlib.Path(__file__).parent / "tools.py")
_tools_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tools_mod)
all_tools = _tools_mod.all_tools

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

agent = create_agent(
    model=ChatOpenAI(model="gpt-4o-mini", temperature=0),
    tools=all_tools,
)


@asynccontextmanager
async def compile_agent():
    with ls.tracing_context(client=langsmith_client):
        yield agent
