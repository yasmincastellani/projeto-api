from fastapi import APIRouter
from pydantic import BaseModel
from pydantic import validator
from src.configuracoes.configuracoes import ConfiguracoesPaceiros
import requests
from fastapi.responses import Response, JSONResponse
from src.cache.cache import salvar_chave_redis, buscar_chave_redis


rota_emprestimo = APIRouter(prefix="/emprestimo")

class Emprestimo(BaseModel):
    cpf: str
    parcelas: int
    valor: float

    @validator("cpf")
    def valida_cpf(cls, value:str):
        if value.isnumeric():
            if len(value) != 11:
                raise ValueError("CPF inválido")
    
        
        if not value.isnumeric():
            raise ValueError("CPF inválido")
        
        return value            
    
    @validator("parcelas")
    def  valida_parcelas(cls, value:int):
        if value <= 0:
            raise ValueError("Parcela inválida")
        
        if value >= 360:
            raise ValueError("Parcela maior que a permitida")
        
        return value
    
    @validator("valor")
    def valida_valor(cls, value:float):
        if value <= 0:
            raise ValueError("Valor menor que o permitido")
        
        if value >= 100000:
            raise ValueError("Valor maior que o permitido")
        
        return value
   
async def buscar_token():
    """
    Essa função envia as credenciais na rota de autentificação e retorna
    uma string com o token ou uma string vazia
    """
    url_parceiro = ConfiguracoesPaceiros.URL + "/autenticar"
    #cabeçalho informando que o tipo de conteúdo é json
    cabecalho = {"Content-Type":"application/json"}
    corpo = {
        "client_id": ConfiguracoesPaceiros.CLIENTE_ID,
        "client_secret": ConfiguracoesPaceiros.CLIENTE_TOKEN
    }

    resposta_parceiro = requests.post(url_parceiro, headers=cabecalho, json=corpo)

    if resposta_parceiro.status_code == 401:
        return ""
    
    retorno_token = resposta_parceiro.json()
    
    # string que contém o token
    token_tipo_acesso = f"{retorno_token['token_type']} {retorno_token['access_token']}"
    
    return token_tipo_acesso

async def buscar_ofertas(token: str):

    url_parceiro = ConfiguracoesPaceiros.URL + "/ofertas"
    cabecalho = {
        "Authorization": token
    }

    resposta_parceiro = requests.get(url_parceiro, headers=cabecalho)

    if resposta_parceiro.status_code == 403:
        return []

    lista_ofertas = resposta_parceiro.json()

    return lista_ofertas


async def filtrar_ofertas(parcela_simulada: Emprestimo, ofertas: list):


    for oferta in ofertas:
        if parcela_simulada.valor <= oferta["value"] and parcela_simulada.parcelas <= oferta["installments"]:
            return oferta
    
    return None


    
@rota_emprestimo.get("/")
async def buscar_emprestimo(dados: Emprestimo):


    retorno_cache = await buscar_chave_redis(cpf=dados.cpf)
    #validando se o retorno da função é != de falso. Se for, retorna o valor da chave (dict). 
    # Se não, segue o fluxo com o parceiro
    if retorno_cache != False: 
        return JSONResponse(content=retorno_cache)

    retorno_token = await buscar_token()
    if retorno_token == "":
        return Response(status_code=502)
    
    retorno_lista = await buscar_ofertas(token=retorno_token)
    if retorno_lista == []:
        return Response(status_code=502)

    oferta_filtrada = await filtrar_ofertas(parcela_simulada=dados, ofertas=retorno_lista)
    if oferta_filtrada == None:
        return Response(status_code=204)
    
    salvar_cache = await salvar_chave_redis(cpf=dados.cpf, oferta_filtrada=oferta_filtrada)
    if salvar_cache == False:
        print("Erro ao salvar cache no Redis")

    return JSONResponse(oferta_filtrada)
