from __future__ import annotations


def split_paragraphs(text: str) -> list[str]:
    cleaned = (text or "").strip()
    if not cleaned:
        return []
    return [p.strip() for p in cleaned.split("\n\n") if p.strip()]


def join_paragraphs(paragraphs: list[str]) -> str:
    return "\n\n".join([p.strip() for p in paragraphs if p.strip()]).strip()


def numbered_paragraphs(text: str) -> tuple[list[str], str]:
    paragraphs = split_paragraphs(text)
    lines = []
    for idx, paragraph in enumerate(paragraphs, start=1):
        lines.append(f"[{idx}] {paragraph}")
    return paragraphs, "\n\n".join(lines)


def apply_replacements(paragraphs: list[str], replacements: dict[int, str]) -> list[str]:
    updated = list(paragraphs)
    for idx, new_text in replacements.items():
        if idx < 1 or idx > len(updated):
            continue
        updated[idx - 1] = new_text.strip()
    return updated

