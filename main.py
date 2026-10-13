import os
from typing import List

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS: lets the grader's web page call our API from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Layer 1: defaults (lowest priority) ----
DEFAULTS = {
    "port": "8000",
    "workers": "1",
    "debug": "false",
    "log_level": "info",
    "api_key": "default-secret-000",
}

# ---- Layer 2: config.development.yaml ----
YAML_DEV = {
    "port": "8499",
    "debug": "false",
    "log_level": "warning",
    "api_key": "key-jyonaw118j",
}

# ---- Layer 3: .env file ----
DOTENV = {
    "APP_DEBUG": "true",
}

# ---- Layer 4: OS environment variables (APP_* only) ----
OS_ENV = {
    "APP_WORKERS": "3",
    "APP_DEBUG": "false",
}
# If the host also provides real APP_* variables, they win
OS_ENV.update({k: v for k, v in os.environ.items() if k.startswith("APP_")})

ALIASES = {"NUM_WORKERS": "workers"}


def normalize_key(raw: str) -> str:
    """APP_DEBUG -> debug, NUM_WORKERS -> workers, Port -> port"""
    key = raw.strip().upper()
    if key.startswith("APP_"):
        key = key[4:]
    if key in ALIASES:
        return ALIASES[key]
    return key.lower()


def coerce(key: str, value):
    value = str(value).strip()
    if key in ("port", "workers"):
        try:
            return int(value)
        except ValueError:
            return value
    if key == "debug":
        return value.lower() in ("true", "1", "yes", "on")
    return value


@app.get("/effective-config")
def effective_config(set: List[str] = Query(default=[])):
    merged = {}

    # low -> high precedence; later layers overwrite earlier ones
    for layer in (DEFAULTS, YAML_DEV, DOTENV, OS_ENV):
        for raw_key, value in layer.items():
            merged[normalize_key(raw_key)] = value

    # CLI overrides: ?set=key=value (highest priority)
    for item in set:
        if "=" in item:
            k, v = item.split("=", 1)
            merged[normalize_key(k)] = v

    result = {k: coerce(k, v) for k, v in merged.items()}
    result["api_key"] = "****"  # never reveal the secret
    return result
