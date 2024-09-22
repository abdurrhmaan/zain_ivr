import asyncio

async def wait_for_event(condition: asyncio.Condition, timeout: float):
    try:
        async with asyncio.timeout(timeout):
            async with condition:
                await condition.wait()
    except asyncio.TimeoutError:
        pass