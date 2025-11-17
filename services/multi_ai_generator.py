"""
Multi-AI Code Generator
Automatically falls back to Gemini if OpenAI quota is exceeded
"""
import asyncio
import logging
from typing import Optional
import google.generativeai as genai
from openai import AsyncOpenAI, OpenAIError

logger = logging.getLogger(__name__)


class ResponsesWrapper:
    """Wrapper to make MultiAIGenerator compatible with OpenAI client interface"""
    
    def __init__(self, generator):
        self.generator = generator
    
    async def create(self, model: str, input: str):
        """Create a response using multi-AI generator"""
        text = await self.generator.generate(input)
        
        # Return object that mimics OpenAI response
        class Response:
            def __init__(self, text):
                self.output_text = text
        
        return Response(text)


class MultiAIGenerator:
    """
    Code generator that tries OpenAI first, falls back to Gemini if quota exceeded
    """
    
    def __init__(self, openai_key: str, gemini_key: Optional[str] = None, model: str = "gpt-5", timeout: int = 900):
        """
        Initialize multi-AI generator
        
        Args:
            openai_key: OpenAI API key
            gemini_key: Google Gemini API key (optional)
            model: OpenAI model to use
            timeout: Timeout for API calls
        """
        self.openai_client = AsyncOpenAI(api_key=openai_key, timeout=timeout)
        self.openai_model = model
        self.timeout = timeout
        
        # Create responses wrapper for compatibility
        self.responses = ResponsesWrapper(self)
        
        # Initialize Gemini if key provided
        self.gemini_available = False
        if gemini_key:
            try:
                genai.configure(api_key=gemini_key)
                self.gemini_model = genai.GenerativeModel('gemini-pro')
                self.gemini_available = True
                logger.info("Gemini fallback enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini: {e}")
    
    async def generate(self, prompt: str) -> str:
        """
        Generate code using OpenAI, fallback to Gemini if quota exceeded
        
        Args:
            prompt: User prompt
            
        Returns:
            Generated code
        """
        # Try OpenAI first
        try:
            logger.info("Attempting code generation with OpenAI")
            response = await asyncio.wait_for(
                self.openai_client.responses.create(
                    model=self.openai_model,
                    input=prompt
                ),
                timeout=self.timeout
            )
            logger.info("✅ OpenAI generation successful")
            return response.output_text
            
        except OpenAIError as e:
            error_str = str(e).lower()
            
            # Check if it's a quota error
            if 'quota' in error_str or '429' in error_str or 'insufficient_quota' in error_str:
                logger.warning("⚠️  OpenAI quota exceeded, falling back to Gemini")
                
                if self.gemini_available:
                    return await self._generate_with_gemini(prompt)
                else:
                    logger.error("❌ Gemini not available, cannot fallback")
                    raise Exception(
                        "OpenAI quota exceeded and Gemini fallback not configured. "
                        "Please add GEMINI_API_KEY to .env file or add credits to OpenAI account."
                    )
            else:
                # Other OpenAI error, re-raise
                raise
    
    async def _generate_with_gemini(self, prompt: str) -> str:
        """
        Generate code using Google Gemini
        
        Args:
            prompt: User prompt
            
        Returns:
            Generated code
        """
        try:
            logger.info("🔄 Generating with Gemini...")
            
            # Run Gemini in thread pool (it's synchronous)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.gemini_model.generate_content,
                prompt
            )
            
            logger.info("✅ Gemini generation successful")
            return response.text
            
        except Exception as e:
            logger.error(f"❌ Gemini generation failed: {e}")
            raise Exception(f"Both OpenAI and Gemini failed. Gemini error: {str(e)}")
    
    async def generate_app_name(self, prompt: str) -> str:
        """
        Generate app name using available AI
        
        Args:
            prompt: User's app description
            
        Returns:
            App name
        """
        name_prompt = f"""Based on this app description, generate a simple one-word app name.
The name should be:
- One word only (no spaces, no hyphens)
- Lowercase
- Alphanumeric only
- Descriptive of the app's purpose
- Maximum 15 characters

App description: {prompt}

Respond with ONLY the app name, nothing else."""
        
        try:
            response = await self.generate(name_prompt)
            app_name = response.strip().lower()
            
            # Clean the name
            import re
            app_name = re.sub(r'[^a-z0-9]', '', app_name)
            
            if not app_name or len(app_name) < 2:
                app_name = "myapp"
            elif len(app_name) > 15:
                app_name = app_name[:15]
            
            return app_name
            
        except Exception as e:
            logger.warning(f"Failed to generate app name: {e}, using default")
            return "myapp"
