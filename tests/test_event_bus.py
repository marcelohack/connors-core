"""Tests for EventBus pub/sub system."""

import asyncio

import pytest

from connors_core.core.event_bus import Event, EventBus, event_bus


class TestEvent:
    """Tests for Event dataclass."""

    def test_event_creation(self):
        event = Event(type="trade_executed", data={"symbol": "AAPL", "pnl": 150.0})
        assert event.type == "trade_executed"
        assert event.data["symbol"] == "AAPL"
        assert event.timestamp is not None

    def test_event_to_dict(self):
        event = Event(type="bot_started", data={"bot_id": "test-bot"})
        d = event.to_dict()
        assert d["type"] == "bot_started"
        assert d["data"]["bot_id"] == "test-bot"
        assert "timestamp" in d
        assert isinstance(d["timestamp"], str)  # isoformat string


class TestEventBus:
    """Tests for EventBus pub/sub."""

    def setup_method(self):
        self.bus = EventBus()

    def test_initial_state(self):
        assert self.bus.subscriber_count() == 0

    @pytest.mark.asyncio
    async def test_emit_no_subscribers(self):
        # Should not raise even with no subscribers
        await self.bus.emit("test_event", {"key": "value"})

    @pytest.mark.asyncio
    async def test_subscribe_and_receive(self):
        received = []

        async def collector():
            async for event in self.bus.subscribe():
                received.append(event)
                if len(received) >= 2:
                    break

        task = asyncio.create_task(collector())
        # Give subscriber time to register
        await asyncio.sleep(0.01)

        assert self.bus.subscriber_count() == 1

        await self.bus.emit("event_a", {"n": 1})
        await self.bus.emit("event_b", {"n": 2})

        await asyncio.wait_for(task, timeout=1.0)

        assert len(received) == 2
        assert received[0].type == "event_a"
        assert received[1].type == "event_b"
        assert received[0].data["n"] == 1

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self):
        queues = []
        for _ in range(3):
            q = asyncio.Queue(maxsize=1000)
            self.bus.subscribers.append(q)
            queues.append(q)

        assert self.bus.subscriber_count() == 3

        await self.bus.emit("broadcast", {"msg": "hello"})

        for q in queues:
            event = q.get_nowait()
            assert event.type == "broadcast"
            assert event.data["msg"] == "hello"

    @pytest.mark.asyncio
    async def test_full_queue_drops_event(self):
        q = asyncio.Queue(maxsize=1)
        self.bus.subscribers.append(q)

        # Fill the queue
        await self.bus.emit("first", {})
        # This should be dropped (queue full), not raise
        await self.bus.emit("second", {})

        assert q.qsize() == 1
        event = q.get_nowait()
        assert event.type == "first"

    @pytest.mark.asyncio
    async def test_dead_queue_cleanup(self):
        # Simulate a broken queue by creating one that raises on put_nowait
        class BrokenQueue(asyncio.Queue):
            def put_nowait(self, item):
                raise RuntimeError("broken")

        broken = BrokenQueue()
        good = asyncio.Queue(maxsize=1000)
        self.bus.subscribers.extend([broken, good])

        assert self.bus.subscriber_count() == 2
        await self.bus.emit("test", {"data": 1})

        # Broken queue should be removed
        assert self.bus.subscriber_count() == 1
        # Good queue should still get the event
        event = good.get_nowait()
        assert event.type == "test"

    @pytest.mark.asyncio
    async def test_subscriber_cleanup_on_cancel(self):
        async def subscriber():
            async for _ in self.bus.subscribe():
                pass

        task = asyncio.create_task(subscriber())
        await asyncio.sleep(0.01)
        assert self.bus.subscriber_count() == 1

        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        assert self.bus.subscriber_count() == 0

    def test_clear(self):
        for _ in range(5):
            self.bus.subscribers.append(asyncio.Queue())
        assert self.bus.subscriber_count() == 5

        self.bus.clear()
        assert self.bus.subscriber_count() == 0


class TestGlobalEventBus:
    """Tests for the global event_bus singleton."""

    def test_global_instance_exists(self):
        assert isinstance(event_bus, EventBus)

    def test_global_instance_is_singleton(self):
        from connors_core.core.event_bus import event_bus as bus2

        assert event_bus is bus2
