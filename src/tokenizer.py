from pathlib import Path

import tiktoken

from src.pricing import ModelPricing

VALID_EXTENSIONS = {".txt", ".md", ".py", ".json", ".csv", ".sql", ".js", ".html"}

def count_tokens(text: str, encoding_name: str = "o200k_base") -> int:
    """Count tokens locally using BPE encoding."""
    encoder = tiktoken.get_encoding(encoding_name)
    return len(encoder.encode(text))

def load_text_from_path(target: Path) -> tuple[str, int]:
    """Load text from a single file or recursively from a directory."""
    if target.is_file():
        return target.read_text(encoding="utf-8", errors="ignore"), 1

    combined_text = []
    file_count = 0
    for file_path in target.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in VALID_EXTENSIONS:
            combined_text.append(file_path.read_text(encoding="utf-8", errors="ignore"))
            file_count += 1
    return "\n".join(combined_text), file_count

def calculate_cost(input_tokens: int, output_tokens: int, model: ModelPricing) -> float:
    """Calculate total USD cost for given input and output tokens."""
    input_cost = (input_tokens / 1_000_000) * model.input_1m
    output_cost = (output_tokens / 1_000_000) * model.output_1m
    return input_cost + output_cost