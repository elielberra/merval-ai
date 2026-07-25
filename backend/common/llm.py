from anthropic import Anthropic

NEWS_MODEL = "claude-sonnet-5"
# Final stock-pick decision. Sonnet by default since it's run as an ensemble
# (multiple calls); switch to "claude-opus-4-8" for max quality on the decision.
DECISION_MODEL = "claude-sonnet-5"


def client():
    return Anthropic()
