from app.config import get_settings

def estimate_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4) if text else 0

def calculate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    cfg = get_settings()
    return (prompt_tokens * cfg.input_cost_per_1m + completion_tokens * cfg.output_cost_per_1m) / 1_000_000
