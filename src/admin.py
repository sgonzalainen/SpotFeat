from src.mysql import MysqlAdmin as mysql_admin

from src.spotify1 import SpotifyAdmin as spotify


class Admin():

    def __init__(self, user, password):

        self.mysql = mysql_admin(user, password)
        self.spotify = spotify()


    def update_albums_table_missing(self):

        albums_to_scrape = [album[0] for album in list(self.mysql.fetch_album_in_songs_null())]

        for album in albums_to_scrape:

            data = self.spotify.get_album_info(album)

            album_dict = {}
            album_dict['album_id'] = album
            album_dict['name'] = data['name'].replace('%','')[0:100]
            album_dict['type'] = data['type']
            album_dict['popularity'] = data['popularity']
            album_dict['release_date'] = data['release_date']
            try:
                album_dict['img_url'] = data.get('images')[0].get('url')
            except IndexError:
                album_dict['img_url'] = ''

            self.mysql.insert_mysql('albums',album_dict)

            for artist in data['artists']:
                self.mysql.insert_mysql('artist_album',{'artist_id' : artist['id'], 'album_id': album})




