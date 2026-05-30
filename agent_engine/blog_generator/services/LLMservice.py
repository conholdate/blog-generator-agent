"""
Centralized LLM Service Layer
Handles all LLM API calls across the project with consistent configuration and error handling.
Uses self-hosted LLM via OpenAI-compatible API (Professionalize).
"""
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel, ModelSettings
from config import settings
from typing import Optional, Dict, Any, List, Tuple
import asyncio
import logging

logger = logging.getLogger(__name__)


class LLMService:
    """
    Centralized service for all LLM operations.
    Uses self-hosted LLM via OpenAI-compatible API.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern - only one instance across the application"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize LLM client only once"""
        if self._initialized:
            return
            
        # Self-hosted LLM client (OpenAI-compatible API)
        self.openai_client = AsyncOpenAI(
            base_url=settings.PROFESSIONALIZE_BASE_URL,
            api_key=settings.PROFESSIONALIZE_API_KEY_2
        )
        
        # OpenAI Chat Completions Model for agents
        self.agent_model = OpenAIChatCompletionsModel(
            model=settings.PROFESSIONALIZE_LLM_MODEL,
            openai_client=self.openai_client
        )
        
        self._initialized = True
        logger.info("LLM Service initialized with self-hosted model")
    
    # ─────────────────────────────────────────────────────────────────────────
    # AGENT-BASED CALLS (for complex multi-turn workflows)
    # ─────────────────────────────────────────────────────────────────────────
    
    async def run_agent(
        self,
        instructions: str,
        context: str,
        agent_name: str = "assistant",
        temperature: float = 0.6,
        max_turns: int = 10,
        model: Optional[str] = None,
        max_tokens: int = 16000 
    ) -> Any:
        """
        Run an OpenAI Agent with instructions and context.
        
        Args:
            instructions: System prompt/instructions for the agent
            context: User message/context to process
            agent_name: Name for the agent (for logging)
            temperature: Model temperature (0.0-1.0)
            max_turns: Maximum conversation turns
            model: Optional model override (uses default if None)
            
        Returns:
            Runner result object with final_output and token_usage dict:
            result.token_usage = {"input_tokens": int, "output_tokens": int, "total_tokens": int}
        """
        try:
            # Use custom model if provided, otherwise use default
            agent_model = self.agent_model
            if model:
                agent_model = OpenAIChatCompletionsModel(
                    model=model,
                    openai_client=self.openai_client
                )
            
            agent = Agent(
                name=agent_name,
                instructions=instructions,
                model=agent_model,
                model_settings=ModelSettings(temperature=temperature,max_tokens=max_tokens)
            )
            
            result = await Runner.run(agent, context, max_turns=max_turns)
            print(f"DEBUG raw result: {result}", flush=True)
            print(f"DEBUG final_output: {result.final_output}", flush=True)
            print(f"DEBUG raw_responses count: {len(getattr(result, 'raw_responses', []))}", flush=True)
            for i, raw in enumerate(getattr(result, 'raw_responses', [])):
                print(f"DEBUG raw_response[{i}]: {raw}", flush=True)
                print(f"DEBUG raw_response choices: {getattr(raw, 'choices', 'NO CHOICES')}", flush=True)
            # ── Aggregate token usage across all turns ──────────────────────
            input_tokens = 0
            output_tokens = 0
            for raw in getattr(result, "raw_responses", []):
                usage = getattr(raw, "usage", None)
                if usage:
                    input_tokens  += getattr(usage, "input_tokens",  0) or getattr(usage, "prompt_tokens",     0)
                    output_tokens += getattr(usage, "output_tokens", 0) or getattr(usage, "completion_tokens", 0)

            result.token_usage = {
                "input_tokens":  input_tokens,
                "output_tokens": output_tokens,
                "total_tokens":  input_tokens + output_tokens
            }
            logger.debug(f"[{agent_name}] token_usage: {result.token_usage}")
            # ───────────────────────────────────────────────────────────────

            return result
            
        except Exception as e:
            logger.error(f"Agent run failed: {e}")
            print(f"error in run_agent: {e}")
            raise
    
    # ─────────────────────────────────────────────────────────────────────────
    # SIMPLE COMPLETION CALLS (for targeted corrections, validations, etc.)
    # ─────────────────────────────────────────────────────────────────────────
    
    async def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        system: Optional[str] = None
    ) -> Tuple[str, Dict[str, int]]:
        """
        Simple completion call using self-hosted LLM (OpenAI-compatible API).
        Best for: Quick corrections, validations, simple generations.

        Args:
            prompt: The user prompt/message
            model: Model name (uses default if None)
            temperature: Model temperature
            max_tokens: Maximum tokens in response
            system: Optional system message

        Returns:
            Tuple of (generated_text, token_usage_dict)
            token_usage = {"input_tokens": int, "output_tokens": int, "total_tokens": int}
        """
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            response = await self.openai_client.chat.completions.create(
                model=model or settings.PROFESSIONALIZE_LLM_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            if not response or not response.choices:
                logger.error("Empty response from LLM")
                raise ValueError("LLM returned empty response")

            content = response.choices[0].message.content

            # Fallback: reasoning models sometimes put output in reasoning_content
            # when they run out of tokens before producing actual content
            if content is None:
                provider_fields = getattr(response.choices[0].message, 'provider_specific_fields', {}) or {}
                reasoning = provider_fields.get('reasoning_content') or provider_fields.get('reasoning')
                if reasoning:
                    logger.warning("content was None, falling back to reasoning_content")
                    content = reasoning
                else:
                    logger.error(f"LLM returned None content. Full response: {response.model_dump() if hasattr(response, 'model_dump') else response}")
                    raise ValueError("LLM returned None content and no reasoning fallback")

            # ── Extract token usage from response ───────────────────────────
            usage = getattr(response, "usage", None)
            token_usage = {
                "input_tokens":  getattr(usage, "prompt_tokens",     0) if usage else 0,
                "output_tokens": getattr(usage, "completion_tokens", 0) if usage else 0,
                "total_tokens":  getattr(usage, "total_tokens",      0) if usage else 0,
            }
            logger.debug(f"[complete] token_usage: {token_usage}")
            # ───────────────────────────────────────────────────────────────

            return content.strip(), token_usage

        except Exception as e:
            logger.error(f"Completion call failed: {e}")
            raise
    
    # ─────────────────────────────────────────────────────────────────────────
    # RETRY LOGIC (for handling transient failures)
    # ─────────────────────────────────────────────────────────────────────────
    
    async def complete_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        **kwargs
    ) -> Tuple[Optional[str], Dict[str, int]]:
        """
        Completion with automatic retry on failure.
        
        Args:
            prompt: The user prompt
            max_retries: Maximum number of retry attempts
            **kwargs: Additional arguments passed to complete()
            
        Returns:
            Tuple of (generated_text_or_None, token_usage_dict)
        """
        for attempt in range(1, max_retries + 1):
            try:
                return await self.complete(prompt, **kwargs)
            except Exception as e:
                logger.warning(f"Attempt {attempt}/{max_retries} failed: {e}")
                if attempt == max_retries:
                    logger.error(f"All {max_retries} attempts failed")
                    return None, {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    # ─────────────────────────────────────────────────────────────────────────
    # BATCH OPERATIONS (for processing multiple requests efficiently)
    # ─────────────────────────────────────────────────────────────────────────
    
    async def complete_batch(
        self,
        prompts: List[str],
        **kwargs
    ) -> List[Optional[str]]:
        """
        Process multiple prompts concurrently.
        
        Args:
            prompts: List of prompts to process
            **kwargs: Arguments passed to complete()
            
        Returns:
            List of responses (None for failed requests)
        """
        tasks = [self.complete(prompt, **kwargs) for prompt in prompts]
        return await asyncio.gather(*tasks, return_exceptions=True)


# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL INSTANCE (singleton)
# ─────────────────────────────────────────────────────────────────────────────

llm_service = LLMService()


# ─────────────────────────────────────────────────────────────────────────────
# CONVENIENCE FUNCTIONS (for quick imports)
# ─────────────────────────────────────────────────────────────────────────────

async def run_agent(instructions: str, context: str, **kwargs) -> Any:
    """Convenience function for running agents"""
    return await llm_service.run_agent(instructions, context, **kwargs)


async def complete(prompt: str, **kwargs) -> Tuple[str, Dict[str, int]]:
    """Convenience function for simple completions"""
    return await llm_service.complete(prompt, **kwargs)


async def complete_with_retry(prompt: str, **kwargs) -> Tuple[Optional[str], Dict[str, int]]:
    """Convenience function for completions with retry"""
    return await llm_service.complete_with_retry(prompt, **kwargs)