from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModelPricing:
    provider: str
    model: str
    input_1m: float
    output_1m: float
    context_window: str
    cached_input_1m: float | None = None
    batch_discount: float = 0.50
    tier: str = "General"
    description: str = ""
    strengths: tuple[str, ...] = field(default_factory=tuple)


# USD per 1M tokens. Rates reflect current 2025/2026 standard public pricing tiers.
PRICING_REGISTRY: list[ModelPricing] = [
    # Google
    ModelPricing(
        provider="Google",
        model="Gemini 2.5 Flash",
        input_1m=0.15,
        output_1m=0.60,
        context_window="1M",
        cached_input_1m=0.0375,
        tier="Ultra-Low Cost",
        description="Exceptional price-to-performance ratio with massive 1M context.",
        strengths=("High Speed", "Huge Context", "Multimodal", "Ultra Cheap"),
    ),
    ModelPricing(
        provider="Google",
        model="Gemini 2.5 Pro",
        input_1m=1.25,
        output_1m=10.00,
        context_window="2M",
        cached_input_1m=0.3125,
        tier="Flagship",
        description="Top-tier reasoning and code synthesis across 2M token context.",
        strengths=("Deep Reasoning", "2M Context Window", "Complex Code"),
    ),
    ModelPricing(
        provider="Google",
        model="Gemini 2.0 Flash Lite",
        input_1m=0.075,
        output_1m=0.30,
        context_window="1M",
        cached_input_1m=0.01875,
        tier="Ultra-Low Cost",
        description="Hyper-fast and economical for lightweight summarization and triage.",
        strengths=("Sub-second Latency", "Rock-bottom Pricing"),
    ),
    # OpenAI
    ModelPricing(
        provider="OpenAI",
        model="GPT-4o",
        input_1m=2.50,
        output_1m=10.00,
        context_window="128K",
        cached_input_1m=1.25,
        tier="Flagship",
        description="Industry standard flagship model with strong multimodal and coding capabilities.",
        strengths=("General Intelligence", "Vision", "Ecosystem"),
    ),
    ModelPricing(
        provider="OpenAI",
        model="GPT-4o-mini",
        input_1m=0.15,
        output_1m=0.60,
        context_window="128K",
        cached_input_1m=0.075,
        tier="Ultra-Low Cost",
        description="Affordable and fast workhorse for high-frequency lightweight tasks.",
        strengths=("Cost Efficiency", "Fast Responses"),
    ),
    ModelPricing(
        provider="OpenAI",
        model="o3-mini",
        input_1m=1.10,
        output_1m=4.40,
        context_window="200K",
        cached_input_1m=0.55,
        tier="Reasoning",
        description="High-reasoning STEM, math, and coding model with thinking tokens.",
        strengths=("Math & Logic", "Coding", "Reasoning Effort Controls"),
    ),
    ModelPricing(
        provider="OpenAI",
        model="o1",
        input_1m=15.00,
        output_1m=60.00,
        context_window="200K",
        cached_input_1m=7.50,
        tier="Reasoning Flagship",
        description="Deep reinforcement-learning reasoning model for the hardest problems.",
        strengths=("PhD-level Reasoning", "Deep Analysis"),
    ),
    ModelPricing(
        provider="OpenAI",
        model="GPT-4.5",
        input_1m=75.00,
        output_1m=150.00,
        context_window="128K",
        cached_input_1m=37.50,
        tier="Premium Research",
        description="Massive scale foundation model for creative nuance and empathy.",
        strengths=("Creative Writing", "Broad World Knowledge"),
    ),
    # Anthropic
    ModelPricing(
        provider="Anthropic",
        model="Claude 3.7 Sonnet",
        input_1m=3.00,
        output_1m=15.00,
        context_window="200K",
        cached_input_1m=0.30,  # Cache read (90% off)
        tier="Flagship / Hybrid Reasoning",
        description="Frontier coding and hybrid reasoning model with adjustable thinking time.",
        strengths=("Superb Coding", "Extended Thinking", "Precise Instruction Following"),
    ),
    ModelPricing(
        provider="Anthropic",
        model="Claude 3.5 Sonnet",
        input_1m=3.00,
        output_1m=15.00,
        context_window="200K",
        cached_input_1m=0.30,
        tier="Flagship",
        description="Benchmark leader in engineering, coding, and multi-step workflows.",
        strengths=("Agentic Workflows", "Artifacts", "Code Generation"),
    ),
    ModelPricing(
        provider="Anthropic",
        model="Claude 3.5 Haiku",
        input_1m=0.80,
        output_1m=4.00,
        context_window="200K",
        cached_input_1m=0.08,
        tier="Fast & Cost-Efficient",
        description="Lightning fast execution with near-Sonnet intelligence for simple tasks.",
        strengths=("Rapid Turnaround", "Accurate Function Calling"),
    ),
    # DeepSeek
    ModelPricing(
        provider="DeepSeek",
        model="DeepSeek V3",
        input_1m=0.14,
        output_1m=0.28,
        context_window="64K",
        cached_input_1m=0.014,
        tier="Ultra-Low Cost",
        description="Open MoE flagship offering frontier intelligence at fraction of usual cost.",
        strengths=("Unbeatable Pricing", "Open Architecture", "Strong Reasoning"),
    ),
    ModelPricing(
        provider="DeepSeek",
        model="DeepSeek R1",
        input_1m=0.55,
        output_1m=2.19,
        context_window="64K",
        cached_input_1m=0.14,
        tier="Reasoning",
        description="Open reasoning model competing directly with OpenAI o1 at 95% lower cost.",
        strengths=("Open Weights Reasoning", "Math & Logic", "Extreme Value"),
    ),
    # Meta / Open Weights (Hosted)
    ModelPricing(
        provider="Meta",
        model="Llama 3.3 70B",
        input_1m=0.40,
        output_1m=0.40,
        context_window="128K",
        cached_input_1m=0.20,
        tier="Fast & Cost-Efficient",
        description="Open foundation model with intelligence comparable to previous 405B models.",
        strengths=("Open Ecosystem", "Balanced Cost/Intelligence"),
    ),
    ModelPricing(
        provider="Meta",
        model="Llama 3.1 405B",
        input_1m=2.00,
        output_1m=2.00,
        context_window="128K",
        cached_input_1m=1.00,
        tier="Flagship",
        description="Massive open model capable of fine-tuning teacher models and synthetic data.",
        strengths=("Synthetic Data Generation", "Distillation"),
    ),
    # Mistral
    ModelPricing(
        provider="Mistral",
        model="Mistral Large 2",
        input_1m=2.00,
        output_1m=6.00,
        context_window="128K",
        cached_input_1m=1.00,
        tier="Flagship",
        description="Top-tier European multilingual and reasoning frontier model.",
        strengths=("Multilingual", "Code Reasoning"),
    ),
    ModelPricing(
        provider="Mistral",
        model="Codestral",
        input_1m=0.30,
        output_1m=0.90,
        context_window="256K",
        cached_input_1m=0.15,
        tier="Coding Specialist",
        description="Specialized code completion and generation model covering 80+ programming languages.",
        strengths=("FIM (Fill-in-the-Middle)", "Large 256K Context", "Fast Infilling"),
    ),
]
