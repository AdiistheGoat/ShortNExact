"""
Generic LLM interface for supporting multiple language model providers.
This module provides an abstract base class and concrete implementations
for different LLM providers like OpenAI, Gemini, etc.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import asyncio
import openai
import google
import google.generativeai as genai


@dataclass
class LLMResponse:
    """Standardized response structure for all LLM providers."""
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LLMTool:
    """Standardized tool structure for LLM function calling."""
    type: str
    name: str
    description: str
    parameters: Optional[Dict[str, Any]] = None


@dataclass 
class LLMToolCall:
    """Standardized tool call response structure."""
    name: str
    arguments: Optional[Dict[str, Any]] = None


class LLMProvider(ABC):
    """
    Abstract base class for all LLM providers.
    
    This interface ensures consistent behavior across different providers
    while allowing for provider-specific implementations.
    """
    
    def __init__(self, api_key: str, model: str, base_url: Optional[str] = None):
        """
        Initialize the LLM provider.
        
        Args:
            api_key: The API key for the provider
            model: The model name to use
            base_url: Optional base URL for the API (for custom endpoints)
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.client = None
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the provider and validate credentials.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def generate_response(
        self,
        input_text: str,
        instructions: str,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
        tools: Optional[List[LLMTool]] = None
    ) -> LLMResponse:
        """
        Generate a response from the LLM.
        
        Args:
            input_text: The input text/prompt for the LLM
            instructions: System instructions/prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            tools: Optional list of tools for function calling
            
        Returns:
            LLMResponse: Standardized response object
        """
        pass
    
    @abstractmethod
    async def validate_api_key(self) -> bool:
        """
        Validate the API key by making a test call.
        
        Returns:
            bool: True if API key is valid, False otherwise
        """
        pass
    
    def get_provider_name(self) -> str:
        """Get the name of this provider."""
        return self.__class__.__name__.replace('Provider', '').lower()


class OpenAIProvider(LLMProvider):
    """OpenAI implementation of the LLM provider interface."""
    
    async def initialize(self) -> bool:
        """Initialize OpenAI client and validate credentials."""
        try:
            self.client = openai.AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            return await self.validate_api_key()
        except Exception as e:
            print(f"Failed to initialize OpenAI provider: {e}")
            return False
    
    async def validate_api_key(self) -> bool:
        """Validate OpenAI API key by listing models."""
        try:
            await self.client.models.list()
            return True
        except Exception as e:
            print(f"OpenAI API key validation failed: {e}")
            return False
    
    async def generate_response(
        self,
        input_text: str,
        instructions: str,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
        tools: Optional[List[LLMTool]] = None
    ) -> LLMResponse:
        """Generate response using OpenAI API."""
        try:
            messages = [
                {"role": "system", "content": instructions},
                {"role": "user", "content": input_text}
            ]
            
            # Prepare request parameters
            request_params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature
            }
            
            if max_tokens:
                request_params["max_tokens"] = max_tokens
            
            # Add tools if provided
            if tools:
                openai_tools = []
                for tool in tools:
                    openai_tool = {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description
                        }
                    }
                    if tool.parameters:
                        openai_tool["function"]["parameters"] = tool.parameters
                    openai_tools.append(openai_tool)
                
                request_params["tools"] = openai_tools
                request_params["tool_choice"] = "auto"
            
            response = await self.client.chat.completions.create(**request_params)
            
            # Handle tool calls
            if tools and response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                return LLMResponse(
                    content="",  # No content when tool is called
                    model=self.model,
                    provider="openai",
                    usage=response.usage.__dict__ if response.usage else None,
                    metadata={
                        "tool_call": LLMToolCall(
                            name=tool_call.function.name,
                            arguments=eval(tool_call.function.arguments) if tool_call.function.arguments else {}
                        )
                    }
                )
            
            # Regular text response
            content = response.choices[0].message.content
            return LLMResponse(
                content=content,
                model=self.model,
                provider="openai",
                usage=response.usage.__dict__ if response.usage else None
            )
            
        except Exception as e:
            raise Exception(f"OpenAI API call failed: {e}")


class GeminiProvider(LLMProvider):
    """Google Gemini implementation of the LLM provider interface."""
    
    async def initialize(self) -> bool:
        """Initialize Gemini client and validate credentials."""
        try:
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model)
            return await self.validate_api_key()
        except Exception as e:
            print(f"Failed to initialize Gemini provider: {e}")
            return False
    
    async def validate_api_key(self) -> bool:
        """Validate Gemini API key by making a test generation."""
        try:
            # Make a simple test call
            response = await asyncio.to_thread(
                self.client.generate_content,
                "Test",
                generation_config={'max_output_tokens': 1}
            )
            return True
        except Exception as e:
            print(f"Gemini API key validation failed: {e}")
            return False
    
    async def generate_response(
        self,
        input_text: str,
        instructions: str,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
        tools: Optional[List[LLMTool]] = None
    ) -> LLMResponse:
        """Generate response using Gemini API."""
        try:
            # Combine instructions and input for Gemini
            full_prompt = f"{instructions}\n\nInput: {input_text}"
            
            # Configure generation parameters
            generation_config = {
                'temperature': temperature,
            }
            if max_tokens:
                generation_config['max_output_tokens'] = max_tokens
            
            # Handle tools for Gemini (function calling)
            if tools:
                # Import Gemini-specific types for proper tool definition
                from google.generativeai.types import FunctionDeclaration, Tool
                
                # Convert our tools to Gemini format with proper schema
                function_declarations = []
                for tool in tools:
                    # Create function declaration with proper parameter schema
                    # Since our tools don't have input parameters, provide empty but valid schema
                    func_decl = FunctionDeclaration(
                        name=tool.name,
                        description=tool.description,
                        parameters={
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    )
                    function_declarations.append(func_decl)
                
                # Create the Tool object with all function declarations
                gemini_tools = [Tool(function_declarations=function_declarations)]
                
                response = await asyncio.to_thread(
                    self.client.generate_content,
                    full_prompt,
                    generation_config=generation_config,
                    tools=gemini_tools
                )
                
                # Check for function calls
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if candidate.content and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'function_call') and part.function_call:
                                return LLMResponse(
                                    content="",
                                    model=self.model,
                                    provider="gemini",
                                    metadata={
                                        "tool_call": LLMToolCall(
                                            name=part.function_call.name,
                                            arguments=dict(part.function_call.args) if part.function_call.args else {}
                                        )
                                    }
                                )
            else:
                response = await asyncio.to_thread(
                    self.client.generate_content,
                    full_prompt,
                    generation_config=generation_config
                )
            
            content = response.text
            return LLMResponse(
                content=content,
                model=self.model,
                provider="gemini"
            )
            
        except Exception as e:
            raise Exception(f"Gemini API call failed: {e}")


class LLMProviderFactory:
    """Factory class for creating LLM provider instances."""
    
    _providers = {
        "openai": OpenAIProvider,
        "gemini": GeminiProvider
    }
    
    @classmethod
    def create_provider(
        self,
        provider_name: str,
        api_key: str,
        model: str,
        base_url: Optional[str] = None
    ) -> LLMProvider:
        """
        Create an LLM provider instance.
        
        Args:
            provider_name: Name of the provider ("openai", "gemini")
            api_key: API key for the provider
            model: Model name to use
            base_url: Optional base URL for custom endpoints
            
        Returns:
            LLMProvider: Instance of the requested provider
            
        Raises:
            ValueError: If provider_name is not supported
        """
        provider_name = provider_name.lower()
        if provider_name not in self._providers:
            raise ValueError(f"Unsupported provider: {provider_name}")
        
        return self._providers[provider_name](api_key, model, base_url)
    
    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """Get list of supported provider names."""
        return list(cls._providers.keys())
