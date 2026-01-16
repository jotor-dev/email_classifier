import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("API_TOKEN")
# Vamos testar o modelo que tu escolheste
model = "facebook/bart-large-mnli" 

print(f"--- Iniciando Invocação ---")
print(f"Token detectado: {token[:5]}..." if token else "ERRO: Token não encontrado no .env")

try:
    client = InferenceClient(api_key=token)
    
    # O método zero_shot_classification é o caminho mais curto
    result = client.zero_shot_classification(
        "Gostaria de saber o status do meu investimento",
        model=model,
        candidate_labels=["Produtivo", "Improdutivo"]
    )
    
    print(f"Resposta do Oráculo: {result}")

except Exception as e:
    print(f"A magia falhou! Causa: {e}")