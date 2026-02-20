"""PIIMiddleware approach — masks PII at the agent middleware layer.

Works well for single-agent tool loops. Each PII type needs explicit
apply_to_input / apply_to_output / apply_to_tool_results flags.
"""
from langchain.agents import create_agent
from langchain.agents.middleware import PIIMiddleware
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from contextlib import asynccontextmanager

import importlib.util, pathlib
_spec = importlib.util.spec_from_file_location("tools", pathlib.Path(__file__).parent / "tools.py")
_tools_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tools_mod)
all_tools = _tools_mod.all_tools

load_dotenv(dotenv_path="../.env", override=True)

agent = create_agent(
    model=ChatOpenAI(model="gpt-4o-mini", temperature=0),
    tools=all_tools,
    middleware=[
        # Email addresses
        PIIMiddleware("email", strategy="redact",
                      apply_to_input=True, apply_to_output=True, apply_to_tool_results=True),
        # Credit card numbers
        PIIMiddleware("credit_card", strategy="mask",
                      apply_to_input=True, apply_to_output=True, apply_to_tool_results=True),
        # SSN
        PIIMiddleware("ssn", detector=r"\b\d{3}-\d{2}-\d{4}\b", strategy="redact",
                      apply_to_input=True, apply_to_output=True, apply_to_tool_results=True),
        # Phone numbers
        PIIMiddleware("phone", detector=r"(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
                      strategy="redact",
                      apply_to_input=True, apply_to_output=True, apply_to_tool_results=True),
        # IP addresses
        PIIMiddleware("ip", strategy="redact",
                      apply_to_input=True, apply_to_output=True, apply_to_tool_results=True),
    ],
)


@asynccontextmanager
async def compile_agent():
    yield agent
