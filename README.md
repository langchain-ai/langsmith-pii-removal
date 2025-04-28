# LangSmith PII Removal

A minimal demo of how to prevent logging of sensitive data/personally identifiable information (PII) in LangSmith traces using environment variables, client input and output manipulation and custom anonymizers.

## Usage
- Set environment variables to hide all inputs/outputs.
- Use the LangSmith Client for custom masking logic or regex anonymizers (e.g., for emails, IP addresses, UUIDs).

See:
- `remove_pii.ipynb` for code examples.
- `images/` for LangSmith visual examples. 


For more, visit: https://docs.smith.langchain.com/observability/how_to_guides/mask_inputs_outputs
