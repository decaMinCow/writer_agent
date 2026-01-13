from __future__ import annotations


def format_exception_chain(exc: BaseException, *, max_depth: int = 8) -> str:
    parts: list[str] = []
    current: BaseException | None = exc
    seen: set[int] = set()

    while current is not None and id(current) not in seen and len(parts) < max_depth:
        seen.add(id(current))
        message = str(current).strip()
        if message:
            parts.append(f"{current.__class__.__name__}: {message}")
        else:
            parts.append(f"{current.__class__.__name__}")
        current = current.__cause__ or current.__context__

    return " <- ".join(parts)

