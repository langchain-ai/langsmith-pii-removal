from langchain_core.tools import tool

# Fake customer database for demonstrating PII in tool calls
CUSTOMER_DB = {
    "john smith": {
        "name": "John Smith",
        "email": "john.smith@acmecorp.com",
        "phone": "(555) 867-5309",
        "ssn": "123-45-6789",
        "credit_card": "4532-1488-0343-6728",
        "ip_address": "192.168.1.42",
        "address": "123 Main St, Springfield, IL 62701",
    },
    "jane doe": {
        "name": "Jane Doe",
        "email": "jane.doe@globex.net",
        "phone": "(555) 234-5678",
        "ssn": "987-65-4321",
        "credit_card": "5105-1051-0510-5100",
        "ip_address": "10.0.0.7",
        "address": "456 Oak Ave, Shelbyville, IL 62565",
    },
}


@tool
def get_weather(location: str) -> str:
    """Get the weather for a given location."""
    return f"The weather in {location} is sunny and 72°F."


@tool
def calculate(expression: str) -> str:
    """Calculate a simple mathematical expression (basic operations only)."""
    import operator
    import ast

    try:
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


@tool
def lookup_customer(name: str) -> str:
    """Look up customer information by name. Returns their full profile."""
    key = name.strip().lower()
    customer = CUSTOMER_DB.get(key)
    if not customer:
        return f"No customer found with name '{name}'."
    return (
        f"Customer Record:\n"
        f"  Name: {customer['name']}\n"
        f"  Email: {customer['email']}\n"
        f"  Phone: {customer['phone']}\n"
        f"  SSN: {customer['ssn']}\n"
        f"  Credit Card: {customer['credit_card']}\n"
        f"  IP Address: {customer['ip_address']}\n"
        f"  Address: {customer['address']}"
    )


all_tools = [get_weather, calculate, lookup_customer]
