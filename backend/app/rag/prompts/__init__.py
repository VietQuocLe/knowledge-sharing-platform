from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent


@lru_cache(maxsize=32)
def load_prompt_template(filename: str) -> str:
    """
    Reads and caches a prompt template file from the prompts directory.
    Cached in memory to guarantee zero I/O overhead on repeated calls.
    """
    file_path = PROMPTS_DIR / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Prompt template file not found: {file_path}")
    return file_path.read_text(encoding="utf-8").strip()


def render_prompt(filename: str, **kwargs) -> str:
    """
    Loads the template and formats it with provided keyword arguments.
    """
    template = load_prompt_template(filename)
    if kwargs:
        return template.format(**kwargs)
    return template


__all__ = ["load_prompt_template", "render_prompt"]
