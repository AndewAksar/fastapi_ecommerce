"""Utilities for building context snippets from the knowledge base."""

from pathlib import Path


def load_context_snippets(base: Path, max_chars: int = 6000) -> str:
    """Collect compact snippets from Markdown files within ``knowledge``.

    The function walks through ``knowledge`` directory inside ``base`` and
    concatenates the first few paragraphs from each Markdown document,
    prepending the filename as a section heading. The combined text is
    truncated to ``max_chars`` symbols to keep prompt sizes manageable.

    Args:
        base: Root directory that contains the ``knowledge`` folder.
        max_chars: Maximum number of characters to include in the result.

    Returns:
        Aggregated snippet string limited by ``max_chars`` characters.
    """

    knowledge_dir = base / "knowledge"
    if not knowledge_dir.exists():
        return ""

    parts: list[str] = []

    for file_path in sorted(knowledge_dir.glob("*.md")):
        text = file_path.read_text(encoding="utf-8")
        head_sections = text.split("\n\n")[:3]
        snippet = "\n\n".join(head_sections).strip()
        parts.append(f"\n# {file_path.name}\n{snippet}")

    full = "\n\n".join(parts).strip()
    return full[:max_chars]
