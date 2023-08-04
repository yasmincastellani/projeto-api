import redis
from src.configuracoes.configuracoes import ConfigRedis
import json


async def conexao_redis() -> redis.Redis:
    conexao = redis.Redis(password=ConfigRedis.SENHA)
    return conexao



async def salvar_chave_redis(cpf: str, oferta_filtrada: dict) -> bool:
    redis = await conexao_redis()
    
    #.set() salva uma chave e um valor por um determinado tempo
    retorno_set = redis.set(cpf, json.dumps(oferta_filtrada), 50)

    #.close() fecha a conexão com o banco 
    redis.close()
    
    if retorno_set is None:
        return False
    else:
        return True
    



async def buscar_chave_redis(cpf: str) -> (str | bool):
    redis = await conexao_redis()

    retorno_get = redis.get(cpf) 
    
    redis.close()

    if retorno_get is None:
        return False
    else:
        retorno_get = retorno_get.decode("utf-8")
        retorno_get = json.loads(retorno_get)
        
        retorno_get.update({"cache": True})
        return retorno_get



    