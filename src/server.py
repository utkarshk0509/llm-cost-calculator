from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.pricing import PRICING_REGISTRY
from src.tokenizer import (
    analyze_prompt_optimization,
    calculate_detailed_cost,
    count_tokens,
    estimate_tokens_by_provider,
)

app = FastAPI(
    title="LLM Cost Calculator API",
    description="Interactive API for calculating and comparing LLM token counts and costs across providers.",
    version="1.0.0",
)

# Enable CORS for local Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EstimateRequest(BaseModel):
    prompt: str = Field(default="", description="The main user prompt or codebase text.")
    system_prompt: str = Field(default="", description="Optional system instructions.")
    output_tokens: int = Field(default=500, ge=1, le=128000, description="Expected completion output tokens.")
    calls_per_day: int = Field(default=100, ge=1, le=10_000_000, description="Projected calls per day.")
    cache_read_pct: float = Field(default=0.0, ge=0.0, le=1.0, description="Portion of input eligible for prompt cache hit (0.0 to 1.0).")
    is_batch: bool = Field(default=False, description="Whether to apply batch API discount (typically 50%).")
    reasoning_tokens: int = Field(default=0, ge=0, le=64000, description="Estimated reasoning/thinking tokens.")
    provider_filter: str | None = Field(default=None, description="Optional filter by provider name.")


class OptimizeRequest(BaseModel):
    text: str = Field(..., description="Prompt text to analyze for token optimization.")


PROMPT_TEMPLATES = [
    {
        "id": "rag-qa",
        "name": "RAG Document Q&A",
        "description": "Enterprise question-answering over indexed documentation and retrieval chunks.",
        "system_prompt": "You are a precise technical support AI. Answer the user's question using ONLY the provided context snippets. If the context does not contain the answer, say 'I cannot find that in the documentation.' Do not hallucinate.",
        "prompt": "Context Snippets:\n[Doc 1]: The Kubernetes cluster autoscaler evaluates pod resource requests every 10 seconds. When pods remain unscheduled for >30 seconds due to insufficient CPU/memory, a new node is provisioned within the node pool.\n[Doc 2]: Cluster scaling limits are defined under nodePool.spec.scaling.minReplicas and maxReplicas in cluster-config.yaml.\n\nQuestion: How long does the autoscaler wait before spinning up a new node when CPU is maxed out?",
        "output_tokens": 350,
        "calls_per_day": 500,
        "cache_read_pct": 0.70,
    },
    {
        "id": "code-refactor",
        "name": "Code Refactoring & Audit",
        "description": "Refactor legacy Python code for async concurrency, typing, and security.",
        "system_prompt": "You are a senior principal software engineer. Review the provided code for security vulnerabilities, race conditions, and performance bottlenecks. Output refactored code with comprehensive type hints and docstrings.",
        "prompt": "def fetch_user_dashboard(user_id):\n    conn = sqlite3.connect('app.db')\n    cursor = conn.cursor()\n    # raw query vulnerable to injection\n    cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')\n    user = cursor.fetchone()\n    cursor.execute(f'SELECT * FROM orders WHERE user_id = {user_id}')\n    orders = cursor.fetchall()\n    return {'user': user, 'orders': orders}",
        "output_tokens": 1200,
        "calls_per_day": 100,
        "cache_read_pct": 0.0,
    },
    {
        "id": "data-extraction",
        "name": "Structured JSON Extraction",
        "description": "Extract invoice fields into strict typed JSON schema.",
        "system_prompt": "Extract invoice line items, dates, vendor names, tax ID, and totals from the unstructured text. Return valid JSON only with keys: vendor, date, line_items (list of name, qty, price), subtotal, tax, total.",
        "prompt": "INVOICE #94821\nVendor: Apex Cloud Hosting LLC (EIN: 82-4910291)\nBilling Date: October 24, 2026\nItem 1: Dedicated GPU Instance A100 (40GB) - 720 hours @ $2.10/hr = $1,512.00\nItem 2: NVMe Fast Storage 2TB - 1 month = $140.00\nItem 3: High-speed egress bandwidth 5TB @ $0.05/GB = $250.00\nSubtotal: $1,902.00\nTax (8.25%): $156.92\nTotal Amount Due: $2,058.92",
        "output_tokens": 400,
        "calls_per_day": 2000,
        "cache_read_pct": 0.50,
    },
    {
        "id": "deep-reasoning",
        "name": "STEM & Algorithmic Reasoning",
        "description": "Complex mathematical modeling and game theory optimization.",
        "system_prompt": "You are a mathematical researcher. Solve the problem with rigorous step-by-step proofs, formulating differential equations where necessary.",
        "prompt": "Prove the convergence rate of stochastic gradient descent with momentum under non-convex Polyak-Lojasiewicz conditions. Specifically determine how the momentum parameter beta influences the spectral radius of the underlying discrete dynamical system.",
        "output_tokens": 2500,
        "calls_per_day": 50,
        "reasoning_tokens": 4000,
        "cache_read_pct": 0.0,
    },
]


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "app": "llm-cost-calculator-api"}


@app.get("/api/templates")
def list_templates() -> list[dict[str, Any]]:
    return PROMPT_TEMPLATES


@app.get("/api/models")
def get_models() -> list[dict[str, Any]]:
    return [
        {
            "provider": m.provider,
            "model": m.model,
            "input_1m": m.input_1m,
            "output_1m": m.output_1m,
            "context_window": m.context_window,
            "cached_input_1m": m.cached_input_1m,
            "batch_discount": m.batch_discount,
            "tier": m.tier,
            "description": m.description,
            "strengths": list(m.strengths),
        }
        for m in PRICING_REGISTRY
    ]


@app.post("/api/optimize")
def optimize_prompt(req: OptimizeRequest) -> dict[str, Any]:
    return analyze_prompt_optimization(req.text)


@app.post("/api/estimate")
def estimate_cost(req: EstimateRequest) -> dict[str, Any]:
    full_text = ""
    if req.system_prompt.strip():
        full_text += f"System: {req.system_prompt.strip()}\n\n"
    full_text += req.prompt.strip()

    if not full_text.strip():
        raise HTTPException(status_code=400, detail="Please provide a prompt or system prompt.")

    # Token calculations
    primary_input_tokens = count_tokens(full_text)
    provider_tokens = estimate_tokens_by_provider(full_text)

    # Filter models if requested
    models_to_evaluate = PRICING_REGISTRY
    if req.provider_filter and req.provider_filter.lower() != "all":
        models_to_evaluate = [m for m in PRICING_REGISTRY if m.provider.lower() == req.provider_filter.lower()]
        if not models_to_evaluate:
            models_to_evaluate = PRICING_REGISTRY

    # Calculate detailed costs for each model
    results = []
    for model in models_to_evaluate:
        # Use provider-specific token count for highest accuracy
        model_in_tokens = provider_tokens.get(model.provider, primary_input_tokens)
        cost_data = calculate_detailed_cost(
            in_tokens=model_in_tokens,
            out_tokens=req.output_tokens,
            model=model,
            cache_read_pct=req.cache_read_pct,
            is_batch=req.is_batch,
            reasoning_tokens=req.reasoning_tokens,
            calls_per_day=req.calls_per_day,
        )
        cost_data["input_tokens_used"] = model_in_tokens
        results.append(cost_data)

    # Sort results by single_call_cost ascending
    results.sort(key=lambda r: r["single_call_cost"])

    cheapest = results[0] if results else None
    most_expensive = results[-1] if results else None

    # Find flagship reference (e.g. GPT-4o or Claude 3.5/3.7 Sonnet)
    flagship = next((r for r in results if r["model"] in ("GPT-4o", "Claude 3.7 Sonnet")), results[-1] if results else None)

    # Generate actionable insights
    savings_insights = []
    if cheapest and flagship and cheapest["model"] != flagship["model"]:
        diff_monthly = flagship["monthly_cost"] - cheapest["monthly_cost"]
        pct_savings = round((1 - (cheapest["single_call_cost"] / max(0.000001, flagship["single_call_cost"]))) * 100, 1)
        savings_insights.append(
            f"Using **{cheapest['model']}** instead of **{flagship['model']}** saves **{pct_savings}%** "
            f"(${diff_monthly:,.2f}/month at {req.calls_per_day:,} calls/day)."
        )

    if req.cache_read_pct > 0:
        savings_insights.append(
            f"Prompt caching at {int(req.cache_read_pct * 100)}% hit rate is significantly reducing input token costs for supported models."
        )

    if req.is_batch:
        savings_insights.append(
            "Batch API 50% discount is currently applied to all models supporting asynchronous workflows."
        )

    # Analyze optimization potential
    optimization_info = analyze_prompt_optimization(full_text)

    return {
        "text_stats": {
            "characters": len(full_text),
            "words": len(full_text.split()),
            "lines": full_text.count("\n") + 1,
        },
        "token_counts": {
            "primary_input_tokens": primary_input_tokens,
            "provider_breakdown": provider_tokens,
            "output_tokens": req.output_tokens,
            "reasoning_tokens": req.reasoning_tokens,
            "total_tokens_per_call": primary_input_tokens + req.output_tokens + req.reasoning_tokens,
        },
        "query_params": {
            "calls_per_day": req.calls_per_day,
            "cache_read_pct": req.cache_read_pct,
            "is_batch": req.is_batch,
        },
        "models": results,
        "cheapest_model": cheapest,
        "most_expensive_model": most_expensive,
        "flagship_model": flagship,
        "savings_insights": savings_insights,
        "optimization": optimization_info,
    }


# Mount static build folder if it exists
static_path = Path(__file__).resolve().parent / "static"
if static_path.exists():
    app.mount("/assets", StaticFiles(directory=static_path / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found")
        file_target = static_path / full_path
        if full_path and file_target.is_file():
            return FileResponse(file_target)
        return FileResponse(static_path / "index.html")


def start():
    """CLI entrypoint for running the web server."""
    import uvicorn
    print("🚀 Starting LLM Cost Calculator Full Stack Web Server on http://localhost:8000 ...")
    uvicorn.run("src.server:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    start()
