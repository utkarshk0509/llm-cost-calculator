from dataclasses import dataclass

@dataclass(frozen=True)
class ModelPricing:
    provider: str
    model: str
    input_1m: float   
    output_1m: float 
    context_window: str

PRICING_REGISTRY : list[ModelPricing] = [
    ModelPricing("Google", "Gemini 2.5 Flash", 0.15, 0.60, "1M"),
    ModelPricing("Google", "Gemini 2.5 Pro", 1.25, 10.00, "2M"),
    ModelPricing("OpenAI", "GPT-4o", 2.50, 10.00, "128K"),
    ModelPricing("OpenAI", "GPT-4o-mini", 0.15, 0.60, "128K"),
    ModelPricing("Anthropic", "Claude 3.7 Sonnet", 3.00, 15.00, "200K"),
    ModelPricing("Anthropic", "Claude 3.5 Haiku", 0.80, 4.00, "200K"),
]