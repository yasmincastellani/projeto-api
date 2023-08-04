from fastapi import FastAPI
from src.rotas.emprestimos import rota_emprestimo
from datetime import datetime
import uvicorn

app = FastAPI()
app.include_router(rota_emprestimo, prefix="/api")

@app.get("/")
def servico_vida():
    return {"ON": datetime.now()}


if __name__ == "__main__":
    print(__name__)
    uvicorn.run(
        "app:app",
        port=8000,
        workers=1
    )