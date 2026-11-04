from app.core.ai.ollama_engine import OllamaAI


ai = OllamaAI()

response = ai._generate("What the fuck!")

print(response)