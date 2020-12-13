from dotenv import load_dotenv, find_dotenv
import os


class AudioVar():

    sample_rate = 22050
    n_mfcc = 14
    hop_length = 512
    n_fft = 2048
    path_temp_mp3 = './data/temp_mp3/song_temp.mp3'

    model_sample_sec = 9

    model_path = './model/mymodel'


    seconds_clip = 5





class DatasetVar():

    path_songs = './data/songs.json'

    genre_dict = {'rock': 0, 'electro': 1, 'rap': 2, 'classic': 3, 'reggaeton': 4, 'jazz': 5, 'pop':6}

    genre_list = ['rock', 'electro', 'rap', 'classic', 'reggaeton', 'jazz', 'pop']

    test_size = 0.1

    val_size = 0.15


class DatabaseVar():
    

    load_dotenv('src/.env')

    songs_table = 'songs'


    artist_table = 'artist'

    album_table = 'album'

    user_table = 'users'

    user_songs_table = 'user_song'

    artist_album_table = 'artist_album'

class Community():

    path_G = './data/network/network_artists.gpickle'

    artist_ref_distance = 'Camela'

    penalty_not_path = 15


class ScoringVar():
    top_artist = 50
    genre = 50

    









