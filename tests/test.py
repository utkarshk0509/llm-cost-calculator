from pathlib import Path

from src.pricing import PRICING_REGISTRY, ModelPricing
from src.tokenizer import (
    analyze_prompt_optimization,
    calculate_cost,
    calculate_detailed_cost,
    count_tokens,
    estimate_tokens_by_provider,
    load_text_from_path,
)


def test_token_count_non_empty():
    tok_count = count_tokens("Hello world, testing LLM token counting!")
    assert tok_count > 0


def test_cost_calculation_math():
    mock_model = ModelPricing("Test", "Mock-1", input_1m=2.0, output_1m=10.0, context_window="128K")
    cost = calculate_cost(500_000, 100_000, mock_model)
    assert round(cost, 4) == 2.0000


def test_detailed_cost_with_caching_and_batch():
    mock_model = ModelPricing(
        "Anthropic", "Claude 3.7 Sonnet", input_1m=3.0, output_1m=15.0, context_window="200K", cached_input_1m=0.30
    )
    # 1M input tokens with 80% cache hit, 100K output tokens, 100 calls/day
    res = calculate_detailed_cost(
        in_tokens=1_000_000,
        out_tokens=100_000,
        model=mock_model,
        cache_read_pct=0.80,
        is_batch=True,
        calls_per_day=50,
    )
    assert res["single_call_cost"] > 0
    assert res["monthly_cost"] > 0
    assert res["savings_from_caching_and_batch"] > 0


def test_provider_token_estimation():
    text = "Detailed code review and refactoring prompt for enterprise application."
    estimates = estimate_tokens_by_provider(text)
    assert "OpenAI" in estimates
    assert "Google" in estimates
    assert "Anthropic" in estimates
    assert estimates["OpenAI"] > 0


def test_prompt_optimization_detection():
    verbose_prompt = (
        "Please make sure to write clean code. As an AI language model, I would like you to analyze this text.    \n\n\n\n  "
    )
    analysis = analyze_prompt_optimization(verbose_prompt)
    assert analysis["original_tokens"] > 0
    assert analysis["percentage_saved"] >= 0
    assert len(analysis["suggestions"]) > 0


def test_load_text_file(tmp_path: Path):
    f_path = tmp_path / "sample.py"
    f_path.write_text("print('test')", encoding="utf-8")

    text, f_count = load_text_from_path(f_path)
    assert f_count == 1
    assert "print('test')" in text


def test_load_text_directory(tmp_path: Path):
    (tmp_path / "a.py").write_text("a = 1", encoding="utf-8")
    (tmp_path / "b.txt").write_text("b = 2", encoding="utf-8")
    (tmp_path / "ignored.bin").write_bytes(b"\x00\xff")

    text, f_count = load_text_from_path(tmp_path)
    assert f_count == 2
    assert "a = 1" in text
    assert "b = 2" in text


def test_pricing_registry_sanity():
    assert len(PRICING_REGISTRY) >= 10
    providers = {m.provider for m in PRICING_REGISTRY}
    assert "Google" in providers
    assert "OpenAI" in providers
    assert "Anthropic" in providers
    assert "DeepSeek" in providers
