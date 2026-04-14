from __future__ import annotations


def convert_int(value: str | int) -> int:
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except ValueError:
        return int(value, base=16)
