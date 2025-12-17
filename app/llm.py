import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from groq import Groq
import google.generativeai as genai

class LLMClient(ABC):
    @abstractmethod
    def generate_answer(self, system_prompt: str, history: List[Dict[str, str]], question: str, model: Optional[str] = None) -> str:
        pass

class GroqClient(LLMClient):
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set")
        self.client = Groq(api_key=api_key)
        self.default_model = "llama-3.3-70b-versatile"

    def generate_answer(self, system_prompt: str, history: List[Dict[str, str]], question: str, model: Optional[str] = None) -> str:
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            messages.append(msg)
        messages.append({"role": "user", "content": question})

        target_model = model if model else self.default_model
        
        completion = self.client.chat.completions.create(
            messages=messages,
            model=target_model,
        )
        return completion.choices[0].message.content

class GeminiClient(LLMClient):
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            # Fallback or strict error? For now, print warning if not set but requested
            print("WARNING: GEMINI_API_KEY not set")
        else:
            genai.configure(api_key=api_key)
        self.default_model = "gemini-pro"

    def generate_answer(self, system_prompt: str, history: List[Dict[str, str]], question: str, model: Optional[str] = None) -> str:
        # Gemini handles history strictly. We'll simplify by combining context into prompt for now, 
        # or use start_chat. For RAG, single-turn with context is often easier in Gemini APIs 
        # unless using the chat session object.
        # Let's map messages to Gemini format: user/model.
        
        # Note: System prompt in Gemini is often just prepended to the first message or configured.
        # For simplicity in this generic wrapper:
        
        full_prompt = f"System Instruction:\n{system_prompt}\n\nHistory:\n"
        for msg in history:
            role = "User" if msg['role'] == 'user' else "Model"
            full_prompt += f"{role}: {msg['content']}\n"
        
        full_prompt += f"\nUser: {question}"

        target_model = "gemini-pro" # Gemini has fewer model aliases
        model_instance = genai.GenerativeModel(target_model)
        response = model_instance.generate_content(full_prompt)
        return response.text

def get_llm_client() -> LLMClient:
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    if provider == "gemini":
        return GeminiClient()
    return GroqClient()
