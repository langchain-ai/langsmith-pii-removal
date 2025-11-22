# 🔒 PII Removal LangSmith

A comprehensive demonstration of how to prevent logging of sensitive data and personally identifiable information (PII) in LangSmith traces. **You can mask PII even without LangChain!** This repository shows multiple approaches including direct LangSmith integration, LangGraph workflows, and LangChain middleware.

## ✨ Features

- **🔐 Automatic PII Masking**: Uses LangSmith's `create_anonymizer` to automatically mask emails, IP addresses, phone numbers, credit cards, SSNs, and dates
- **🚫 Works Without LangChain**: PII masking works directly with OpenAI and LangSmith - no LangChain required!
- **🛠️ Multiple Approaches**: Shows different methods for PII removal including environment variables, client manipulation, and custom anonymizers
- **🔄 LangGraph Integration**: Demonstrates PII masking in a LangGraph agent workflow
- **🛡️ LangChain PIIMiddleware**: Demonstrates PII detection and handling using LangChain's PIIMiddleware with configurable strategies (redact, mask, hash, block)

## ⚙️ Setup

### Prerequisites

- Python 3.11+
- OpenAI API key
- LangSmith API key (optional, for trace viewing)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/langchain-ai/langsmith-pii-removal
   cd langsmith-pii-removal
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file**
   ```bash
   # Create .env file in root directory
   touch .env  # On Windows: type nul > .env
   ```
   
   Add your API keys to `.env`:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   LANGSMITH_API_KEY=your_langsmith_api_key_here  # Optional
   LANGSMITH_TRACING=true  # Optional, for trace viewing
   ```

## 🛡️ PII Masking Methods (No LangChain Required!)

> **💡 Key Point**: You can mask PII in LangSmith traces **without using LangChain**. The methods below work directly with OpenAI and LangSmith.

See the `non-langchain-example/remove_pii.ipynb` notebook for working examples:

### 1. Environment Variables (Simplest Method)
Hide all inputs/outputs globally - no code changes needed:
```bash
export LANGSMITH_HIDE_INPUTS=true
export LANGSMITH_HIDE_OUTPUTS=true
```

### 2. LangSmith Client with Anonymizer (Recommended)
Use custom regex patterns to mask specific PII types - works with any OpenAI client:
```python
import openai
from langsmith import Client
from langsmith.wrappers import wrap_openai
from langsmith.anonymizer import create_anonymizer

# Create anonymizer with regex patterns
anonymizer = create_anonymizer([
    {"pattern": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "replace": "[EMAIL_REDACTED]"},
    {"pattern": r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "replace": "[IP_REDACTED]"}
])

# Use with LangSmith client
langsmith_client = Client(anonymizer=anonymizer)
openai_client = wrap_openai(openai.Client())

# PII is automatically masked in traces
response = openai_client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "My email is john@example.com"}],
    langsmith_extra={"client": langsmith_client}
)
```

### 3. Custom Input/Output Redaction
Define custom logic to redact specific fields:
```python
from langsmith import Client
from langsmith.wrappers import wrap_openai
import openai

def redact_system_messages(inputs: dict) -> dict:
    """Redact system messages from inputs."""
    messages = inputs.get("messages", [])
    redacted = [
        {"role": m.get("role"), "content": "REDACTED"}
        if m.get("role") == "system" else m
        for m in messages
    ]
    return {**inputs, "messages": redacted}

langsmith_client = Client(hide_inputs=redact_system_messages)
openai_client = wrap_openai(openai.Client())

response = openai_client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[...],
    langsmith_extra={"client": langsmith_client}
)
```

> **📝 Note**: All three methods work with the standard OpenAI Python SDK - no LangChain dependency required!

## 🚀 LangGraph Integration

The `langgraph-example/agent.py` demonstrates how to integrate PII masking into a LangGraph workflow using LangSmith's anonymizer (the same anonymizer approach shown above - no LangChain required for the masking itself).

> [!IMPORTANT]
>  The `@asynccontextmanager` is required to inject the custom LangSmith client with anonymizer into the graph.

## 🛡️ LangChain PIIMiddleware Integration

The `langchain-example/agent.py` demonstrates how to use LangChain's `PIIMiddleware` to detect and handle PII with configurable strategies. If you're already using LangChain agents, this provides fine-grained control over PII handling within the agent middleware layer.

### Features

- **Built-in PII Types**: Email, credit card, IP address, MAC address, URL
- **Custom PII Detectors**: Regex patterns or custom functions for domain-specific PII
- **Multiple Strategies**: 
  - `redact`: Replace with `[REDACTED_TYPE]`
  - `mask`: Partially mask (e.g., `****-****-****-1234`)
  - `hash`: Replace with deterministic hash
  - `block`: Raise exception when detected
- **Flexible Application**: Apply to inputs, outputs, and tool results independently

### Example Usage

```python
from langchain.agents import create_agent
from langchain.agents.middleware import PIIMiddleware

# Custom detector function
def detect_api_key(content: str) -> list[dict[str, str | int]]:
    matches = []
    pattern = r"sk-[a-zA-Z0-9]{32,}"
    for match in re.finditer(pattern, content):
        matches.append({
            "text": match.group(0),
            "start": match.start(),
            "end": match.end(),
        })
    return matches

# Create agent with PII middleware
agent = create_agent(
    model="gpt-4o-mini",
    tools=[...],
    middleware=[
        # Built-in email detection with redact strategy
        PIIMiddleware("email", strategy="redact", apply_to_input=True),
        # Built-in credit card with mask strategy
        PIIMiddleware("credit_card", strategy="mask", apply_to_input=True),
        # Custom API key detector with block strategy
        PIIMiddleware("api_key", detector=detect_api_key, strategy="block", apply_to_input=True),
    ],
)
```

## 🎯 Running the Examples

### Quick Start: Non-LangChain Example

Try PII masking with just OpenAI and LangSmith:

1. **Run the notebook**
   ```bash
   jupyter notebook non-langchain-example/remove_pii.ipynb
   ```

### Running LangGraph/LangChain Examples

1. **Start LangGraph Studio**
   ```bash
   langgraph dev --config langgraph.json
   ```

2. **Access the Studio**
   - Open your browser to `http://localhost:2024`
   - Select either `langgraph_pii_masking` or `langchain_pii_masking`

3. **Test PII Masking**
   - **LangGraph example**: Try "My email is john@example.com and phone is (555) 123-4567"
   - **LangChain example**: Try "My email is john@example.com and credit card is 4532-1234-5678-9010"
   - Observe how PII is automatically handled before processing

![LangGraph PII Masking Trace](images/langgraph.png)

## 📊 Supported PII Types

### Direct LangSmith Integration (No LangChain Required)
The `non-langchain-example/remove_pii.ipynb` and `langgraph-example/agent.py` use LangSmith's anonymizer:
- **📧 Email addresses**: `user@example.com` → `[EMAIL_REDACTED]`
- **🌐 IP addresses**: `192.168.1.1` → `[IP_REDACTED]`
- **📞 Phone numbers**: `(555) 123-4567` → `[PHONE_REDACTED]`
- **💳 Credit cards**: `1234-5678-9012-3456` → `[CC_REDACTED]`
- **🆔 Social Security Numbers**: `123-45-6789` → `[SSN_REDACTED]`
- **📅 Dates**: `12/25/2024` → `[DATE_REDACTED]`

### LangChain PIIMiddleware (Optional)
The `langchain-example/agent.py` uses LangChain's middleware:
- **📧 Email addresses**: Redacted (`[REDACTED_email]`)
- **💳 Credit cards**: Masked (shows last 4 digits: `****-****-****-9010`)
- **🔑 API keys**: Blocked (raises exception when detected)

## 🎯 Which Approach Should I Use?

| Approach | When to Use | Dependencies |
|----------|-------------|---------------|
| **LangSmith Anonymizer** | ✅ **Recommended for most cases** - Works with any OpenAI client, no LangChain needed | `openai`, `langsmith` |
| **Environment Variables** | Simple blanket hiding of all inputs/outputs | None (just env vars) |
| **LangChain PIIMiddleware** | Only if you're already using LangChain agents and need middleware-level control | `langchain`, `langchain-openai` |
| **LangGraph + Anonymizer** | When building LangGraph workflows | `langgraph`, `langsmith` |

> **💡 Recommendation**: Start with LangSmith's anonymizer (Method 2 above) - it works with standard OpenAI SDK and requires no LangChain dependencies!

## 📚 Documentation

For more detailed information on PII masking and observability, visit:
- [LangSmith Documentation](https://docs.smith.langchain.com/observability/how_to_guides/mask_inputs_outputs)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain PIIMiddleware Documentation](https://python.langchain.com/docs/how_to/pii_middleware)

## 🤝 Contributing

Feel free to submit issues and enhancement requests!
