from src.variables import AudioVar
import requests
import librosa
import audioread
import numpy as np
import moviepy.editor as mpy
import matplotlib.pyplot as plt
import librosa.display

sample_rate = AudioVar.sample_rate
n_mfcc = AudioVar.n_mfcc
hop_length = AudioVar.hop_length
n_fft = AudioVar.n_fft

#path_temp_mp3 = Audio.path_temp_mp3


def _create_mp3_file( mp3_link, path_temp_mp3):
    '''
    Creates mp3 file for further MFCCs coefficients extraction
    Args:
        mp3_link(str): link to song preview
        file_path(str): path to save temporarily mp3 file
    '''
    endpoint = mp3_link
    s = requests.Session()
    song = s.get(endpoint, stream = True)
    with open(path_temp_mp3, 'wb') as f:
        f.write(song.content)


def _extract_mfccs(path_temp_mp3, sample_rate = sample_rate, n_mfcc = n_mfcc, hop_length = hop_length, n_fft = n_fft):

    '''
    Extracts mfccs coefficients for the audio donwloaded before
    Args:
        path_temp_mp3(str): temporary directory where mp3 file is stored
        sample_rate(int): settings to extract mfccs
        n_mfcc(int): number of coefficients
        hop_length(int): settings to extract mfccs
        n_fft(int): settings to extract mfccs

    Returns:
        mfcc(array): array with coefficients

    '''


    signal, sample_rate = librosa.load(path_temp_mp3, sr = sample_rate)
    mfcc = librosa.feature.mfcc(signal, sample_rate, n_mfcc = n_mfcc, n_fft = n_fft, hop_length = hop_length)
    
    return mfcc

def encode_mfccs(mfccs):
    '''
    Encodes mfccs array to string to save in database
    Args:
        mfccs(array): array of mfccs coefficients
    Returns:
        string(str): encoded string of mfccs
    
    '''
    string = '_'.join(str(item) for row in mfccs for item in row)
    
    return string


def decode_mfccs(string, n_mfcc):
    
    temp_list = string.split('_')
    long = int(len(temp_list) / n_mfcc)
 
    shape = (n_mfcc, long)
    mfccs_array = np.array(temp_list,dtype=float).reshape(shape)
    
    return mfccs_array



def split_mfcc(mfcc):

    '''Splits mfccs array in several samples for model input
    Args:
        mfcc(array)
    Returns:
        mfcc_splited(list): list of arrays of mfccs

    '''

    total_frames = mfcc.shape[1]

    frames_per_second =  AudioVar.sample_rate // AudioVar.hop_length

    frames_per_sample = AudioVar.model_sample_sec * frames_per_second

    num_split = (total_frames) // frames_per_sample

    mfcc_splited=[]

    for i in range(num_split):
        
        start = 0 + i * frames_per_sample
        end = frames_per_sample * (1 + i)
        
        sample = mfcc[:, start : end ]
       
        mfcc_splited.append(sample)
    
    return mfcc_splited


def create_clip(path_temp_mp3):

    audioclip = mpy.AudioFileClip(path_temp_mp3)
    audioclip = audioclip.subclip(t_start = 0, t_end = AudioVar.seconds_clip)

    return audioclip


def create_video_clip(img_url, audioclip):

    

    try:
        clip = mpy.ImageSequenceClip([img_url], durations =[AudioVar.seconds_clip])

    except:
        print(f'{img_url} Error on this imageclip. Could not be created')
        return None

    else:

        videoclip = clip.set_audio(audioclip)


    return videoclip

def merge_video_clips(videoclips):


    merged_videoclip = mpy.concatenate_videoclips(videoclips, method='compose')

    return merged_videoclip



def plot_mfcc(mfcc,sample_rate=sample_rate,hop_length=hop_length):
    '''This function plots mfcc'''
    #plt.figure()
    fig, ax = plt.subplots()
    im=librosa.display.specshow(mfcc, sr=sample_rate, hop_length=hop_length,ax=ax)

    plt.xlabel("Time")
    plt.ylabel("MFCC coefficients")
    
    fig.colorbar(im)
    plt.title("MFCCs")
    
    return fig


















    







