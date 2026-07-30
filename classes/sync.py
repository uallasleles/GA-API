import requests
import json
from datetime import datetime

# Exemplo de timestamp para sincronização incremental
# Em um cenário real, você armazenaria o último timestamp de sincronização em um arquivo/banco de dados
last_sync_time = datetime(2024, 1, 1, 0, 0, 0) 

def fetch_data_from_erp(since_time):
    """
    Simula a extração de dados modificados do ERP desde um determinado horário.
    Em um cenário real, isso envolveria uma consulta ao banco de dados do ERP 
    ou uma chamada de API.
    """
    print(f"Buscando dados do ERP modificados desde {since_time}")
    # Exemplo de dados estáticos para demonstração
    erp_data = [
        {"id": 1, "name": "Produto A", "price": 100.00, "updated_at": "2024-11-26T10:00:00Z"},
        {"id": 2, "name": "Produto B", "price": 200.00, "updated_at": "2024-11-27T09:00:00Z"}
    ]
    
    # Filtrar dados que foram atualizados após last_sync_time (simulação)
    modified_data = [item for item in erp_data if datetime.fromisoformat(item['updated_at'].replace('Z', '')) > since_time]
    return modified_data

def sync_with_external_api(data):
    """
    Envia os dados extraídos para a API externa.
    """
    api_url = "api.external-service.com" # Substitua pela URL real da API externa
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer SEU_TOKEN_AQUI" # Substitua pelo seu token de autenticação
    }

    for item in data:
        # Prepara o payload conforme a API externa espera
        payload = json.dumps({
            "external_id": item['id'],
            "product_name": item['name'],
            "price": item['price']
        })
        
        try:
            response = requests.post(api_url, headers=headers, data=payload)
            response.raise_for_status() # Lança exceção para códigos de status ruins (4xx ou 5xx)
            print(f"Dados do item {item['id']} enviados com sucesso! Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Erro ao enviar dados do item {item['id']}: {e}")

# Execução do script
if __name__ == "__main__":
    data_to_sync = fetch_data_from_erp(last_sync_time)
    if data_to_sync:
        sync_with_external_api(data_to_sync)
    else:
        print("Nenhum dado novo para sincronizar.")

    # Atualize o timestamp da última sincronização após a conclusão bem-sucedida
    # Em um cenário real, você salvaria isso em um local persistente
    # last_sync_time = datetime.now() 
