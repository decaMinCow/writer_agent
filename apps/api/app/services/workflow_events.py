from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class WorkflowEvent:
    name: str
    payload: dict[str, Any]


def format_sse_event(*, name: str, payload: dict[str, Any]) -> str:
    data = json.dumps(payload, ensure_ascii=False)
    return f"event: {name}\ndata: {data}\n\n"


class WorkflowEventHub:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._subscribers: dict[uuid.UUID, set[asyncio.Queue[WorkflowEvent]]] = {}

    async def subscribe(self, *, run_id: uuid.UUID) -> asyncio.Queue[WorkflowEvent]:
        queue: asyncio.Queue[WorkflowEvent] = asyncio.Queue(maxsize=200)
        async with self._lock:
            self._subscribers.setdefault(run_id, set()).add(queue)
        return queue

    async def unsubscribe(self, *, run_id: uuid.UUID, queue: asyncio.Queue[WorkflowEvent]) -> None:
        async with self._lock:
            subscribers = self._subscribers.get(run_id)
            if not subscribers:
                return
            subscribers.discard(queue)
            if not subscribers:
                self._subscribers.pop(run_id, None)

    async def publish(self, *, run_id: uuid.UUID, name: str, payload: dict[str, Any]) -> None:
        async with self._lock:
            queues = list(self._subscribers.get(run_id, set()))

        if not queues:
            return

        event = WorkflowEvent(name=name, payload=payload)
        for queue in queues:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    continue

