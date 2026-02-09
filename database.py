import os

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:lorenzo123@localhost:5432/postgres",
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class HistoricoLimpeza(Base):
    __tablename__ = "historico_limpeza"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String, index=True) # EBS ou IP
    recurso_id = Column(String, index=True)
    regiao = Column(String, index=True)
    valor_economizado = Column(Float)
    data_execucao = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)