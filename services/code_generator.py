"""
Code Generator Service
Handles AI-powered code generation using OpenAI API
"""
import asyncio
from typing import List, Optional
from dataclasses import dataclass
from openai import AsyncOpenAI, OpenAIError, APITimeoutError
import logging

from exceptions import AIGenerationError, CodeValidationError

logger = logging.getLogger(__name__)


@dataclass
class CodeFile:
    """Represents a generated code file"""
    path: str
    content: str


@dataclass
class GeneratedCode:
    """Container for generated code and metadata"""
    files: List[CodeFile]
    dependencies: List[str]
    expo_version: str
    
    def get_main_file(self) -> CodeFile:
        """Get the main App.js or App.tsx file"""
        for file in self.files:
            if file.path in ["App.js", "App.tsx"]:
                return file
        raise ValueError("No main App file found in generated code")


# Legacy alias for backward compatibility
class CodeGenerationError(AIGenerationError):
    """Raised when code generation fails (legacy alias)"""
    pass


class CodeGenerator:
    """Service for generating React Native + Expo code using OpenAI"""
    
    def __init__(self, api_key: str, model: str = "gpt-5", timeout: int = 900):
        """
        Initialize the CodeGenerator
        
        Args:
            api_key: OpenAI API key
            model: OpenAI model to use (default: gpt-5)
            timeout: Timeout in seconds for API calls (default: 900 = 15 minutes)
        """
        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout)
        self.model = model
        self.timeout = timeout
        
    def _build_system_prompt(self) -> str:
        """
        Construct system prompt for OpenAI with Expo expertise
        
        Returns:
            System prompt string
        """
        return """You are an expert React Native and Expo developer. Generate complete, production-ready mobile application code based on user requirements.

Requirements:
- Use Expo SDK 50+
- Follow React Native best practices
- Include proper error handling
- Use TypeScript for type safety
- Include necessary imports
- Create functional components with hooks
- Add inline comments for complex logic
- Ensure code is ready to run without modifications

Output Format:
Provide the complete App.tsx file content.
Start your response with the code directly - no explanations before the code.
Use TypeScript and include proper type annotations.
Include any additional component files if needed (separate with "// FILE: ComponentName.tsx").
Specify any required Expo packages beyond defaults in a comment at the top.

IMPORTANT: For dependencies, list ONLY the package names separated by commas, NO comments or explanations.

Example output structure:
```typescript
// DEPENDENCIES: expo-linear-gradient, @expo/vector-icons
import React from 'react';
import { View, Text } from 'react-native';

export default function App() {
  return (
    <View>
      <Text>Hello World</Text>
    </View>
  );
}
```"""
    
    def _build_user_prompt(self, prompt: str) -> str:
        """
        Construct user prompt from user's app description
        
        Args:
            prompt: User's natural language app description
            
        Returns:
            Formatted user prompt
        """
        return f"""Create a complete Expo mobile application with the following requirements:

{prompt}

Generate the full App.tsx file and any additional components needed.
Remember to include all necessary imports and make the code ready to run."""
    
    async def generate_app_name(self, prompt: str) -> str:
        """
        Generate a simple one-word app name from the prompt
        
        Args:
            prompt: User's natural language description of the app
            
        Returns:
            Simple one-word app name (lowercase, alphanumeric)
            
        Raises:
            AIGenerationError: If name generation fails
        """
        try:
            logger.info("Generating app name from prompt")
            
            name_prompt = f"""Based on this app description, generate a simple one-word app name.
The name should be:
- One word only (no spaces, no hyphens)
- Lowercase
- Alphanumeric only
- Descriptive of the app's purpose
- Maximum 15 characters

App description: {prompt}

Respond with ONLY the app name, nothing else."""
            
            response = await asyncio.wait_for(
                self.client.responses.create(
                    model=self.model,
                    input=name_prompt
                ),
                timeout=30  # Short timeout for name generation
            )
            
            app_name = response.output_text.strip().lower()
            
            # Clean the name - remove any non-alphanumeric characters
            import re
            app_name = re.sub(r'[^a-z0-9]', '', app_name)
            
            # Ensure it's not empty and not too long
            if not app_name or len(app_name) < 2:
                app_name = "myapp"
            elif len(app_name) > 15:
                app_name = app_name[:15]
            
            logger.info(f"Generated app name: {app_name}")
            return app_name
            
        except Exception as e:
            logger.warning(f"Failed to generate app name: {e}, using default")
            return "myapp"
    
    async def generate_app_code(self, prompt: str) -> GeneratedCode:
        """
        Generate React Native + Expo code from natural language prompt
        
        Args:
            prompt: User's natural language description of the app
            
        Returns:
            GeneratedCode object containing code files and metadata
            
        Raises:
            CodeGenerationError: If code generation fails
        """
        try:
            logger.info(f"Starting code generation with model {self.model}")
            
            # Build the full prompt combining system and user prompts
            full_prompt = f"{self._build_system_prompt()}\n\n{self._build_user_prompt(prompt)}"
            
            # Create response with GPT-5 API format
            response = await asyncio.wait_for(
                self.client.responses.create(
                    model=self.model,
                    input=full_prompt
                ),
                timeout=self.timeout
            )
            
            # Extract generated code from response
            generated_content = response.output_text
            
            if not generated_content:
                raise CodeGenerationError("OpenAI returned empty response")
            
            logger.info("Code generation completed successfully")
            
            # Parse the response to extract code and metadata
            return self._parse_generated_code(generated_content)
            
        except asyncio.TimeoutError:
            logger.error(f"Code generation timed out after {self.timeout} seconds")
            raise AIGenerationError(
                f"Code generation timed out after {self.timeout} seconds",
                "Please try again with a simpler prompt"
            )
        except APITimeoutError:
            logger.error("OpenAI API timeout")
            raise AIGenerationError(
                "OpenAI API request timed out",
                "Please try again"
            )
        except OpenAIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise AIGenerationError(
                f"Failed to generate code: {str(e)}",
                "Try rephrasing your prompt or check OpenAI service status"
            )
        except Exception as e:
            logger.error(f"Unexpected error during code generation: {str(e)}")
            raise AIGenerationError(
                f"An unexpected error occurred: {str(e)}",
                "Please try again or contact support"
            )
    
    def _parse_generated_code(self, content: str) -> GeneratedCode:
        """
        Parse OpenAI response to extract code files and metadata
        
        Args:
            content: Raw content from OpenAI response
            
        Returns:
            GeneratedCode object with parsed files and metadata
        """
        files: List[CodeFile] = []
        dependencies: List[str] = []
        expo_version = "50.0.0"  # Default version
        
        # Extract dependencies from comments
        lines = content.split('\n')
        for line in lines[:10]:  # Check first 10 lines for dependencies
            if 'DEPENDENCIES:' in line or 'dependencies:' in line.lower():
                # Extract dependencies from comment
                deps_part = line.split('DEPENDENCIES:', 1)[-1].strip()
                deps_part = deps_part.replace('//', '').strip()
                raw_deps = [dep.strip() for dep in deps_part.split(',') if dep.strip()]
                
                # Clean up dependencies - remove comments and invalid characters
                for dep in raw_deps:
                    # Remove anything in parentheses (comments)
                    clean_dep = dep.split('(')[0].strip()
                    # Remove quotes
                    clean_dep = clean_dep.replace('"', '').replace("'", '')
                    # Only add if it looks like a valid package name
                    if clean_dep and not ' ' in clean_dep and clean_dep.replace('-', '').replace('@', '').replace('/', '').replace('.', '').isalnum():
                        dependencies.append(clean_dep)
                break
        
        # Extract code blocks
        code_blocks = []
        in_code_block = False
        current_block = []
        
        for line in lines:
            if line.strip().startswith('```'):
                if in_code_block:
                    # End of code block
                    code_blocks.append('\n'.join(current_block))
                    current_block = []
                    in_code_block = False
                else:
                    # Start of code block
                    in_code_block = True
            elif in_code_block:
                current_block.append(line)
        
        # If no code blocks found, treat entire content as code
        if not code_blocks:
            code_blocks = [content]
        
        # Process code blocks to extract files
        for block in code_blocks:
            # Check for multiple files in one block (separated by // FILE: comments)
            if '// FILE:' in block:
                file_parts = block.split('// FILE:')
                for i, part in enumerate(file_parts):
                    if i == 0:
                        # First part is the main App file
                        files.append(CodeFile(path="App.tsx", content=part.strip()))
                    else:
                        # Extract filename and content
                        lines = part.split('\n', 1)
                        filename = lines[0].strip()
                        file_content = lines[1] if len(lines) > 1 else ""
                        files.append(CodeFile(path=filename, content=file_content.strip()))
            else:
                # Single file - assume it's App.tsx
                files.append(CodeFile(path="App.tsx", content=block.strip()))
        
        # Ensure we have at least one file
        if not files:
            raise CodeValidationError("Failed to extract any code files from generated content")
        
        # Create GeneratedCode object
        generated_code = GeneratedCode(
            files=files,
            dependencies=dependencies,
            expo_version=expo_version
        )
        
        # Validate the generated code
        self._validate_generated_code(generated_code)
        
        return generated_code
    
    def _validate_generated_code(self, code: GeneratedCode) -> None:
        """
        Validate that generated code contains required Expo project structure
        
        Args:
            code: GeneratedCode object to validate
            
        Raises:
            CodeValidationError: If validation fails
        """
        # Check that we have at least one file
        if not code.files:
            raise CodeValidationError("Generated code contains no files")
        
        # Check that we have a main App file
        has_main_file = any(
            file.path in ["App.js", "App.tsx", "App.jsx"]
            for file in code.files
        )
        if not has_main_file:
            raise CodeValidationError(
                "Generated code must contain an App.js, App.tsx, or App.jsx file"
            )
        
        # Validate main file content
        try:
            main_file = code.get_main_file()
        except ValueError as e:
            raise CodeValidationError(str(e))
        
        # Check for required imports
        required_patterns = [
            "import",  # Must have at least one import
            "export default",  # Must export default component
        ]
        
        for pattern in required_patterns:
            if pattern not in main_file.content:
                raise CodeValidationError(
                    f"Generated code missing required pattern: '{pattern}'"
                )
        
        # Check for React Native imports
        if "react-native" not in main_file.content.lower() and "react" not in main_file.content.lower():
            raise CodeValidationError(
                "Generated code must import React or React Native components"
            )
        
        # Validate that code is not empty or too short
        if len(main_file.content.strip()) < 50:
            raise CodeValidationError(
                "Generated code is too short to be a valid Expo application"
            )
        
        logger.info("Code validation passed")
    
    def validate_expo_structure(self, code: GeneratedCode) -> bool:
        """
        Public method to validate Expo project structure
        
        Args:
            code: GeneratedCode object to validate
            
        Returns:
            True if validation passes
            
        Raises:
            CodeValidationError: If validation fails
        """
        self._validate_generated_code(code)
        return True
