RETAIN = 5

RUNS = 2

METADATA_MAX_RETRIES = 5

MODELS = [
    # openai models
    "openai/gpt-5.4-nano",
    "openai/gpt-5.4-mini",
    "openai/gpt-5.4",
    "openai/gpt-5.5",
    "openai/gpt-5.6-luna",
    "openai/gpt-5.6-terra",
    "openai/gpt-5.6-sol",
    # anthropic models
    "anthropic/claude-opus-5",
    "anthropic/claude-opus-4.8",
    "anthropic/claude-sonnet-5",
    "anthropic/claude-sonnet-4.6",
    "anthropic/claude-haiku-4.5",
    # google models (gemini family)
    "google/gemini-2.5-flash",
    "google/gemini-3.1-pro-preview",
    "google/gemini-3.5-flash",
    "google/gemini-3.1-flash-lite-preview",
    # google models (gemma family)
    "google/gemma-4-31b-it",
    "google/gemma-4-31b-it:free",
    "google/gemma-3-27b-it",
    # meta models (llama family)
    "meta-llama/llama-4-maverick",
    "meta-llama/llama-4-scout",
    "meta-llama/llama-3.3-70b-instruct",
    #  quen models
    "qwen/qwen3.6-plus",
    "qwen/qwen3.7-max",
    "qwen/qwen3.7-plus",
    "qwen/qwen3.6-35b-a3b",
    # mistral models
    "mistralai/mistral-large-2512",
    "mistralai/mistral-small-2603",
    "mistralai/ministral-14b-2512",
]


TEMPERATURE = 0


SYSTEM_PROMPT = """
Person A and Person B are talking to each other. Person A asks a question and Person B answers.
Given Person A's question, estimate how strongly Person B's answer should be interpreted as
answering “yes” versus “no.”

Output a single integer score from 1 to 7, where:

1 = definitely no
2 = very likely no
3 = somewhat likely no
4 = completely uncertain, ambiguous
5 = somewhat likely yes
6 = very likely yes
7 = definitely yes

Also report the rationale for your decision in a few sentences, explaining why you gave the score you did.
If the answer is ambiguous or irrelevant, explain why.

Return score and rationale as valid JSON.
"""

SCORE_SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "score": {
                        "type": "integer"
                    },
                    "rationale": {"type": "string"}
                },
                "required": ["id", "score", "rationale"],
                "additionalProperties": False
            }
        }
    },
    "required": ["results"],
    "additionalProperties": False
}
