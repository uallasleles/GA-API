import requests
import os
import json as json_module
import logging
from dotenv import load_dotenv
from classes.token_manager import load_token_data, save_token_data, is_token_valid
from classes.Logger import Logger as Log

logger = logging.getLogger(__name__)

# Prática recomendada: carregar variáveis ​​de ambiente para informações confidenciais, como chaves de API
load_dotenv() 

class APIClient:
    """
    Uma classe padrão para consumir uma API REST genérica.
    Um cliente para interagir com uma API usando autenticação via token.
    """

    api_key = os.getenv("API_KEY")
    API_BASE_URL = os.getenv("API_BASE_URL")
    API_SERVER = os.getenv("API_SERVER")


    API_VERSION = os.getenv("API_VERSION")

    # payload = f"grant_type={API_GRANT_TYPE}&username={API_USERNAME}&password={API_PASSWORD}&partner={API_PARTNER}" 

    def __init__(self, base_url=API_BASE_URL):
        self.base_url = base_url
        self.API_GRANT_TYPE = os.getenv("API_GRANT_TYPE")
        self.API_USERNAME = os.getenv("API_USERNAME")
        self.API_PASSWORD = os.getenv("API_PASSWORD")
        self.API_PARTNER = os.getenv("API_PARTNER")
        self.session = requests.Session()
        # Content-Type será definido automaticamente por requests (não forçar application/x-www-form-urlencoded)
        self.session.headers.update({'Accept': 'application/json'})
        
        # token = load_token_data()["access_token"]
        self._access_token = load_token_data()["access_token"]
        logger.debug(f"Token carregado: {self._access_token[:20]}...")

        self.session.headers.update({'Authorization': f'Bearer {self._access_token}'})
        self.timeout = 10

    @property
    def access_token(self):
        """Propriedade para obter o token, renovando se necessário."""
        if not self._access_token or not is_token_valid():
            logger.info("Token expirado ou ausente. Gerando novo token...")
            self.refresh_access_token()
        return self._access_token

    def refresh_access_token(self):
        """Obtém (ou renova) o token de acesso e persiste os dados."""
        # Lógica para chamar o endpoint de autenticação da API (OAuth 2.0, por exemplo)
        auth_url = f"{self.base_url}/token"
        payload = f"grant_type={self.API_GRANT_TYPE}&username={self.API_USERNAME}&password={self.API_PASSWORD}&partner={self.API_PARTNER}"
        response = requests.post(auth_url, data=payload)
        response.raise_for_status()
        token_data = response.json()

        self._access_token = token_data['access_token']
        # 'expires_in' é o tempo de vida do token em segundos retornado pela API
        save_token_data(self._access_token, token_data['expires_in'])
        logger.info("Novo token gerado e salvo.")

    def _request(self, method, endpoint, params=None, json=None, data=None):
        """
        Método auxiliar para lidar com o ciclo de vida da solicitação, incluindo tratamento de erros.
        """
        url = f"{self.base_url}{endpoint}"
        if params is None:
            params = {'x-api-version': self.API_VERSION}
        try:
            response = self.session.request(method, url, params=params, data=data, json=json, timeout=self.timeout)
            response.raise_for_status()  # Levanta HTTPError se status >= 400
        
            try:
                return response.json()
            except requests.exceptions.JSONDecodeError as json_err:
                logger.error(f"Erro ao decodificar JSON da resposta: {json_err}")
                logger.debug(f"Status: {response.status_code}, Content-Type: {response.headers.get('Content-Type')}")
                logger.debug(f"Preview: {response.text[:500]}")
                return None
        
        except requests.exceptions.Timeout as e:
            logger.error(f"A solicitação expirou: {e}")
            return None
        except requests.exceptions.HTTPError:
            # print(response.json())
            error_data = response.json()
            logger.error(f"Resposta JSON: {json_module.dumps(error_data, indent=4, ensure_ascii=False)}")
            Log().add("ERROR", f"Resposta JSON: {json_module.dumps(error_data, indent=4, ensure_ascii=False)}")
            # logger.error(f"Erro HTTP {response.status_code}: {response.reason}")
            try:
                error_data = response.json()
                logger.debug(f"Resposta JSON: {json_module.dumps(error_data, indent=4, ensure_ascii=False)}")
                Log().add("ERROR", f"Resposta JSON: {json_module.dumps(error_data, indent=4, ensure_ascii=False)}")
            except (requests.exceptions.JSONDecodeError, ValueError):
                logger.debug(f"Resposta de texto: {response.text[:500]}")
                Log().add("DEBUG", f"Resposta de texto: {response.text[:500]}")
            
            if response.status_code == 401:
                logger.info("Não autorizado (401). Token inválido/expirado.")
                logger.info("Renovando token...")
                self.refresh_access_token()
                logger.info("Reenviando dados...")
                self.session.headers.update({'Authorization': f'Bearer {self._access_token}'})
                response = self.session.request(method, url, params=params, data=data, json=json, timeout=self.timeout)
                try:
                    response.raise_for_status()
                    return response.json()
                except Exception as retry_err:
                    logger.error(f"Erro na retentativa: {retry_err}")
                    return None
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro durante a solicitação: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                logger.debug(f"Código de status: {e.response.status_code}")
                logger.debug(f"Corpo de Resposta: {e.response.text}")
            return None

    def get(self, endpoint, params=None):
        return self._request('GET', endpoint, params=params)

    def post(self, endpoint, params=None, data=None, json=None):
        return self._request('POST', endpoint, params=params, data=data, json=json)

    def put(self, endpoint, params=None, data=None, json=None):
        return self._request('PUT', endpoint, params=params, data=data, json=json)

    def delete(self, endpoint):
        return self._request('DELETE', endpoint)


if __name__ == '__main__':
    pass
