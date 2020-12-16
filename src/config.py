import os
import dotenv

import sys
sys.path.append("../")

dotenv.load_dotenv()

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
redirect_uri = 'http://localhost:5000/callback'


db_name = 'spotify_project'
password_mysql = os.getenv("MYSQL_PWD")
user_mysql = os.getenv("MYSQL_USER")

app_secret_key =  b'_5#y2L"F4Q8z\n\xec]/'







