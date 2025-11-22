from langchain.agents import create_agent
from langchain.agents.middleware import PIIMiddleware
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env", override=True)

# Define tools for the agent
@tool
def get_weather(location: str) -> str:
    """Get the weather for a given location."""
    return f"The weather in {location} is sunny and 72°F."

@tool
def calculate(expression: str) -> str:
    """Calculate a simple mathematical expression (basic operations only)."""
    import operator
    import ast
    
    # Safe evaluation using ast.literal_eval for simple expressions
    # This only works for simple numeric expressions, not arbitrary code
    try:
        # For simple arithmetic, we'll use a safer approach
        # This is a simplified version - in production, use a proper math parser
        allowed_ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
        }
        
        def safe_eval(node):
            if isinstance(node, ast.Constant):
                return node.value
            elif isinstance(node, ast.BinOp):
                left = safe_eval(node.left)
                right = safe_eval(node.right)
                op = allowed_ops.get(type(node.op))
                if op is None:
                    raise ValueError("Unsupported operation")
                return op(left, right)
            else:
                raise ValueError("Unsupported expression")
        
        tree = ast.parse(expression, mode='eval')
        result = safe_eval(tree.body)
        return f"The result is {result}"
    except:
        return "Invalid expression. Please use simple arithmetic (e.g., '2 + 2', '10 * 5')"

# Create the agent with PII middleware
# Demonstrates different strategies: redact, mask, and custom detector
agent = create_agent(
    model=ChatOpenAI(model="gpt-4o-mini", temperature=0),
    tools=[get_weather, calculate],
    middleware=[
        # Email addresses - redact strategy (built-in type)
        PIIMiddleware("email", strategy="redact", apply_to_input=True),
        # Credit card numbers - mask strategy (shows last 4 digits)
        PIIMiddleware("credit_card", strategy="mask", apply_to_input=True),
        # Custom API key detector using regex pattern - redact strategy
        PIIMiddleware(
            "api_key",
            detector=r"sk-[a-zA-Z0-9]{32,}",
            strategy="redact",
            apply_to_input=True,
        ),
    ],
)

# For compatibility with async context manager pattern
from contextlib import asynccontextmanager

@asynccontextmanager
async def compile_agent():
    """Async context manager for the agent."""
    yield agent

