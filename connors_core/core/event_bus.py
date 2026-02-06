"""
Event Bus

Simple in-memory pub/sub for bot events.
"""

import asyncio
from typing import AsyncIterator, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class Event:
    """Event data"""

    type: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "type": self.type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }


class EventBus:
    """
    Simple in-memory pub/sub for bot events

    Events are broadcast to all subscribers (WebSocket connections, loggers, etc.)
    """

    def __init__(self):
        self.subscribers: List[asyncio.Queue] = []

    async def emit(self, event_type: str, data: Dict[str, Any]):
        """
        Broadcast event to all subscribers (NON-BLOCKING)

        Uses put_nowait() for zero-latency, fire-and-forget emission.
        Bot execution is NEVER blocked by event bus, API, or WebSocket issues.

        Args:
            event_type: Type of event (e.g., "bot_started", "trade_executed")
            data: Event data
        """
        if not self.subscribers:
            # No subscribers, skip immediately (zero overhead)
            return

        event = Event(type=event_type, data=data)

        # Broadcast to all subscribers (NON-BLOCKING)
        dead_queues = []
        for queue in self.subscribers:
            try:
                # put_nowait() = immediate, never blocks bot execution
                queue.put_nowait(event)
            except asyncio.QueueFull:
                # Queue full (slow consumer) - drop event, never block bot
                pass
            except Exception:
                # Queue broken/closed - mark for removal
                dead_queues.append(queue)

        # Clean up dead subscribers (doesn't affect bot performance)
        for queue in dead_queues:
            try:
                self.subscribers.remove(queue)
            except ValueError:
                pass

    async def subscribe(self) -> AsyncIterator[Event]:
        """
        Subscribe to event stream

        Yields:
            Event objects as they occur
        """
        queue = asyncio.Queue(maxsize=1000)
        self.subscribers.append(queue)

        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            # Clean up when subscriber disconnects
            if queue in self.subscribers:
                self.subscribers.remove(queue)

    def subscriber_count(self) -> int:
        """Get number of active subscribers"""
        return len(self.subscribers)

    def clear(self):
        """Clear all subscribers"""
        self.subscribers.clear()


# Global event bus instance
event_bus = EventBus()
