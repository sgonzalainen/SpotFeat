import networkx as nx
from src.variables import Community
import pandas as pd
from src.mysql import mysql as mysql



def create_community():

    df_comm = pd.DataFrame(mysql.fetch_community(), columns = ['artist1', 'artist2'])
    G = nx.from_pandas_edgelist(df_comm,  source='artist1', target='artist2')

    nx.write_gpickle(G, Community.path_G)

    return df_comm



def load_community():

    G = nx.read_gpickle(Community.path_G)

    return G


def shortest_path_len(G, main_artist, ref_artist = Community.artist_ref_distance):

    try:
        return nx.shortest_path_length(G, source = main_artist,target = ref_artist)

    except:
        return Community.penalty_not_path ##penalty for not having connection



    



    


def shortest_path(G, main_artist, ref_artist = Community.artist_ref_distance):

    
    return nx.shortest_path(G, source = main_artist,target = ref_artist)



def check_if_in_G(G, artist):
    return G.has_node(artist)
