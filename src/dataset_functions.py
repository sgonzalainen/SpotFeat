from src.variables import AudioVar, DatasetVar, DatabaseVar, ScoringVar, Community

import src.spotify as spotify
from src.mysql import mysql as mysql
import src.network as net

import os
import src.audio as audio
import src.model as mod
import src.visual as vis
from tqdm import tqdm
from random import choices
import numpy as np
from datetime import datetime
import pandas as pd
import re
from sklearn.metrics.pairwise import cosine_similarity

import collections
import requests


path_temp_mp3 = AudioVar.path_temp_mp3
path_temp_mp3_video = AudioVar.path_temp_mp3_video

from src.config import client_id,client_secret, redirect_uri




songs_table = DatabaseVar.songs_table
markets = ['ES', 'US', 'SE','DZ','EG','MA','ZA','TN','BH','HK','IN','IL','JP','JO','KW','LB','MY','OM','PS',
'QA','SA','SG','TW','TH','AE','VN','AD','AT','BE','BG','CY','CZ','DK','EE','FI','FR','DE','GR','HU',
'IS','IE','IT','LV','LI','LT','LU','MT','MC','NL','NO','PL','PT','RO','SK','CH','TR','GB','RU',
'BY','KZ','MD','UA','AL','BA','HR','ME','MK','RS','SI','XK','CA','CR','DO','SV','GT','HN','MX','NI','PA'
,'AR','BO','BR','CL','CO','EC','PY','PE','UY','AU','NZ']
model = mod.import_model(AudioVar.model_path)










def get_info_song(data, file_path):


    '''
    Based on song raw data, it cleans and enriches song data (like song genre)
    Args:
        data(dict): song raw data
        file_path(str): path to save temporarily song audio
    Returns:
        song_dict(dict): dictionary containing enriched and cleaned info of a song to be injected to database
        artist_song_list(list): list of pair artist_id and song_id to be injected to database


    '''
    
    song_dict = {}

    artist_song_list = []
    
    song_dict['song_id'] = data['id']
    song_dict['name'] = data['name'][0:100].replace('%','') #limited to 100 characters
    
    song_dict['album_id'] = data['album']['id']
    song_dict['is_playable'] = data.get('is_playable',0)
    song_dict['popularity'] = data['popularity']
    
    
    song_dict['preview_url'] = data['preview_url']
    
    mp3_link = data['preview_url']


    song_dict ['mfccs'], mfccs_array = get_mfccs(mp3_link, file_path) #extracts mfccs array for song

    preds = mod.get_prediction_prob(model, mfccs_array) #predicts song genre based on mfccs
    genre = mod.find_genre_max(preds)
    encoded_preds = mod.encode_prediction_prob(preds) #encodes prediction to save as well to database

    song_dict['genre_model'] = genre
    song_dict['model_pred'] = encoded_preds




    for song in data['artists']:
        artist_song_list.append({'artist_id' : song['id'], 'song_id': data['id']})


    
    return song_dict, artist_song_list


def get_mfccs(mp3_link, file_path):
    '''
    Extracts mfccs array for a given mp3 link
    Args:
        mp3_link(str): preview url for song
        file_path(str): temporary directory to save song audio

    Returns:
        mfccs_array(array): array of mfccs
        mfccs(str): mfccs encoded in single string
    
    '''
    
    audio._create_mp3_file(mp3_link, file_path) #this creates mp3 file
    
    mfccs_array = audio._extract_mfccs(file_path) #creates mfccs array
    
    mfccs = audio.encode_mfccs(mfccs_array) #encodes array to single string to be saved to database
    
    os.remove(file_path) #deleting used mp3 file
    
    
    return mfccs, mfccs_array


def insert_song_data(headers, song_id, col_name = 'song_id'):
    '''
    Insert new song to database
    Args:
        song_id(str): song id
    
    '''

    table_name = songs_table
    
    
    if mysql.check_in_table(table_name,col_name, song_id):#double check if song in database then do nothing
        
        pass
    else:
        data = spotify._get_json_song(headers,song_id) # raw data of a song

        

        if (data['preview_url'] is None): #checks if it finds preview url
            print('Preview url null. Finding through markets a previeuw url')
            for country in markets: #if no preview url found, then iterates through differnt markets to find preview url
                print(f'Trying {country}')
                data = spotify._get_json_song(headers, song_id, country) #new try raw data
                if not (data['preview_url'] is None): #finds preview url
                    print('Preview url found', data['preview_url'])

                    break
                else:
                    pass

            if (data['preview_url'] is None): #if it is still none
                return False



        data['id'] = song_id #this change needed to solve problem with ids non playalbe and relinked. with this solution we may have same songs with two entries with different ids          


        data, data2 = get_info_song(data, path_temp_mp3) #data is song_dict and data2 is artist_song_id info
        mysql.insert_mysql('songs',data)

        new = False

        for item in data2: #this inserts into artist_song all rows
            mysql.insert_mysql('artist_song',item)

            if mysql.check_in_table('artist','artist_id', item['artist_id']):
                pass
            else:
                insert_new_artist(headers, item['artist_id'])#check if artist in artist table
                new = True #to know if a new user were introduced to update network community

    return True







def get_my_full_top_50(headers):
    
    '''
    Creates a dictionary with the scores of all songs in the top_50 lists of a user for short, mid and long term.
    Args:
    
    Returns:
        top_songs_dict(dict): key are songs ids. Values are the score based on its appearance in those lists

    
    '''
    
    short_term_50 = spotify.get_top_50('short_term', headers)
    medium_term_50 = spotify.get_top_50('medium_term', headers)
    long_term_50 = spotify.get_top_50('long_term', headers)
    
    top_songs_dict = {}
    
    
    
    sum_list = short_term_50 + medium_term_50 + long_term_50
    
    sum_list = set(sum_list)
    
    for song in sum_list:
        
        score = 0
        #factors to multiply each time range
        factor_long = 1
        factor_medium = 1
        factor_short = 1
        
        if song in long_term_50:
            pos=long_term_50.index(song)
            score += (100 - pos) * factor_long
        
        if song in medium_term_50:
            pos = medium_term_50.index(song)
            score += (100 - pos) * factor_medium
            
        if song in short_term_50:
            pos = short_term_50.index(song)
            score += (100 - pos) * factor_short
            
        top_songs_dict[song] = score
        
    top_songs_dict = {key:value for key,value in sorted(top_songs_dict.items(), key = lambda x:x[1], reverse = True)}
        
    return top_songs_dict




def collect_my_user_profile(headers):
    '''
    Collects useful profile information about the user, e.g. user info, top songs, top artists
    Args:
        headers(dict): spotify api headers
    Returns:
        temp_dict_user (dict): user info, i.e. name, country, num of followers and img url
        temp_list_top_songs(list): list of top songs to be injected to database. Userid, song id and its score
        temp_list_top_artists (list): list of top artist



    '''
    temp_dict_user = {}
    temp_list_top_songs = []

    data = spotify.get_my_user_info(headers) #request to spotify api with raw data

    user_id = data['id']
    user_country = data['country']
    user_name = data['display_name']
    user_num_followers = data['followers']['total']
    try:
        user_img_url = data['images'][0]['url'] #Keep first image

    except IndexError:
        user_img_url ='' #this will change to predefined unkown pic in app
    
    finally:

        top50 = get_my_full_top_50(headers) #get info related to top50 songs for all time ranges


        temp_dict_user = {'user_id': user_id,
                    'name' : user_name ,
                    'country': user_country,
                    'num_followers': user_num_followers,
                    'img_url' : user_img_url,
                    }

        for key, value in top50.items():
            temp_list_top_songs.append({'user_id': user_id, 'song_id': key, 'song_score': value})


        #top artists ################

        temp_list_top_artists = spotify.get_user_top_artist(headers)

        return temp_dict_user, temp_list_top_songs, temp_list_top_artists


def update_user_profile_data(headers):
    '''
    After user login, this scrapes and updates user info to databases.
    
    '''


    print('Scraping data of login user')
    user_profile, user_top_songs, user_top_artists = collect_my_user_profile(headers) #user data, top songs info to be injected to database and top artists

    user_id = user_profile['user_id']
    table_name = DatabaseVar.user_table
    main_col = 'user_id'

    

    ##Update users table
    print('Updating user info to database')

    if mysql.check_in_table(table_name, main_col, user_id): #checks if user already in user table

        for key, value in user_profile.items():
            if key != 'user_id':
                mysql.update_database(table_name, main_col, key, user_id, value) #updates all fields with new data. #this may be optimized and only update if changes present
            else:
                pass
    else: #new user ever
        mysql.insert_mysql(table_name, user_profile)

    print('Task done')

    ##### Update user_artist table  #############################
    
    print('Updating user artists to database')

    if mysql.check_in_table('user_artist', 'user_id', user_id): #checks if user is already in user_artist table
        mysql.delete_where('user_artist', user_id, 'user_id') #deletes old info
    else:
        pass

    new = False #initial value 

    for artist in user_top_artists:

        if not mysql.check_in_table('artist', 'artist_id', artist): #check if artist in artist table
            insert_new_artist(headers, artist)
            new = True #to know if a new user were introduced to update network community
        else:
            pass

        data  = {'user_id': user_id, 'artist_id': artist}
        mysql.insert_mysql('user_artist', data) #insertes to mysql the favourtie artist for user

    print('Task done')
        
        
  

    ##Update users_songs table

    print('Updating user songs to database')

    table_name = DatabaseVar.user_songs_table
    main_col = 'user_id'

    if mysql.check_in_table(table_name, main_col, user_id): #if user in table, delete to update later
        mysql.delete_where(table_name, user_id, main_col) #delete
    else:
        pass
    
    for song in user_top_songs:

        res = True

        #here !!!!! first check if song in songs database, if not then get data 
        if not mysql.check_in_table(songs_table, 'song_id', song['song_id']): #check if song in songs_table

            print(f"{song['song_id']} song not in database")
            res = insert_song_data(headers, song['song_id']) #insert song to database

            
        else: #if exists then
            pass #do nothing


        if not res: #it did not find preview url then abort inclusion
            continue


        table_name = DatabaseVar.user_songs_table
        mysql.insert_mysql(table_name, song) #Now we add all info


    print('Task done')

    print('Updating albums database if needed')

    update_albums_table_missing(headers) #this checks if new albums have been introduced and scrapes data
    print('Updating artist database if needed')
    update_missing_artists(headers) #this check if some artist is missing in table for some trailing error

    print('Task done')

    print('Recreating artists community')
    net.create_community() #always update at every login. This could be optimized if new artist found by top artist or artist in top songs. Not that "easy" to do if in new songs , therefore we create community every time

    print('Task done')
    

    return user_profile, user_top_songs



def insert_new_artist(headers, artist):
    '''
    Insert new artist in database
    Args:
        artist(str): artist id
    '''

    print(f"{artist} artist not in database")
    tmp_dict = get_info_artist(artist, headers)
    mysql.insert_mysql('artist', tmp_dict) #inserted into mysql table artist
    data = spotify.get_artist_related(artist, headers).get('artists') #list of artist related

    for element in data: #for each artist related
        id_tmp = element['id']
        tmp_dict = {'main_id': artist, 'rel_id': id_tmp}
        mysql.insert_mysql('artist_rel', tmp_dict)

    


def calc_user_profile_genre(user_info):

    

    user_genres_list = [row[0] for row in user_info] #needed to get rid of dummy tuples from mysql 


    genre_list = DatasetVar.genre_list

    user_genre_dict = {genre : user_genres_list.count(genre)  for genre in genre_list}

    return user_genre_dict



def pick_genre(user_genre_dict):

    genres = list(user_genre_dict.keys())
    weights =  list(user_genre_dict.values())
    genre_picked = choices(genres,  weights = weights)[0]

    return genre_picked

def pick_song(user_array, genre):

    temp_array = keep_genre_songs(user_array, genre)

    songs = temp_array[:,0] #songs in first column


    weights =  temp_array[:,1].astype(int) #songs popularity in second column


    try:
        song_picked = choices(songs,  weights = weights)[0]
    except IndexError:
        return None

    return song_picked


def find_songs_playlist(num_songs, users):

    pool_songs = find_pool_songs(users)
    df = create_structure_score_table(pool_songs, users)
    df = add_score_song_playlist(df)

    
    df_preselected = df.groupby(['song_id','artist_id']).sum().sort_values('total_points',ascending=False).reset_index()

    global pool_artist

    pool_artist = []



    df_preselected['corrected_score'] = df_preselected.apply(get_penalty_rep_artist, axis = 1)

    df_selected = df_preselected.sort_values('corrected_score',ascending=False).reset_index().head(num_songs)

    #df_selected = df.groupby('song_id').sum().sort_values('total_points',ascending=False).reset_index().head(num_songs)
    #this was without correction by repetitive artists


    return df, df_selected


def get_penalty_rep_artist(row):

    

    artist = row['artist_id']

    num_appear = pool_artist.count(artist)

    pool_artist.append(artist)

    corrected_score = row['total_points'] / ((1 + (num_appear/10))**ScoringVar.penalty_exponent)

    return corrected_score




def get_list_selected_songs(num_songs, users):
    df, df_selected = find_songs_playlist(num_songs, users)

    selected_songs = list(df_selected.song_id)


    stats_playlist = get_stats_playlist(df, selected_songs)




    return selected_songs, stats_playlist


def get_stats_playlist(df,selected_songs):

    

    contribution_playlist = get_contribution_playlist(df,selected_songs)


    genre_stats_playlist = get_genre_stat_playlist(selected_songs)

    popularity = get_popu_playlist(selected_songs)

    age = get_age_playlist(selected_songs)


    stats_playlist = {'contribution': contribution_playlist, 'genres': genre_stats_playlist, 'popularity': popularity, 'age': age}





    return stats_playlist


def get_popu_playlist(selected_songs):

    popu_list = []

    for song in selected_songs:
        popu_rating = list(mysql.fetch_column_table_where('songs', 'popularity', 'song_id', song))[0][0]
        popu_list.append(popu_rating)



    avg_pop = int(np.mean(popu_list))

    return avg_pop


def get_age_playlist(selected_songs):

    dates_list = []

    for song in selected_songs:
        date = list(mysql.fetch_years_songs_by_song_id(song))[0][0]
        dates_list.append(date)


    ages_list = list(map(extract_age_date, dates_list))

    avg_age = round(np.mean(ages_list),1)

    return avg_age


def get_genre_stat_playlist(selected_songs):

    genre_list = []

    for song in selected_songs:
        genre = list(mysql.fetch_column_table_where('songs', 'COALESCE(genre, genre_model)', 'song_id', song))[0][0]
        genre_list.append(genre)

    counter_genres = collections.Counter(genre_list)

    labels = list(counter_genres.keys())
    values_chart = list(counter_genres.values())

    return {'labels':labels, 'values_chart':values_chart }






def get_contribution_playlist(df,selected_songs):

    df = df[df.song_id.isin(selected_songs)]


    df_user = df.groupby('user_id').sum()

    members_list = df_user.index.values.tolist()

    members_list =  list(map(translate_user_id, members_list)) #this transalte to name user

    values_list = df_user.total_points.values.tolist()


    pct_list =[ round(value / np.sum(values_list) *100, 1) for value in values_list]

    return {'labels': members_list, 'values_chart':pct_list }













def add_score_song_playlist(df):
    df['top_song_points'] = df.apply(get_score_by_top_song, axis = 1)
    df['top_artist_points'] = df.apply(get_score_by_top_artist, axis = 1)
    df['popularity_points'] = df.apply(get_score_popularity, axis = 1)
    df['genre_points'] = df.apply(get_score_genre, axis = 1)

    df['total_points'] = df['top_song_points'] + df['top_artist_points'] + df['popularity_points'] + df['genre_points']

    return df


def get_score_genre(row):

    match = list(mysql.find_genre_song(row['song_id']))
    genre = match[0][0]

    user_genre_profile = np.array(list(mysql.find_user_all_songs_genre(row['user_id'])))
    user_genre_profile = calc_user_profile_genre(user_genre_profile)
    user_genre_profile = {key : value / sum(list(user_genre_profile.values())) for key, value in list(user_genre_profile.items())}

    factor = user_genre_profile[genre]

    return int(ScoringVar.genre * factor)


def get_score_popularity(row):

    match = list(mysql.fetch_column_table_where('songs','popularity', 'song_id', row['song_id']))

    return match[0][0]





def get_score_by_top_song(row):

    match = list(mysql.fetch_score_user_top_song(row['user_id'], row['song_id']))

    if len(match) > 0:
        return match[0][0]
    else:
        return 0

def get_score_by_top_artist(row):

    match = list(mysql.check_song_artist_top(row['user_id'], row['song_id']))

    if len(match) > 0:
        return ScoringVar.top_artist

    else:
        return 0





def create_structure_score_table(pool_songs, users):

    column_songs = []
    column_user = []

    for user in users:

        column_songs.extend(pool_songs)

        list_user  = [user] * len(pool_songs)
        column_user.extend(list_user)

    column_artist = [] #for penalizing repeated artist
    for song in column_songs:
        print(song)
        artist_name = list(mysql.get_artist_by_song_id(song))[0][0] #we pick first artist
        column_artist.append(artist_name)




    data = {'user_id': column_user, 'song_id': column_songs, 'artist_id': column_artist}
    df = pd.DataFrame(data)

    return df






def find_pool_songs(users):

    all_songs = []
    for user in users:
        fetch = list(mysql.fetch_column_table_where('user_song','song_id','user_id',user))
        all_songs.extend([item[0] for item in fetch])

    return list(set(all_songs))


def translate_user_id(user_id):

  

    name = list(mysql.fetch_column_table_where('users', 'name', 'user_id', user_id))[0][0]

    return name




def pick_genre_song_and_include(genre_profile, songs_array, my_playlist, output_txt):

    try_count = 0

    song_selected = None

    while (song_selected is None):

        try_count += 1
        genre_selected = pick_genre(genre_profile) #new genre picked
        song_selected = pick_song(songs_array, genre_selected)

        if try_count == 5:
            return my_playlist, output_txt, songs_array, False


    my_playlist.append(song_selected)

    songs_array = remove_match_song(songs_array, [song_selected]) # no need to go through all songs selected, just the one recently picked
 
    song_name = list(mysql.get_name_song(song_selected))[0][0]

    user_id = songs_array[0,3]
    output_txt.append(f'{song_name} selected as {genre_selected} song in {user_id} TOP songs')



    return my_playlist, output_txt, songs_array, True



        
def get_index_array(array, value):

    i =  np.where(array ==value)[0][0]
    

    return i

def remove_match_song(array, songs, col = 0):

    ids = array[:,col]
    

    i_list = [get_index_array(ids, song) for song in songs ]

    array = np.delete(array, i_list, 0)

    return array

def keep_genre_songs(array, genre):

    i_list = np.where(array ==genre)[0]

    array = array[i_list]

    return array

    











def retrieve_mfccs_song(self, song_id):

    #maybe not in use at the end

    table_name = self.songs_table


    ret = self.mysql.get_mysql_mfccs_song(table_name,song_id)
    ret = list(ret.fetchone())[0]
    mfcc_decoded = audio.decode_mfccs(ret, AudioVar.n_mfcc)

    return mfcc_decoded






def create_mix_playlist(headers, users, num_songs =AudioVar.num_song_playlist):
    song_id_list, stats_playlist = get_list_selected_songs(num_songs, users)

    data = spotify.create_playlist(headers, users)
    playlist_id = data['id']
    spotify.add_songs_to_playlist(playlist_id, song_id_list, headers)

    url_playlist = data['external_urls'].get('spotify')

    return song_id_list, url_playlist, stats_playlist







def create_output_file(user1, txt_output):

    now = datetime.now()
    dt_string = now.strftime("%d_%m_%Y_%H_%M_%S")

    file_name = f'{user1}_mix_tape_{dt_string}'

    

    f = open(f'./output/{file_name}.txt','w')
    txt_output = map(lambda x : x+'\n', txt_output)
    f.writelines(txt_output)
    f.close()

    



def get_chart_genres(user1, user2 = -1):
    
    #this can be improved by Objects!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    user1_genre_profile = np.array(list(mysql.find_user_all_songs_genre(user1)))
    user1_genre_profile = calc_user_profile_genre(user1_genre_profile)  
    categories =  list(user1_genre_profile.keys())
    user1_values = [value / sum(list(user1_genre_profile.values())) for value in list(user1_genre_profile.values())]

    if user2 == -1 :
        fig = vis.draw_starplot(categories, user1_values)
        similarity = -1
    else:

        user2_genre_profile = np.array(list(mysql.find_user_all_songs_genre(user2)))
        user2_genre_profile = calc_user_profile_genre(user2_genre_profile)
        user2_values = [value / sum(list(user2_genre_profile.values())) for value in list(user2_genre_profile.values())]

        fig = vis.draw_starplot(categories, user1_values, user2_values)

        similarity = vis.find_similarity(user1_values,user2_values)

    return fig, similarity

    

   
   


def scrape_artists(self, seed_artist = None):



    mysql_list = list(self.mysql.get_info_for_model('artist', 'artist_id', 'artist_id'))
    mysql_list = [ele[0] for ele in mysql_list]

    if seed_artist == None:
        artist_list = list(self.mysql.get_info_for_model('artist', 'artist_id', 'artist_id'))

        artist_list = [ele[0] for ele in artist_list]
    else: 
        artist_list = [seed_artist]


    count = 0

    for artist in tqdm(artist_list):

        try:

            if self.mysql.check_in_table('artist','artist_id', artist):
                print('artist already in data')
            else:
                tmp_dict = self.get_info_artist(artist)
                self.mysql.insert_mysql('artist', tmp_dict) #inserted into mysql table artist

            

            data = self.spotify.get_artist_related(artist).get('artists') #list of artist related

            if data is None:
                print(f'{artist} artist data not found.')
                continue

            if self.mysql.check_in_table('artist_rel','main_id', artist):
                insert = False
            else:
                insert = True

            for element in data:
                id_tmp = element['id']
                if not self.mysql.check_in_table('artist','artist_id', id_tmp):
                    artist_list.append(id_tmp)
                else:
                    pass

                if insert:
                    tmp_dict = {'main_id': artist, 'rel_id': id_tmp}
                    self.mysql.insert_mysql('artist_rel', tmp_dict)
                else:
                    pass
            
            count += 1

            if count % 500 == 0:
                print(len(artist_list))
                print(artist)

        except:
            print(f'there was some error with {artist}. Going to next')





def get_info_artist(artist_id, headers):
    '''
    Fetches from spotify api info related to artist and returns artist info in format to be inserted to database
    '''

    data = spotify.get_artist_info(artist_id, headers)

 

    tmp_dict = {}

    tmp_dict['artist_id'] = artist_id
    tmp_dict['name'] = data['name'][0:100]
    tmp_dict['popularity'] = data['popularity']
    tmp_dict['followers'] = data['followers']['total']

    try:
        tmp_dict['img_url'] = data['images'][0]['url']
    except IndexError:
        tmp_dict['img_url'] = ''


    return tmp_dict


def get_all_users(user1):

    users= list(mysql.find_all_users())

    users =[user[0] for user in users if user1 not in user[0]]

    return users


def fetch_user2_profile(user):

    user_data = list(mysql.fetch_user(user))[0]

    temp_dict_user = {'user_id': user_data[0],
            'name' : user_data[1] ,
            'country': user_data[2],
            'num_followers': user_data[3],
            'img_url' : user_data[4],
            }



    return temp_dict_user


def get_info_distances_between_users(user1, user2):


    G = net.load_community()


    user1_artists = [item[0] for item in list(mysql.fetch_user_artists(user1)) if net.check_if_in_G(G,item[0])]
    user2_artists = [item[0] for item in list(mysql.fetch_user_artists(user2)) if net.check_if_in_G(G,item[0])]
    
    distances = []
    min_distance = 100000 #dummy large value
    min_path = []
    for artist in user1_artists:
        for rel_artist in user2_artists:
            distance = net.shortest_path_len(G, artist, rel_artist)
            distances.append(distance)
            if distance < min_distance:
                min_distance = distance
                min_path = net.shortest_path(G,  artist, rel_artist)
            else:
                pass

    avg_distance = round(np.mean(distances),1)

    return avg_distance, min_distance, min_path


def get_my_matches(main_user):


    other_users_info = get_other_users_info(main_user)

    other_users = [other.get('user_id') for other in other_users_info]

    

    scores_by_distance = get_score_by_distance(main_user, other_users) #mathces info by distance between top artist
    scores_by_genre = get_score_by_genres(main_user, other_users) #matches between genres

    mean_score = list(map(lambda x,y: round(np.mean([x,y]) * 100 if not np.isnan(x) else y * 100, 1), scores_by_distance, scores_by_genre))

    all_scores = [{'user_id': other , 'score': score} for other, score in zip(other_users,mean_score) ]

    #just to be sure dictioanries are in same order. this could be optimized
    for other in other_users_info:
        for score in all_scores:
            if score['user_id'] == other['user_id']:
                other['score'] = score['score']
                break
            else:
                pass
    




    

    other_users_info= sorted(other_users_info, reverse = True, key = lambda x: float(x.get('score')))

    

    return other_users_info




def get_score_by_genres(main_user, other_users):


    main_user_profile = np.array(list(mysql.find_user_all_songs_genre(main_user)))
    main_user_profile = [list(calc_user_profile_genre(main_user_profile).values())]

    others_profiles = []
    for other in other_users:
        other_user_profile = np.array(list(mysql.find_user_all_songs_genre(other)))
        other_user_profile = list(calc_user_profile_genre(other_user_profile).values())
        others_profiles.append(other_user_profile)

    scores = cosine_similarity(main_user_profile,others_profiles)[0] 



    return scores

    



def get_score_by_distance(main_user, other_users):

    

    info_distances = []
    for other in other_users:
        avg_distance, min_distance, min_path = get_info_distances_between_users(main_user, other)

        tmp_dict = {'user_name': other, 'avg_distance':avg_distance, 'min_distance': min_distance, 'min_path':min_path }
        info_distances.append(tmp_dict)

        

    df = pd.DataFrame(info_distances)
    scores = list(df.avg_distance.rank(ascending = False, pct=True))

    return scores



def fecth_match_score(user_id, other_users_info):

    for user in other_users_info:

        if user.get('user_id') == user_id:
            return user.get('score')





    







            




def get_info_distances_artist_ref(user):

    print('Calculating distances for community')

    G = net.load_community()

    
    user_artists = [item[0] for item in list(mysql.fetch_user_artists(user)) if net.check_if_in_G(G,item[0])] #this is to avoid take into account artist which are not connected to community
    
    user_artists = sorted(user_artists, key = lambda x: net.shortest_path_len(G, x))
    
    distances = [net.shortest_path_len(G, artist)   for artist in user_artists]
    avg_distance = round(np.mean(distances),1)

    min_distance = distances[0]

    min_path = net.shortest_path(G, user_artists[0])

    min_path = list(map(extract_url_img_by_artist_name, min_path))

    ref_artist = Community.artist_ref_distance #to pass to app to show in html


    print('Task done')


    

    return avg_distance, min_distance, min_path, ref_artist


def extract_url_img_by_artist_name(artist_name):

    artist_url = list(mysql.fetch_column_table_where('artist', 'img_url', 'name', artist_name))[0][0]


    return {'name': artist_name, 'artist_url': artist_url}


def find_matches_by_artist_for_playlist(user1, user2):

    res = list(mysql.find_artist_in_other_songs(user1, user2))

    tmp_keywords = []
    clean_list_songs = [] #for no duplicates
    for item in res:
         keyword = item[0]+item[1]
         if keyword not in tmp_keywords:
             clean_list_songs.append([item[0], item[1], item[2]])
             tmp_keywords.append(keyword)

    return clean_list_songs


def get_rating_popu_user(user):

    print('Calculating popularity')

    songs = list(mysql.fetch_popularity(user))
    avg_pop = int(np.mean([song[1] for song in songs]))

    #con posibilidad de poder devolver el mayor popular

    print('Task done')
    return avg_pop


def get_years_user(user):

    print('Calculating musical age')

    data = list(mysql.fetch_years_songs(user))

    list_dates = [item[0] for item in data]

    list_ages = list(map(extract_age_date, list_dates))

    print('Task done')

    return round(np.mean(list_ages),1)

def extract_age_date(date):

    year_now = datetime.now().year

    pattern = r'\d{4}'

    try:
        year = re.search(pattern, date).group()
    except:
        return np.NaN

    else:

        age = int(year_now - int(year))

        return age




def get_other_users_info(main_user_id):

    #to be developed further for similarity

    other_users = get_all_users(main_user_id)

    others_info = []

    for other in other_users:
        others_info.append(get_full_info_user(other))

    return others_info


def get_full_info_user(user_id):

    profile = fetch_user2_profile(user_id)
    name = profile.get('name')
    img = profile.get('img_url')

    if img == '':
        img = 'https://pbs.twimg.com/media/EFIv5HzUcAAdjhl?format=png&name=360x360'


    tmp_dict = {'name': name, 'user_id': user_id, 'img_url': img}

    return tmp_dict





def collect_info_new_playlist(headers, song_id_list):

    info_playlist = []

    for song in song_id_list:

        info_song = get_info_song_dict_by_id(song)

        info_playlist.append(info_song)


    return info_playlist

def get_info_song_dict_by_id(song):



    match = list(mysql.fetch_report_song(song))[0]


    song_name = match[0]
    artist_name = match[1]
    album_name = match[2]
    artist_img = match[3]
    album_img = match[4]
    preview_url = match[5]

    #if artist_img == '':
        #artist_img = 'https://www.file-extensions.org/imgs/articles/4/375/unknown-file-icon-hi.png'

    if album_img == '':
        album_img = 'https://www.file-extensions.org/imgs/articles/4/375/unknown-file-icon-hi.png' #this link may have problems


    info_song = {'song_name': song_name, 'artist_name': artist_name, 'album_name': album_name, 'artist_img': artist_img, 'album_img': album_img, 'preview_url':preview_url }

    return info_song



def genre_profile_api(user_id):

    user_profile = np.array(list(mysql.find_user_all_songs_genre(user_id)))
    user_profile = calc_user_profile_genre(user_profile)

    genre_list = list(user_profile.keys())
    values_list = list(user_profile.values())

    user_list = [ {'genre': key, 'value': value} for key, value in user_profile.items()]  #for JS file




    return genre_list, values_list


def get_my_trending(headers):

    trending_songs = spotify.get_top_50('short_term', headers)

    info_trending = []
    for song in trending_songs:
        info_song = get_info_song_dict_by_id(song)
        info_trending.append(info_song)

    return info_trending


def get_my_top(headers):

    top_songs = spotify.get_top_50('long_term', headers)

    info_top = []
    for song in top_songs:

        try:

            info_song = get_info_song_dict_by_id(song)

        except:
            continue

        else:
            info_top.append(info_song)

    return info_top



def update_albums_table_missing(headers):
    '''
    Checks if new albums have been introduced and scrapes data
    
    '''

    albums_to_scrape = [album[0] for album in list(mysql.fetch_album_in_songs_null())]

    for album in albums_to_scrape:

        print(f"{album} album not in database")

        data = spotify.get_album_info(headers,album)

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

        mysql.insert_mysql('albums',album_dict)

        for artist in data['artists']:
            mysql.insert_mysql('artist_album',{'artist_id' : artist['id'], 'album_id': album})


def update_missing_artists(headers):
    '''Checks if some artist is missing in table for some trailing error'''


    artist_to_scrape = [artist[0] for artist in list(mysql.fetch_artist_in_songs_null())]

    for artist in artist_to_scrape:
        print(f"{artist} artist not in database")
        data = spotify.get_artist_info(artist, headers)

        tmp_dict = {}

        tmp_dict['artist_id'] = artist
        tmp_dict['name'] = data['name'][0:100]
        tmp_dict['popularity'] = data['popularity']
        tmp_dict['followers'] = data['followers']['total']

        try:
            tmp_dict['img_url'] = data['images'][0]['url']
        except IndexError:
            tmp_dict['img_url'] = ''


        mysql.insert_mysql('artist', tmp_dict) #inserted into mysql table artist
        data = spotify.get_artist_related(artist, headers).get('artists') #list of artist related

        for element in data: #for each artist related
            id_tmp = element['id']
            tmp_dict = {'main_id': artist, 'rel_id': id_tmp}
            mysql.insert_mysql('artist_rel', tmp_dict)



def create_video(mytop_list):
    '''
    Main function to creates video mix tape based on top songs
    Args:
        mytop_list(list): list of top song ids
    '''


    videoclips = []

    for item in mytop_list:

        audioclip = create_audio(item)
        videoclip = create_video_clip(item, audioclip)
        if videoclip is None: #if some error happen in video production
            continue
        videoclips.append(videoclip)


    merged_videoclip = audio.merge_video_clips(videoclips)


    return merged_videoclip

    







def create_audio(item):

    mp3_link =  item.get('preview_url')

    audio._create_mp3_file(mp3_link, path_temp_mp3_video) #this creates mp3 file
    
    audioclip = audio.create_clip(path_temp_mp3_video)
    
    os.remove(path_temp_mp3_video) #deleting used mp3 file

    return audioclip


def create_video_clip(item, audioclip):

    img_url = item.get('artist_img')

    if img_url == '':

        img_url = item.get('album_img')



    videoclip = audio.create_video_clip(img_url, audioclip)

    return videoclip

