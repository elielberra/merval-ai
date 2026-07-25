from anthropic import Anthropic

NEWS_MODEL = "claude-sonnet-5"
# Final stock-pick decision — the most critical call, so Opus for max quality.
# The ensemble runs its calls concurrently, so the slower model costs little wall time.
DECISION_MODEL = "claude-opus-5"


def client():
    return Anthropic()
