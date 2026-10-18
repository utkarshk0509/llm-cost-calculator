from pathlib import Path

from src.pricing import ModelPricing
from src.tokenizer import calculate_cost, count_tokens, load_text_from_path


def test_token_count_non_empty():
    tok_count = count_tokens("Hello world, testing LLM token counting!")
    assert tok_count > 0


def test_cost_calculation_math():
    mock_model = ModelPricing("Test", "Mock-1", input_1m=2.0, output_1m=10.0, context_window="128K")
    cost = calculate_cost(500_000, 100_000, mock_model)
    assert round(cost, 4) == 2.0000


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