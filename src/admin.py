from src.mysql import MysqlAdmin as mysql_admin
from src.config import db_name, password_mysql, user_mysql
import src.model as mod
import numpy as np
import src.audio as audio
from src.variables import AudioVar
import seaborn as sns
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt


from src.spotify import SpotifyAdmin as spotify


class Admin():

    def __init__(self, user_mysql, password_mysql):

        self.mysql = mysql_admin(user_mysql, password_mysql)
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

    def update_missing_artists(self):
        artist_to_scrape = [artist[0] for artist in list(self.mysql.fetch_artist_in_songs_null())]

        for artist in artist_to_scrape:
            data = self.spotify.get_artist_info(artist)

            tmp_dict = {}

            tmp_dict['artist_id'] = artist
            tmp_dict['name'] = data['name'][0:100]
            tmp_dict['popularity'] = data['popularity']
            tmp_dict['followers'] = data['followers']['total']

            try:
                tmp_dict['img_url'] = data['images'][0]['url']
            except IndexError:
                tmp_dict['img_url'] = ''


            self.mysql.insert_mysql('artist', tmp_dict) #inserted into mysql table artist
            data = self.spotify.get_artist_related(artist).get('artists') #list of artist related

            for element in data: #for each artist related
                id_tmp = element['id']
                tmp_dict = {'main_id': artist, 'rel_id': id_tmp}
                self.mysql.insert_mysql('artist_rel', tmp_dict)




    def prepare_input_to_model(self):

        data = self.mysql.get_info_for_model() 

        X, y = mod.decode_input_model(data)

        X_train, y_train, X_val, y_val, X_test, y_test = mod.split_train_val_test(X, y)

        return X_train, y_train, X_val, y_val, X_test, y_test


    def get_artist_albums_id(self, data):
    
        '''
        data = user.get_artist_albums_json(artist_id)
        Not in use

        '''
        albums_id = []
        
        for album in data:
            albums_id.append(album['id'])
            
        return albums_id


    def get_all_artists_id(self, playlist_id):

        songs_num = 100 #for first round
        offset = 0
        artists_id_list = []

        while songs_num == 100:

            data = self.spotify.get_playlist_items_json(playlist_id, offset = offset)['items']
            
            artists_id_list.extend(self.get_artists_ids_from_json(data))

            songs_num = len(data)
            
            offset += songs_num #this is to know if new round moving offset is needed

        artists_id_list = list(set(artists_id_list))

        return artists_id_list



    def get_artists_ids_from_json(self, data):

        temp_list = []

        for song in data:
            artist_id = song['track']['artists'][0]['id'] #for database collection we track only first artist to get top tracks
            temp_list.append(artist_id)
            
            
        return temp_list

    def get_songs_ids_from_json(self, data):

        temp_list = []

        for song in data:
            song_id = song['track']['id'] #for database collection we track only first artist to get top tracks
            temp_list.append(song_id)
            
            
        return temp_list


    def get_artist_top_tracks_ids(self, data):

        top_songs_id = []
        
        for song in data['tracks']:
            
            top_songs_id.append(song['id'])
            
        return top_songs_id



    def create_dataset_genre_by_top_tracks(self, playlist_id, genre):

        table_name = self.songs_table
        
        artist_list = self.get_all_artists_id(playlist_id)


        for artist in tqdm(artist_list):
            
            data = self.spotify.get_artist_top_tracks_json(artist)
            song_list = self.get_artist_top_tracks_ids(data)
            
            for song in tqdm(song_list):

                if self.mysql.check_in_table(table_name, 'song_id', song):
                    pass
                else:
                    self.insert_song_data(song) #this inserts song into mysql with data
                    self.mysql.update_database(table_name, 'song_id', 'genre', song, genre)


    def create_dataset_genre_by_songs(self, playlist_id, genre):

        table_name = self.songs_table
        
        songs_list = self.get_all_song_ids_playlist(playlist_id)

        for song in tqdm(songs_list):

            if self.mysql.check_in_table(table_name, 'song_id', song):
                pass
            else:
                self.insert_song_data(song) #this inserts song into mysql with data
                self.mysql.update_database(table_name, 'song_id', 'genre', song, genre)


    def get_all_song_ids_playlist(self, playlist_id):

        songs_num = 100 #for first round
        offset = 0
        songs_id_list = []

        while songs_num == 100:

            data = self.spotify.get_playlist_items_json(playlist_id, offset = offset)['items']
            
            songs_id_list.extend(self.get_songs_ids_from_json(data))

            songs_num = len(data)
            
            offset += songs_num #this is to know if new round moving offset is needed

        songs_id_list = list(set(songs_id_list))

        return songs_id_list


    def update_predictions_database(self):

        model = mod.import_model('../model/mymodel')

        data = np.array(list(self.mysql.get_all_songs('songs')))

        for song in data:
            song_id = song[0]

            mfcc_decoded = audio.decode_mfccs(song[1], AudioVar.n_mfcc)

            preds = mod.get_prediction_prob(model, mfcc_decoded)

            genre = mod.find_genre_max(preds)

            encoded_preds = mod.encode_prediction_prob(preds)

            self.mysql.update_prediction(genre, encoded_preds, song_id)


    def get_confusion_matrix_and_accuracy(self, X_test, y_test):
        predictions_test = model.predict(X_test)

        merge_pred = []
        y_test_merge = []
        for i in range(232):
            song = predictions_test[i*3:(i+1)*3]
            song = song.mean(axis=0)
            merge_pred.append(song)
            y_merge = y_test[i*3]
            y_test_merge.append(y_merge)
            
            
        predictions_merge = np.array(merge_pred).argmax(axis=1)
        y_test_merge = np.array(y_test_merge)

        accuracy_test = accuracy_score(y_test_merge, predictions_merge)

        #

        confusion_matrix = metrics.confusion_matrix(y_test_merge, predictions_merge)
        cm_nor = confusion_matrix.astype('float') / confusion_matrix.sum(axis=1)[:, np.newaxis]

        x_axis_labels = ['rock', 'electro', 'rap', 'classic', 'reggaeton', 'jazz', 'pop']

        sns.heatmap(cm_nor, cmap="Greens", annot=True, xticklabels=x_axis_labels, yticklabels = x_axis_labels)

        plt.savefig('confusion_mat',bbox_inches='tight', dpi= 600)





        return accuracy_test, plt

    def create_model(self):

        model = keras.Sequential([

        # 1st conv step
        keras.layers.Conv2D(64,(3,3),activation='relu',input_shape=(X_train.shape[1], X_train.shape[2],1),padding='same'),
        
        keras.layers.MaxPooling2D((2,2),strides=(2,3)),
    
        keras.layers.BatchNormalization(),
    
    
        # 2nd conv step
    
        keras.layers.Conv2D(64,(3,3),activation='relu',padding='same'),
        
        keras.layers.MaxPooling2D((2,2),strides=(2,3)),
    
        keras.layers.BatchNormalization(),
    
    
        # 3rd conv step
    
        keras.layers.Conv2D(64,(3,3),activation='relu',padding='same'),
        
        keras.layers.MaxPooling2D((1,2),strides=(1,2)),
    
        keras.layers.BatchNormalization(),
    
    

    
    
        keras.layers.Flatten(),

    
        keras.layers.Dense(1000, activation='relu',kernel_regularizer=tf.keras.regularizers.l2(0.14)),

        keras.layers.Dense(500, activation='relu',kernel_regularizer=tf.keras.regularizers.l2(0.14)),
      
        keras.layers.Dense(250, activation='relu',kernel_regularizer=tf.keras.regularizers.l2(0.13)),
    
        keras.layers.Dense(125, activation='relu',kernel_regularizer=tf.keras.regularizers.l2(0.13)),

        keras.layers.Dense(30, activation='relu',kernel_regularizer=tf.keras.regularizers.l2(0.13)),
  
        keras.layers.Dense(15),
    
        keras.layers.Dense(7, activation='softmax'),
    
        ])

        return model


    def train_model(self, model)

        X_train, y_train, X_val, y_val, X_test, y_test = prepare_input_to_model()


        optimiser = keras.optimizers.Adam(learning_rate=0.00012)
        model.compile(optimizer=optimiser,
                        loss='sparse_categorical_crossentropy',
                        metrics=['accuracy'])


        model.summary()

        history = model.fit(X_train, y_train, validation_data=(X_val, y_val), batch_size=500, epochs=200)


        return model, history
























