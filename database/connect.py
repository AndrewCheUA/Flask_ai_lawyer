from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()


SQLALCHEMY_DATABASE_URL = os.getenv('SQLALCHEMY_DATABASE_URL')

engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True, pool_size=15)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = Session()


# Dependency
def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()
