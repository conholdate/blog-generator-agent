"""
Centralized LLM Service Layer
Handles all LLM API calls across the project with consistent configuration and error handling.
Uses self-hosted LLM via OpenAI-compatible API (Professionalize).
"""
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel, ModelSettings
from config import settings
from typing import Optional, Dict, Any, List
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
        model: Optional[str] = None
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
            Runner result object with final_output
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
                model_settings=ModelSettings(temperature=temperature)
            )
            
            result = await Runner.run(agent, context, max_turns=max_turns)
            return result
            
        except Exception as e:
            logger.error(f"Agent run failed: {e}")
            raise
    
    # ─────────────────────────────────────────────────────────────────────────
    # SIMPLE COMPLETION CALLS (for targeted corrections, validations, etc.)
    # ─────────────────────────────────────────────────────────────────────────
    
    async def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system: Optional[str] = None
    ) -> str:
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
            The generated text response
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
            
            # Debug logging - print full response structure
            print(f"\n🔍 DEBUG: LLM Response received")
            print(f"   Response type: {type(response)}")
            print(f"   Has choices: {hasattr(response, 'choices')}")
            
            if hasattr(response, 'choices') and response.choices:
                print(f"   Choices count: {len(response.choices)}")
                first_choice = response.choices[0]
                print(f"   First choice type: {type(first_choice)}")
                print(f"   First choice attributes: {dir(first_choice)}")
                print(f"   Has message: {hasattr(first_choice, 'message')}")
                
                if hasattr(first_choice, 'message'):
                    msg = first_choice.message
                    print(f"   Message type: {type(msg)}")
                    print(f"   Message attributes: {dir(msg)}")
                    print(f"   Message content: {msg.content}")
                    print(f"   Message dict: {msg.model_dump() if hasattr(msg, 'model_dump') else 'N/A'}")
                    
                    # Check for alternative fields
                    if hasattr(msg, 'text'):
                        print(f"   Message.text: {msg.text}")
                    if hasattr(msg, 'content_text'):
                        print(f"   Message.content_text: {msg.content_text}")
                    
                print(f"   First choice dict: {first_choice.model_dump() if hasattr(first_choice, 'model_dump') else 'N/A'}")
            
            print(f"   Full response dict: {response.model_dump() if hasattr(response, 'model_dump') else response}\n")
            
            logger.info(f"LLM Response type: {type(response)}")
            logger.info(f"LLM Response: {response}")
            
            # Robust response extraction with validation
            if not response or not response.choices:
                logger.error("Empty response from LLM")
                logger.error(f"Response object: {response}")
                raise ValueError("LLM returned empty response")
            
            logger.info(f"Choices count: {len(response.choices)}")
            logger.info(f"First choice: {response.choices[0]}")
            logger.info(f"Message: {response.choices[0].message}")
            logger.info(f"Message content: {response.choices[0].message.content}")
            
            content = response.choices[0].message.content
            
            if content is None:
                logger.error("LLM returned None content")
                logger.error(f"Full response: {response}")
                logger.error(f"Response dict: {response.model_dump() if hasattr(response, 'model_dump') else 'N/A'}")
                raise ValueError("LLM returned None content")
            
            return content.strip()
            
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
    ) -> Optional[str]:
        """
        Completion with automatic retry on failure.
        
        Args:
            prompt: The user prompt
            max_retries: Maximum number of retry attempts
            **kwargs: Additional arguments passed to complete()
            
        Returns:
            Generated text or None if all retries fail
        """
        for attempt in range(1, max_retries + 1):
            try:
                return await self.complete(prompt, **kwargs)
            except Exception as e:
                logger.warning(f"Attempt {attempt}/{max_retries} failed: {e}")
                if attempt == max_retries:
                    logger.error(f"All {max_retries} attempts failed")
                    return None
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


async def complete(prompt: str, **kwargs) -> str:
    """Convenience function for simple completions"""
    return await llm_service.complete(prompt, **kwargs)


async def complete_with_retry(prompt: str, **kwargs) -> Optional[str]:
    """Convenience function for completions with retry"""
    return await llm_service.complete_with_retry(prompt, **kwargs)
