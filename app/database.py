from sqlmodel import create_engine, SQLModel, Session

from .models import items, orders, users
from .core.security import settings

engine = create_engine(str(settings.POSTGRES_URL), echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    
def get_session():
    with Session(engine) as session:
        yield session