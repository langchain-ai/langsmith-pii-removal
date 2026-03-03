"""
Custom Fernet-based encryption for LangGraph checkpoint data at rest.

Registered in langgraph_custom.json under `"encryption": {"path": "..."}`.
The server calls encrypt/decrypt hooks before writing to / after reading
from Postgres, so all checkpoint blobs and JSON fields are stored as
opaque ciphertext.

Required env var:
    FERNET_KEY — a URL-safe base64-encoded 32-byte key.
    Generate once with:
        python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""

import json
import os

from cryptography.fernet import Fernet
from langgraph_sdk import Encryption, EncryptionContext

# ---------------------------------------------------------------------------
# Key loading — must be stable across restarts so Postgres data stays readable
#
# IMPORTANT: Do NOT call Fernet.generate_key() here.
# Generating a new key on every server start means any data encrypted in a
# previous run becomes permanently unreadable — Fernet decryption will fail
# with InvalidToken for every existing checkpoint blob in Postgres.
# The key must be fixed and loaded from an environment variable so it is the
# same across all restarts and replicas.
# ---------------------------------------------------------------------------
_raw_key = os.environ.get("FERNET_KEY")
if not _raw_key:
    # Fail loudly on startup rather than silently encrypting with an unknown key
    # that will be lost the moment the process exits.
    raise RuntimeError(
        "FERNET_KEY environment variable is not set. "
        "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
    )

fernet = Fernet(_raw_key.encode())

# ---------------------------------------------------------------------------
# Fields that must stay in plaintext so the server can route / index them
# ---------------------------------------------------------------------------
SKIP_FIELDS = {
    "tenant_id", "owner",
    "run_id", "thread_id", "graph_id", "assistant_id", "user_id", "checkpoint_id",
    "source", "step", "parents", "run_attempt",
    "langgraph_version", "langgraph_api_version", "langgraph_plan", "langgraph_host",
    "langgraph_api_url", "langgraph_request_id", "langgraph_auth_user",
    "langgraph_auth_user_id", "langgraph_auth_permissions",
}

ENCRYPTED_PREFIX = "encrypted:"

# ---------------------------------------------------------------------------
# Encryption instance — referenced by langgraph_custom.json
# ---------------------------------------------------------------------------
encryption = Encryption()


@encryption.encrypt.blob
async def encrypt_blob(ctx: EncryptionContext, data: bytes) -> bytes:
    return fernet.encrypt(data)


@encryption.decrypt.blob
async def decrypt_blob(ctx: EncryptionContext, data: bytes) -> bytes:
    return fernet.decrypt(data)


@encryption.encrypt.json
async def encrypt_json(ctx: EncryptionContext, data: dict) -> dict:
    result = {}
    for k, v in data.items():
        if k in SKIP_FIELDS or v is None:
            result[k] = v
        else:
            encrypted = fernet.encrypt(json.dumps(v).encode()).decode()
            result[k] = ENCRYPTED_PREFIX + encrypted
    return result


@encryption.decrypt.json
async def decrypt_json(ctx: EncryptionContext, data: dict) -> dict:
    result = {}
    for k, v in data.items():
        if isinstance(v, str) and v.startswith(ENCRYPTED_PREFIX):
            decrypted = fernet.decrypt(v[len(ENCRYPTED_PREFIX):].encode()).decode()
            result[k] = json.loads(decrypted)
        else:
            result[k] = v
    return result
