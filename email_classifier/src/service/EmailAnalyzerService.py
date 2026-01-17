import os, logging, re, json, os
import requests
from dotenv import load_dotenv
load_dotenv()

class EmailAnalyzerService:

    def __init__(self) -> None:
        self.API_TOKEN: str = os.getenv("API_TOKEN")
        self.API_URL: str = os.getenv("API_URL")
        self.MODEL_NAME: str = os.getenv("MODEL_NAME")
        self.logger = logging.getLogger(__name__)

    def query_analyse_email(self, text: str) -> dict:
        prompt = f"""
        Você é um Assistente. Sua missão é analisar e-mails e decidir se eles exigem ação humana (Produtivo) ou se são distrações/automáticos (Improdutivo).

        REGRAS PARA A SUGESTÃO:
        1. Se for PRODUTIVO: Escreva uma resposta curta, profissional e personalizada que o usuário possa enviar agora.
        2. Se for IMPRODUTIVO: Sugira uma ação de limpeza em relação ao email.
        3. Nunca use frases genéricas. Seja claro.

        Email: "{text[:1200]}"

        Responda estritamente neste formato JSON:
        {{
            "categoria": "Produtivo" ou "Improdutivo",
            "porcentagem": 0-100 que indica a confiança na categorização,
            "sugestão": "sua sugestão executiva aqui"
        }}
        """

        try:
            response = requests.post(
                url=self.API_URL,
                headers={
                    "Authorization": f"Bearer {self.API_TOKEN}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:8000", 
                    "Email Classifier": "Email Classifier App"
                },
                data=json.dumps({
                    "model": self.MODEL_NAME,
                    "messages": [{"role": "user", "content": prompt}]
                }),
                timeout=30
            )

            response.raise_for_status()
            
            response = response.json()
            response = response['choices'][0]['message']['content']

            return self.formatar_json(response)

        except Exception as e:
            self.logger.error(f"Erro na análise: {e}")
            return {
                "categoria": "Indefinido",
                "porcentagem": 0,
                "sugestão": "O sistema não pôde gerar uma resposta automática para este item."
            }
        
    def formatar_json(self, texto: str) -> dict:
        try:
            match = re.search(r'\{.*\}', texto, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise ValueError("Formato JSON não detectado.")
        except Exception as e:
            self.logger.error(f"Falha ao formatar JSON: {e}")
            raise