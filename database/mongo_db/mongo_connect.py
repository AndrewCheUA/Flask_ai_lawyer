from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

MONGO_DATABASE_URI = os.getenv('MONGO_DATABASE_URI')

client = MongoClient(MONGO_DATABASE_URI, server_api=ServerApi('1'))
db = client.lawyer_database
mongo_collection = db.documents_collection
