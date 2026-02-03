from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional, List

# --- CONFIGURAÇÃO DO BANCO DE DADOS (A Parte "SQL") ---
# Cria um arquivo de banco de dados chamado 'cardapio.db' na mesma pasta
SQLALCHEMY_DATABASE_URL = "sqlite:///./cardapio.db"

# O "motor" que conecta o Python ao banco
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELO DO BANCO (Tabela) ---
# Isso aqui é o equivalente ao "CREATE TABLE pratos (...)"
class PratoDB(Base):
    __tablename__ = "pratos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    descricao = Column(String, nullable=True)
    preco = Column(Float)
    disponivel = Column(Boolean, default=True)

# Cria as tabelas no banco de dados (se não existirem)
Base.metadata.create_all(bind=engine)

# --- MODELOS PYDANTIC (Validação de Dados) ---
# Isso define o que o usuário MANDA e RECEBE da API
class PratoCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None
    preco: float
    disponivel: bool = True

class PratoResponse(PratoCreate):
    id: int
    class Config:
        from_attributes = True # Permite ler dados do ORM

# --- APLICAÇÃO ---
app = FastAPI()

# Função para pegar uma conexão com o banco e fechar depois de usar
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ROTAS (Endpoints) ---

# Criar (INSERT)
@app.post("/pratos", response_model=PratoResponse)
def criar_prato(prato: PratoCreate, db: Session = Depends(get_db)):
    # Cria o objeto do banco
    novo_prato = PratoDB(**prato.dict()) 
    db.add(novo_prato)  # Prepara o INSERT
    db.commit()         # Executa o INSERT (Salva no banco)
    db.refresh(novo_prato) # Recarrega os dados (para pegar o ID gerado)
    return novo_prato

# Listar (SELECT *)
@app.get("/pratos", response_model=List[PratoResponse])
def listar_pratos(db: Session = Depends(get_db)):
    # Equivale a: SELECT * FROM pratos
    return db.query(PratoDB).all()

# Buscar um (SELECT WHERE id = ?)
@app.get("/pratos/{prato_id}", response_model=PratoResponse)
def obter_prato(prato_id: int, db: Session = Depends(get_db)):
    prato = db.query(PratoDB).filter(PratoDB.id == prato_id).first()
    if prato is None:
        raise HTTPException(status_code=404, detail="Prato não encontrado")
    return prato

# Deletar (DELETE)
@app.delete("/pratos/{prato_id}")
def deletar_prato(prato_id: int, db: Session = Depends(get_db)):
    prato = db.query(PratoDB).filter(PratoDB.id == prato_id).first()
    if prato is None:
        raise HTTPException(status_code=404, detail="Prato não encontrado")
    
    db.delete(prato)
    db.commit()
    return {"mensagem": "Prato deletado com sucesso"}