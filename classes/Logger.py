import requests
import os
from dotenv import load_dotenv
import sys

class Logger():
    def __init__(self):
        
        load_dotenv()
        self.api_endpoint = os.getenv("LOGGER_API_URL")
        self.api_token = os.getenv("LOGGER_API_KEY")
        
        self.url = f"{self.api_endpoint}{self.api_token}"

    def add(self, type, message):
        
        json = {
            "app_name" : "RepomFrete",
            "file_name" : sys.argv[0],
            "type" :type,
            "log" : message
        }
        
        try:
            response = requests.post(self.url, json=json)
            if response.status_code == 200:
                return True
            else:
                return False
        except Exception as e:
            print(f"Erro ao inserir log: {e}")
            return False

if __name__ == '__main__':
    logger = Logger()
    retorno = logger.add("INFO", "Testando a classe Logger")
    if retorno:
        print("Log inserido com sucesso")