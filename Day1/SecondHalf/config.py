import os
OPENAI_MODEL=os.getenv(
    "OPENAI_MODEL",
    "openrouter/free"
)
MAX_CONTEXT_TOKENS=32000
MODEL_PRICES={
    "openrouter/free":{
        "input":0.0,
        "output":0.0,
    },
    "authropic/claude-haiku-5.5":{
        "input":0.0,
        "output":0.0
    }
}
DAILY_BUDGET=1.0