from src.pricing import ModelPricing
from src.tokenizer import calculate_cost, count_tokens


def test_token_count_non_empty():
    tokens = count_tokens("Hello world, testing LLM token counting!")
    assert tokens > 0

def test_cost_calculation_math():
    mock_model = ModelPricing("Test", "Mock-1", input_1m=2.0, output_1m=10.0, context_window="128K")
    cost = calculate_cost(500_000, 100_000, mock_model)
    assert round(cost, 4) == 2.0000