import json
from collections.abc import Iterable


def dumps_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)


def load_int_list(value: str | None) -> list[int]:
    if not value:
        return []
    try:
        loaded = json.loads(value)
    except json.JSONDecodeError:
        return []
    return normalize_queue_list(loaded)


def normalize_queue_list(value: object) -> list[int]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, dict)):
        return []

    queue: list[int] = []
    for item in value:
        try:
            queue.append(int(item))
        except (TypeError, ValueError):
            continue
    return queue
