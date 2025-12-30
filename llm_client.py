"""
LLM Client for Agent Reasoning
Handles all LLM API calls with proper error handling
"""
from openai import OpenAI
from config import Config
import json
import re


class LLMClient:
    def __init__(self):
        self.client = OpenAI(
            api_key=Config.LLM_API_KEY,
            base_url=Config.LLM_BASE_URL
        )
        self.model = Config.LLM_MODEL
        self.fallback_models = Config.FALLBACK_MODELS
        self.current_model_index = 0
        print(f"LLM Client initialized with model: {self.model}")
        print(f"Using API base URL: {Config.LLM_BASE_URL}")
        print(f"Fallback models available: {self.fallback_models}")
    
    def _get_next_model(self) -> str:
        """Get the next fallback model to try"""
        if self.current_model_index < len(self.fallback_models):
            model = self.fallback_models[self.current_model_index]
            self.current_model_index += 1
            return model
        return None
    
    def _reset_model_index(self):
        """Reset the model index for next request"""
        self.current_model_index = 0
    
    def call(self, prompt: str, system_prompt: str = None, temperature: float = 0.3, max_tokens: int = 4000) -> str:
        """
        Make an LLM API call with fallback support
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Creativity setting (0.0 - 1.0)
            max_tokens: Maximum tokens in response
        
        Returns:
            The LLM response text
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        # Try primary model first, then fallbacks
        models_to_try = [self.model] + self.fallback_models
        
        for model in models_to_try:
            try:
                print(f"Calling LLM model: {model}")
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                result = response.choices[0].message.content
                print(f"LLM response received: {len(result) if result else 0} characters")
                if result and len(result) > 0:
                    return result
            except Exception as e:
                print(f"LLM API Error with model {model}: {e}")
                continue
        
        print("All models failed")
        return None
    
    def call_json(self, prompt: str, system_prompt: str = None, temperature: float = 0.3, max_tokens: int = 4000) -> dict:
        """
        Make an LLM API call expecting JSON response
        
        Args:
            prompt: The user prompt (should request JSON output)
            system_prompt: Optional system prompt
            temperature: Creativity setting
            max_tokens: Maximum tokens in response
        
        Returns:
            Parsed JSON response as dict
        """
        # Add JSON instruction to prompt
        json_prompt = prompt + "\n\nIMPORTANT: Respond with valid, complete JSON only. No markdown formatting. Ensure all strings are properly closed and the JSON is complete."
        
        response_text = self.call(json_prompt, system_prompt, temperature, max_tokens)
        
        if not response_text:
            return None
        
        # Clean up response
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            print(f"Raw response: {response_text[:500]}")
            
            # Try to fix common JSON issues
            fixed_json = self._try_fix_json(response_text)
            if fixed_json:
                print("Successfully fixed JSON")
                return fixed_json
            
            # Try more aggressive cleaning
            cleaned = self._aggressive_json_clean(response_text)
            if cleaned:
                print("Successfully cleaned JSON")
                return cleaned
            
            # Return partial data if we can extract it
            print("Attempting partial extraction")
            return self._extract_partial_json(response_text)
    
    def _aggressive_json_clean(self, text: str) -> dict:
        """More aggressive JSON cleaning"""
        try:
            # Remove special characters that might cause issues
            text = text.replace('\u2011', '-')  # non-breaking hyphen
            text = text.replace('\u2013', '-')  # en dash
            text = text.replace('\u2014', '-')  # em dash
            text = text.replace('\u2018', "'")  # left single quote
            text = text.replace('\u2019', "'")  # right single quote
            text = text.replace('\u201c', '"')  # left double quote
            text = text.replace('\u201d', '"')  # right double quote
            
            # Try parsing again
            return json.loads(text)
        except:
            return None
    
    def _try_fix_json(self, text: str) -> dict:
        """Try to fix common JSON issues"""
        try:
            # Try to find the last complete object/array
            # Count braces to find where JSON might be complete
            brace_count = 0
            bracket_count = 0
            last_valid_pos = 0
            in_string = False
            escape_next = False
            
            for i, char in enumerate(text):
                if escape_next:
                    escape_next = False
                    continue
                if char == '\\':
                    escape_next = True
                    continue
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                    
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        last_valid_pos = i + 1
                elif char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
            
            if last_valid_pos > 0:
                truncated = text[:last_valid_pos]
                return json.loads(truncated)
        except:
            pass
        
        return None
    
    def _extract_partial_json(self, text: str) -> dict:
        """Extract what we can from partial JSON"""
        try:
            # First, try to fix unterminated strings
            fixed = text.rstrip()
            
            # If last character is not a closing brace, try to find last complete field
            if not fixed.endswith('}') and not fixed.endswith(']'):
                # Find last complete value (before the unterminated part)
                last_complete = fixed.rfind('"}')
                if last_complete > 0:
                    fixed = fixed[:last_complete + 2]
            
            # Try to close unclosed braces
            open_braces = fixed.count('{') - fixed.count('}')
            open_brackets = fixed.count('[') - fixed.count(']')
            
            # Close any open arrays first
            if open_brackets > 0:
                fixed += ']' * open_brackets
            
            # Close any open objects
            if open_braces > 0:
                fixed += '}' * open_braces
            
            print(f"Attempting to parse fixed JSON (length: {len(fixed)})")
            return json.loads(fixed)
        except Exception as e:
            print(f"Could not extract partial JSON: {e}")
            # Return minimal structure
            return {
                "key_skills_to_highlight": [],
                "suggested_projects": [],
                "interview_preparation_tips": [],
                "common_questions": [],
                "technical_topics_to_study": [],
                "company_culture_prep": {
                    "company_values": "Research the company",
                    "questions_to_ask": [],
                    "alignment_points": []
                },
                "confidence_boosters": ["You have relevant skills for this role"]
            }
    
    def chat(self, messages: list, system_prompt: str = None, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """
        Chat completion with message history and fallback support
        
        Args:
            messages: List of {"role": "user/assistant", "content": "..."} messages
            system_prompt: System prompt for context
            temperature: Creativity setting
            max_tokens: Maximum tokens in response
        
        Returns:
            Assistant response text
        """
        full_messages = []
        
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        
        full_messages.extend(messages)
        
        # Try primary model first, then fallbacks
        models_to_try = [self.model] + self.fallback_models
        
        for model in models_to_try:
            try:
                print(f"Chat with LLM model: {model}")
                response = self.client.chat.completions.create(
                    model=model,
                    messages=full_messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                result = response.choices[0].message.content
                print(f"Chat response received: {len(result) if result else 0} characters")
                if result and len(result) > 0:
                    return result
            except Exception as e:
                print(f"LLM Chat Error with model {model}: {e}")
                continue
        
        print("All chat models failed")
        return "I'm sorry, I encountered an error processing your request. The AI service is temporarily unavailable. Please try again in a moment."


# Global LLM client instance
llm = LLMClient()
