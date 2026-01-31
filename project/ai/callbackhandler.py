from typing import Any
from uuid import UUID
import asyncio
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import GenerationChunk, ChatGenerationChunk, LLMResult


class CustomCallbackHandler(AsyncCallbackHandler):
    def __init__(self , queue : asyncio.Queue):
        self.queue = queue

    async def __aiter__(self):
        while True:
            # get current token from queue
            token = await self.queue.get()
            if token is None:
                break

            yield token
    async def on_llm_new_token(
        self,
        token: str,
        *,
        chunk: GenerationChunk | ChatGenerationChunk | None = None,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        self.queue.put_nowait(token)
        print(f"chunk: {chunk}")


    async def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        print("Last token taken")
        await self.queue.put(None)

    async def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        print("An error occurded while getting tokens")
        await self.queue.put(None)


    def copy(self):
        return CustomCallbackHandler(queue= self.queue)


