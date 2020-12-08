import os
import dotenv

dotenv.load_dotenv()

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
redirect_uri = 'http://localhost:5000/callback'


db_name = 'spotify_project'
password_mysql = os.getenv("MYSQL_PWD")
user_mysql = os.getenv("MYSQL_USER")







