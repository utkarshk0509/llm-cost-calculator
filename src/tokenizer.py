from pathlib import Path

import tiktoken

from src.pricing import ModelPricing

VALID_EXTENSIONS = {".txt", ".md", ".py", ".json", ".csv", ".sql", ".js", ".html"}


def count_tokens(text: str, enc_name: str = "o200k_base") -> int:
    # o200k_base (GPT-4o) serves as a fast local proxy for modern BPE tokenizers
    # across providers when exact vendor tokenizers are not bundled.
    enc = tiktoken.get_encoding(enc_name)
    return len(enc.encode(text))


def load_text_from_path(target: Path) -> tuple[str, int]:
    if target.is_file():
        # Ignore decode errors so binary artifacts or non-UTF8 encodings don't crash scans
        return target.read_text(encoding="utf-8", errors="ignore"), 1

    chunks = []
    f_count = 0
    for f_path in target.rglob("*"):
        if f_path.is_file() and f_path.suffix.lower() in VALID_EXTENSIONS:
            chunks.append(f_path.read_text(encoding="utf-8", errors="ignore"))
            f_count += 1
    return "\n".join(chunks), f_count


def calculate_cost(in_tokens: int, out_tokens: int, model: ModelPricing) -> float:
    in_cost = (in_tokens / 1_000_000) * model.input_1m
    out_cost = (out_tokens / 1_000_000) * model.output_1m
    return in_cost + out_cost