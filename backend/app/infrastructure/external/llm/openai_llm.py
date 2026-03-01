from typing import List, Dict, Any, Optional, AsyncGenerator, Tuple
from openai import AsyncOpenAI, RateLimitError
from app.domain.external.llm import LLM
from app.core.config import get_settings
import logging
import asyncio
import re


logger = logging.getLogger(__name__)

class OpenAILLM(LLM):
    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=settings.api_key,
            base_url=settings.api_base
        )
        
        self._model_name = settings.model_name
        self._temperature = settings.temperature
        self._max_tokens = settings.max_tokens
        logger.info(f"Initialized OpenAI LLM with model: {self._model_name}")
    
    @property
    def model_name(self) -> str:
        return self._model_name
    
    @property
    def temperature(self) -> float:
        return self._temperature
    
    @property
    def max_tokens(self) -> int:
        return self._max_tokens

    def _build_kwargs(self, messages, tools=None, response_format=None, tool_choice=None, stream=False):
        kwargs = {
            "model": self._model_name,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
            "messages": messages,
        }
        if stream:
            kwargs["stream"] = True
        if tools:
            kwargs["tools"] = tools
            if tool_choice:
                kwargs["tool_choice"] = tool_choice
        else:
            if response_format:
                kwargs["response_format"] = response_format
        return kwargs

    def _sanitize_tool_calls(self, tool_calls_dict):
        """Sanitize and assemble tool calls from streaming dict"""
        result = []
        for i in sorted(tool_calls_dict.keys()):
            tc = tool_calls_dict[i]
            name = tc["function"].get("name", "")
            m = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)', name)
            if m:
                if name != m.group(1):
                    logger.warning(f"Sanitized malformed tool name: {name!r} → {m.group(1)!r}")
                tc["function"]["name"] = m.group(1)
                result.append(tc)
            else:
                logger.warning(f"Skipping tool call with unparseable name: {name!r}")
        return result or None

    async def ask(self, messages: List[Dict[str, str]],
                tools: Optional[List[Dict[str, Any]]] = None,
                response_format: Optional[Dict[str, Any]] = None,
                tool_choice: Optional[str] = None) -> Dict[str, Any]:
        """Send chat request to OpenAI API with retry mechanism"""
        max_retries = 5
        base_delay = 2.0

        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.info(f"Retrying LLM request (attempt {attempt + 1}/{max_retries + 1}) after {delay:.0f}s delay")
                    await asyncio.sleep(delay)

                kwargs = self._build_kwargs(messages, tools, response_format, tool_choice)
                logger.debug(f"Sending request, model: {self._model_name}, attempt: {attempt + 1}")

                response = await self.client.chat.completions.create(**kwargs)

                logger.debug(f"LLM response received: model={self._model_name}")

                if not response or not response.choices:
                    error_msg = f"LLM returned empty response (no choices) on attempt {attempt + 1}"
                    logger.error(error_msg)
                    if attempt == max_retries:
                        raise ValueError(f"Failed after {max_retries + 1} attempts: {error_msg}")
                    continue

                result = response.choices[0].message.model_dump()

                if result.get("tool_calls"):
                    cleaned_tool_calls = []
                    for tc in result["tool_calls"]:
                        if tc.get("function") and tc["function"].get("name"):
                            raw_name = tc["function"]["name"]
                            clean_name = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)', raw_name)
                            if clean_name:
                                if raw_name != clean_name.group(1):
                                    logger.warning(f"Sanitized malformed tool name: {raw_name!r} → {clean_name.group(1)!r}")
                                tc["function"]["name"] = clean_name.group(1)
                                cleaned_tool_calls.append(tc)
                            else:
                                logger.warning(f"Skipping tool call with unparseable name: {raw_name!r}")
                        else:
                            cleaned_tool_calls.append(tc)
                    result["tool_calls"] = cleaned_tool_calls if cleaned_tool_calls else None

                return result

            except RateLimitError as e:
                rate_limit_delay = 30.0 * (attempt + 1)
                logger.warning(f"Rate limit hit (attempt {attempt + 1}), waiting {rate_limit_delay:.0f}s before retry...")
                if attempt == max_retries:
                    raise e
                await asyncio.sleep(rate_limit_delay)
                continue

            except Exception as e:
                error_msg = f"Error calling LLM API on attempt {attempt + 1}: {str(e)}"
                logger.error(error_msg)
                if attempt == max_retries:
                    raise e
                continue

    async def ask_stream(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        tool_choice: Optional[str] = None
    ) -> AsyncGenerator[Tuple[str, Any], None]:
        """Stream response from LLM, yielding tokens then final result."""
        max_retries = 3
        base_delay = 2.0

        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.info(f"Retrying streaming LLM request (attempt {attempt + 1}) after {delay:.0f}s")
                    await asyncio.sleep(delay)

                kwargs = self._build_kwargs(messages, tools, response_format, tool_choice, stream=True)
                logger.debug(f"Sending streaming request, model: {self._model_name}")

                content = ""
                tool_calls_dict: Dict[int, Dict] = {}

                stream = await self.client.chat.completions.create(**kwargs)
                async for chunk in stream:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta

                    if delta.content:
                        content += delta.content
                        yield ("token", delta.content)

                    if delta.tool_calls:
                        for tc_delta in delta.tool_calls:
                            idx = tc_delta.index
                            if idx not in tool_calls_dict:
                                tool_calls_dict[idx] = {
                                    "id": "",
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""}
                                }
                            if tc_delta.id:
                                tool_calls_dict[idx]["id"] = tc_delta.id
                            if tc_delta.function:
                                if tc_delta.function.name:
                                    tool_calls_dict[idx]["function"]["name"] += tc_delta.function.name
                                if tc_delta.function.arguments:
                                    tool_calls_dict[idx]["function"]["arguments"] += tc_delta.function.arguments

                tool_calls = self._sanitize_tool_calls(tool_calls_dict) if tool_calls_dict else None
                result = {
                    "role": "assistant",
                    "content": content if content else None,
                    "tool_calls": tool_calls
                }
                yield ("result", result)
                return

            except RateLimitError as e:
                rate_limit_delay = 30.0 * (attempt + 1)
                logger.warning(f"Rate limit hit on stream (attempt {attempt + 1}), waiting {rate_limit_delay:.0f}s...")
                if attempt == max_retries:
                    raise e
                await asyncio.sleep(rate_limit_delay)

            except Exception as e:
                logger.error(f"Error in streaming LLM request (attempt {attempt + 1}): {str(e)}")
                if attempt == max_retries:
                    raise e
