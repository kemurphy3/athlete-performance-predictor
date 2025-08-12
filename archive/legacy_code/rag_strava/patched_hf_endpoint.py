from langchain_huggingface.llms import HuggingFaceEndpoint
from typing import Any, Generator, List, Optional
from langchain_core.outputs import GenerationChunk
from langchain_core.runnables import RunnableConfig

class PatchedHuggingFaceEndpoint(HuggingFaceEndpoint):
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> str:
        # Prevent duplicate stop argument for streaming
        if self.streaming:
            if "stop" in kwargs:
                kwargs.pop("stop")
            chunks = self._stream(prompt, stop, run_manager, **kwargs)
            return "".join(chunk.text for chunk in chunks)
        else:
            return super()._call(prompt, stop=stop, run_manager=run_manager, **kwargs)
