import json
import os
from datetime import datetime, timedelta

CONFIG_FILE = 'config.json'

def load_token_data():
    """Carrega dados do token do arquivo de configuração."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return None
    return None

def save_token_data(access_token, expires_in):
    """Salva o token e o tempo de expiração no arquivo de configuração."""
    # Define o tempo de expiração com uma pequena margem de segurança (ex: -60s)
    expiration_time = datetime.now() + timedelta(seconds=expires_in - 60)
    data = {
        'access_token': access_token,
        'expires_at': expiration_time.isoformat()
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def is_token_valid():
    """Verifica se o token existente ainda é válido."""
    data = load_token_data()
    if data and 'expires_at' in data:
        expires_at = datetime.fromisoformat(data['expires_at'])
        return expires_at > datetime.now()
    return False
