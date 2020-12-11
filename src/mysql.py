from src.config import db_name, password_mysql, user_mysql
from src.variables import DatabaseVar

from sqlalchemy import create_engine, inspect



class MysqlConn():
    
    
    def __init__(self):
        
        
        self.database = db_name
        self.connect_mysql(user_mysql, password_mysql)
        #self.connect_mysql('user_mysql', 'password_mysql')
        


    def connect_mysql(self, user, password):
        #this to be deleted???????????????????????
        mysql_url = f'mysql://{user}:{password}@localhost/{self.database}'
        engine = create_engine(mysql_url)

        

        self.conn = engine.connect()
        
        



    def insert_mysql(self, table_name, info):

        '''
        Args:
            table_name(str)
            info(dict)

        '''

        
        columns = str(tuple(key for key in info.keys())).replace('\'',"")
        values = str(tuple(value for value in info.values()))
        
        query = f"INSERT INTO {table_name} {columns} VALUES {values};"
        
        
        self.conn.execute(query)


    def check_in_table(self,table_name,column, _id):


        query = f"(SELECT {column} FROM {table_name} WHERE {column} = '{_id}');"

        answer = self.conn.execute(query)

        if answer.fetchone():
            return True
        else:
            return False


    def update_database(self, table_name, id_col, field_col, _id, value):

        query = f"UPDATE {table_name} SET {field_col} = '{value}' WHERE {id_col} = '{_id}';"
        self.conn.execute(query)


    def get_mysql_mfccs_song(self, table_name, _id,id_col = 'song_id', field_col = 'mfccs'):


        #maybe not in use at the end



        query = f"SELECT {field_col} FROM {table_name} WHERE {id_col} = '{_id}';"
        return self.conn.execute(query)


    def get_info_for_model(self, table_name = 'songs', field_col = 'mfccs, genre', id_col = 'genre'):

        

        query = f"SELECT {field_col} FROM {table_name} WHERE {id_col} IS NOT NULL;"

        
        
        return self.conn.execute(query)

    def delete_where(self, table_name, _id, id_col):

        query = f"DELETE FROM {table_name} WHERE {id_col} ='{_id}';"
        
        return self.conn.execute(query)


    def songs_match_between_users(self, user1, user2, table_name, limit, col_user = 'user_id', match_id = 'song_id'):

        query = f"SELECT table1.{match_id}, table1.song_score, table2.song_score, (table1.song_score + table2.song_score) AS total FROM (SELECT * FROM {table_name} WHERE {col_user} = '{user1}') AS table1 INNER JOIN (SELECT * FROM {table_name} WHERE {col_user} = '{user2}') AS table2 ON table1.{match_id} = table2.{match_id} ORDER BY total DESC LIMIT {limit};"
        
        return self.conn.execute(query)


    def find_user_songs_by_user(self, user, genre):

        query = f"SELECT b.song_id, b.name, b.popularity FROM user_song a INNER JOIN songs b ON a.song_id = b.song_id WHERE (a.user_id = '{user}' AND (COALESCE(b.genre, b.genre_model) = '{genre}'));"
        
 
        return self.conn.execute(query)


    def find_user_all_songs_genre(self, user):

        query = f"SELECT COALESCE(b.genre, b.genre_model) FROM user_song a INNER JOIN songs b ON a.song_id = b.song_id WHERE a.user_id = '{user}';"
        
 
        return self.conn.execute(query)

    def find_user_all_songs_ids(self, user):
        
        query = f"SELECT b.song_id, b.popularity, COALESCE(b.genre, b.genre_model), a.user_id FROM user_song a INNER JOIN songs b ON a.song_id = b.song_id WHERE a.user_id = '{user}';"
        
 
        return self.conn.execute(query)


    def get_all_songs(self, table_name, field_col='song_id, mfccs'): 
        query = f"SELECT {field_col} FROM {table_name};"
        
        return self.conn.execute(query)


    def update_prediction(self, genre, model_pred, song_id, table_name = 'songs'): 

        query = f"UPDATE {table_name} SET genre_model = '{genre}', model_pred = '{model_pred}' WHERE song_id = '{song_id}';"
        
        return self.conn.execute(query)


    def get_name_song(self, song_id):

        query = f"SELECT songs.name FROM songs WHERE song_id = '{song_id}';"
        
        return self.conn.execute(query)

    def find_all_users(self):
        query = f"SELECT users.user_id FROM users;"

        return self.conn.execute(query)

    def fetch_user(self, user):
        query = f"SELECT * FROM users WHERE user_id = '{user}';"

        return self.conn.execute(query)


    def fetch_community(self):
        query = f"SELECT b.name as  Artist1, c.name as Artist2 FROM artist_rel a INNER JOIN artist b ON b.artist_id = a.main_id INNER JOIN artist c ON c.artist_id = a.rel_id;"

        return self.conn.execute(query)

    def fetch_user_artists(self, user):

        query = f"SELECT artist.name FROM user_artist INNER JOIN artist ON user_artist.artist_id = artist.artist_id WHERE user_artist.user_id = '{user}';"

        return self.conn.execute(query)

    def find_artist_in_other_songs(self, user1, user2):

        table1 = f"SELECT a.artist_id, b.name FROM user_artist a INNER JOIN artist b ON b.artist_id = a.artist_id WHERE a.user_id = '{user1}'"
        
        table2 = f"SELECT a.song_id, b.artist_id, c.name FROM user_song a INNER JOIN artist_song b ON a.song_id = b.song_id INNER JOIN songs c ON c.song_id = a.song_id WHERE a.user_id = '{user2}'"

        query = f"SELECT table1.name AS artist_name, table2.name AS song_name, table2.song_id FROM ({table1}) table1 INNER JOIN ({table2}) table2 ON table1.artist_id = table2.artist_id;"

        return self.conn.execute(query)


    def fetch_popularity(self, user):

        query = f"SELECT b.name, b.popularity FROM user_song a INNER JOIN songs b ON a.song_id = b.song_id WHERE a.user_id = '{user}';"

        return self.conn.execute(query)



    def fetch_years_songs(self, user):

        query = f"SELECT c.release_date, b.name FROM user_song a INNER JOIN songs b ON a.song_id = b.song_id INNER JOIN albums c ON c.album_id = b.album_id WHERE a.user_id = '{user}';"

        return self.conn.execute(query)


    def fetch_column_table_where(self, table_name, column_name, where_column, value):
        query = f"SELECT {column_name} FROM {table_name} WHERE {where_column} = '{value}';"

        return self.conn.execute(query)



    def fetch_score_user_top_song(self,user_id, song_id):


        query = f"SELECT song_score FROM user_song WHERE user_id = '{user_id}' AND song_id = '{song_id}';"

        return self.conn.execute(query)


    def check_song_artist_top(self,user_id, song_id):

        table1 = f"SELECT b.album_id FROM user_artist a INNER JOIN artist_album b ON a.artist_id = b.artist_id WHERE a.user_id = '{user_id}'"

        table2 = f"SELECT a.album_id FROM songs a WHERE a.song_id = '{song_id}'"

        query = f"SELECT * FROM ({table1}) table1 INNER JOIN ({table2}) table2 WHERE table2.album_id = table1.album_id;"

        return self.conn.execute(query)


    def find_genre_song(self, song_id):

        query = f"SELECT COALESCE(a.genre, a.genre_model) FROM songs a WHERE a.song_id = '{song_id}';"
        
 
        return self.conn.execute(query)


    def fetch_report_song(self, song_id):

        query = f"SELECT a.name, c.name, d.name, c.img_url, d.img_url FROM songs a INNER JOIN artist_song b ON a.song_id = b.song_id INNER JOIN artist c ON c.artist_id = b.artist_id  INNER JOIN albums d ON d.album_id = a.album_id WHERE a.song_id = '{song_id}';"

        return self.conn.execute(query)











class MysqlAdmin(MysqlConn):
    
    
    def __init__(self, user_mysql, password_mysql):
        #super().__init__() 
        
        self.database = db_name
        self.connect_mysql(user_mysql, password_mysql)
        
        


    def fetch_album_in_songs_null(self):
        
        query = f"SELECT DISTINCT(a.album_id) FROM songs a LEFT JOIN albums b ON a.album_id = b.album_id WHERE b.name IS NULL;"

        return self.conn.execute(query)


    def fetch_artist_in_songs_null(self):
        
        query = f"SELECT DISTINCT(b.artist_id) FROM songs a LEFT JOIN artist_song b ON a.song_id = b.song_id LEFT JOIN artist c ON c.artist_id = b.artist_id WHERE c.artist_id IS NULL;"

        return self.conn.execute(query)









#mysql_admin = MysqlAdmin()

    


mysql = MysqlConn()











        









    


