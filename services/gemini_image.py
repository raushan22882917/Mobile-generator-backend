"""AI Image Generation Service with Gemini and OpenAI Fallback"""
import os
import base64
import requests
from typing import Optional, Tuple
from io import BytesIO

class AIImageGenerator:
    def __init__(self, gemini_api_key: str = None, openai_api_key: str = None):
        """
        Initialize AI Image Generator with fallback support
        
        Args:
            gemini_api_key: Gemini API key (optional)
            openai_api_key: OpenAI API key (optional)
        """
        # Load from config if not provided
        if gemini_api_key is None or openai_api_key is None:
            try:
                from config import settings
                gemini_api_key = gemini_api_key or settings.gemini_api_key
                openai_api_key = openai_api_key or settings.openai_api_key
            except Exception:
                pass
        
        self.gemini_api_key = gemini_api_key
        self.openai_api_key = openai_api_key
        
        # Try to configure Gemini
        self.gemini_available = False
        if gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_api_key)
                self.genai = genai
                self.gemini_available = True
                print("✓ Gemini AI configured for image generation (gemini-2.5-flash-image)")
            except ImportError:
                print("⚠ google-generativeai not installed. Install: pip install google-generativeai")
            except Exception as e:
                print(f"⚠ Gemini configuration failed: {e}")
        
        # Check OpenAI availability
        self.openai_available = False
        if openai_api_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=openai_api_key)
                self.openai_available = True
                print("✓ OpenAI configured for image generation (fallback)")
            except ImportError:
                print("⚠ openai package not installed")
            except Exception as e:
                print(f"⚠ OpenAI configuration failed: {e}")
    
    def generate_image(self, prompt: str) -> Tuple[Optional[bytes], str]:
        """
        Generate an image using AI with fallback support
        
        Tries Gemini first, falls back to OpenAI DALL-E if Gemini fails
        
        Args:
            prompt: Text description of the image to generate
            
        Returns:
            Tuple of (image_bytes, provider_name) or (None, error_message)
        """
        errors = []
        
        # Try Gemini first (if available)
        if self.gemini_available:
            try:
                print(f"🎨 Attempting image generation with Gemini...")
                result = self._generate_with_gemini(prompt)
                if result:
                    return result, "gemini"
                errors.append("Gemini: Not yet implemented")
            except Exception as e:
                error_msg = f"Gemini: {str(e)}"
                print(f"⚠ {error_msg}")
                errors.append(error_msg)
        
        # Fallback to OpenAI DALL-E
        if self.openai_available:
            try:
                print(f"🎨 Falling back to OpenAI DALL-E...")
                result = self._generate_with_openai(prompt)
                if result:
                    return result, "openai"
                errors.append("OpenAI: No result returned")
            except Exception as e:
                error_msg = f"OpenAI: {str(e)}"
                print(f"⚠ {error_msg}")
                errors.append(error_msg)
        
        # No providers available or all failed
        if not self.gemini_available and not self.openai_available:
            error_message = "No image generation providers configured. Install: pip install openai"
        else:
            error_message = "All providers failed: " + "; ".join(errors)
        
        return None, error_message
    
    def _generate_with_gemini(self, prompt: str) -> Optional[bytes]:
        """
        Generate image using Gemini 2.5 Flash Image model
        Uses the new native image generation capability
        """
        try:
            import google.generativeai as genai
            
            # Use the new Gemini 2.5 Flash Image model
            model = genai.GenerativeModel('gemini-2.5-flash-image')
            
            print(f"🎨 Generating image with Gemini 2.5 Flash Image...")
            
            # Generate content with the prompt
            response = model.generate_content(prompt)
            
            # Extract image data from response
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    # Get base64 encoded image data
                    image_data = part.inline_data.data
                    
                    # Decode base64 to bytes
                    import base64
                    image_bytes = base64.b64decode(image_data)
                    
                    print(f"✓ Image generated successfully with Gemini 2.5 Flash Image")
                    return image_bytes
                elif hasattr(part, 'text') and part.text:
                    print(f"📝 Gemini response text: {part.text}")
            
            print("⚠ No image data found in Gemini response")
            return None
            
        except Exception as e:
            print(f"✗ Gemini image generation failed: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _generate_with_openai(self, prompt: str) -> Optional[bytes]:
        """Generate image using OpenAI DALL-E"""
        try:
            # Generate image with DALL-E 3
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            
            # Get image URL
            image_url = response.data[0].url
            
            # Download image
            image_response = requests.get(image_url, timeout=30)
            image_response.raise_for_status()
            
            print(f"✓ Image generated successfully with DALL-E 3")
            return image_response.content
            
        except Exception as e:
            print(f"✗ DALL-E generation failed: {e}")
            raise
    
    def save_image_to_project(self, project_path: str, image_data: bytes, filename: str) -> str:
        """Save generated image to project assets folder"""
        assets_path = os.path.join(project_path, 'assets', 'images')
        os.makedirs(assets_path, exist_ok=True)
        
        # Ensure filename has extension
        if not filename.endswith(('.png', '.jpg', '.jpeg')):
            filename += '.png'
        
        file_path = os.path.join(assets_path, filename)
        
        with open(file_path, 'wb') as f:
            f.write(image_data)
        
        return file_path
