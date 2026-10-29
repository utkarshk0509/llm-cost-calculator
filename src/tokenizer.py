import re
from pathlib import Path

import tiktoken

from src.pricing import ModelPricing

VALID_EXTENSIONS = {".txt", ".md", ".py", ".json", ".csv", ".sql", ".js", ".html", ".tsx", ".ts", ".yaml", ".yml"}


def count_tokens(text: str, enc_name: str = "o200k_base") -> int:
    """Count tokens using tiktoken (default o200k_base for GPT-4o)."""
    if not text:
        return 0
    try:
        enc = tiktoken.get_encoding(enc_name)
        return len(enc.encode(text))
    except Exception:
        # Fallback approximation: 1 token ≈ 4 characters
        return max(1, len(text) // 4)


def estimate_tokens_by_provider(text: str) -> dict[str, int]:
    """Provide estimated token count tailored for each provider's tokenizer family."""
    base_openai = count_tokens(text, "o200k_base")
    return {
        "OpenAI": base_openai,
        "Google": int(round(base_openai * 0.95)),  # Gemini tokenizer is slightly denser on text
        "Anthropic": int(round(base_openai * 1.05)),  # Claude tokenizer has slightly higher token counts
        "DeepSeek": int(round(base_openai * 1.02)),
        "Meta": int(round(base_openai * 1.03)),
        "Mistral": int(round(base_openai * 1.04)),
    }


def load_text_from_path(target: Path) -> tuple[str, int]:
    """Recursively load supported text files from path."""
    if target.is_file():
        return target.read_text(encoding="utf-8", errors="ignore"), 1

    chunks = []
    f_count = 0
    for f_path in target.rglob("*"):
        if f_path.is_file() and f_path.suffix.lower() in VALID_EXTENSIONS:
            try:
                chunks.append(f_path.read_text(encoding="utf-8", errors="ignore"))
                f_count += 1
            except Exception:
                continue
    return "\n".join(chunks), f_count


def calculate_cost(in_tokens: int, out_tokens: int, model: ModelPricing) -> float:
    """Calculate single-call standard cost in USD for backward compatibility."""
    in_cost = (in_tokens / 1_000_000) * model.input_1m
    out_cost = (out_tokens / 1_000_000) * model.output_1m
    return in_cost + out_cost


def calculate_detailed_cost(
    in_tokens: int,
    out_tokens: int,
    model: ModelPricing,
    cache_read_pct: float = 0.0,
    is_batch: bool = False,
    reasoning_tokens: int = 0,
    calls_per_day: int = 100,
) -> dict:
    """Calculate detailed multi-factor cost including prompt caching, batch discounts, and reasoning tokens."""
    # Ensure cache read pct between 0 and 1
    cache_read_pct = max(0.0, min(1.0, cache_read_pct))
    effective_cached_rate = model.cached_input_1m if model.cached_input_1m is not None else model.input_1m

    # Input cost with caching
    cached_tokens = int(in_tokens * cache_read_pct)
    uncached_tokens = in_tokens - cached_tokens
    in_cost = (uncached_tokens / 1_000_000) * model.input_1m + (cached_tokens / 1_000_000) * effective_cached_rate

    # Output cost: standard output tokens + reasoning tokens (reasoning tokens are billed as output tokens)
    total_out_tokens = out_tokens + reasoning_tokens
    out_cost = (total_out_tokens / 1_000_000) * model.output_1m

    total_single_cost = in_cost + out_cost

    # Batch discount applied to total single cost if requested
    if is_batch:
        total_single_cost *= (1.0 - model.batch_discount)

    thousand_calls_cost = total_single_cost * 1_000
    daily_cost = total_single_cost * calls_per_day
    monthly_cost = daily_cost * 30
    annual_cost = daily_cost * 365

    # Standard reference cost (without caching or batching) for comparison
    ref_standard_cost = calculate_cost(in_tokens, out_tokens, model)

    return {
        "provider": model.provider,
        "model": model.model,
        "tier": model.tier,
        "context_window": model.context_window,
        "description": model.description,
        "strengths": list(model.strengths),
        "in_cost": round(in_cost, 6),
        "out_cost": round(out_cost, 6),
        "single_call_cost": round(total_single_cost, 6),
        "thousand_calls_cost": round(thousand_calls_cost, 4),
        "daily_cost": round(daily_cost, 4),
        "monthly_cost": round(monthly_cost, 2),
        "annual_cost": round(annual_cost, 2),
        "reference_standard_cost": round(ref_standard_cost, 6),
        "savings_from_caching_and_batch": round(max(0.0, ref_standard_cost - total_single_cost), 6),
    }


def analyze_prompt_optimization(text: str) -> dict:
    """Analyze prompt for common token-wasting patterns and calculate potential savings."""
    if not text.strip():
        return {
            "original_tokens": 0,
            "optimized_tokens": 0,
            "tokens_saved": 0,
            "percentage_saved": 0.0,
            "suggestions": [],
            "cleaned_preview": "",
        }

    original_tokens = count_tokens(text)
    suggestions = []

    # 1. Multiple consecutive whitespaces and excessive newlines
    cleaned = re.sub(r"[ \t]+", " ", text)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    whitespace_diff = len(text) - len(cleaned)
    if whitespace_diff > 20:
        suggestions.append({
            "type": "Whitespace Normalization",
            "impact": "Medium",
            "message": f"Found {whitespace_diff} redundant whitespace characters and extra blank lines.",
        })

    # 2. Conversational filler phrases that add no instruction value
    filler_patterns = [
        r"(?i)\bplease\s+(?:make\s+sure\s+to|be\s+sure\s+to|ensure\s+that\s+you)\b",
        r"(?i)\bas\s+an\s+ai\s+language\s+model\b",
        r"(?i)\byou\s+are\s+a\s+helpful\s+and\s+knowledgeable\s+assistant\b",
        r"(?i)\bi\s+would\s+like\s+you\s+to\b",
        r"(?i)\bcould\s+you\s+please\b",
        r"(?i)\bin\s+order\s+to\b",
    ]
    detected_fillers = 0
    for pat in filler_patterns:
        matches = len(re.findall(pat, cleaned))
        if matches > 0:
            detected_fillers += matches
            cleaned = re.sub(pat, "", cleaned)

    if detected_fillers > 0:
        suggestions.append({
            "type": "Conversational Boilerplate",
            "impact": "High",
            "message": f"Detected {detected_fillers} verbose filler phrases. Replacing them with direct imperative verbs saves tokens.",
        })

    # Clean up any orphan double spaces
    cleaned = re.sub(r" +", " ", cleaned).strip()
    optimized_tokens = count_tokens(cleaned)
    tokens_saved = max(0, original_tokens - optimized_tokens)
    percentage_saved = (tokens_saved / original_tokens * 100) if original_tokens > 0 else 0.0

    return {
        "original_tokens": original_tokens,
        "optimized_tokens": optimized_tokens,
        "tokens_saved": tokens_saved,
        "percentage_saved": round(percentage_saved, 1),
        "suggestions": suggestions,
        "cleaned_preview": cleaned[:500] + ("..." if len(cleaned) > 500 else ""),
    }
