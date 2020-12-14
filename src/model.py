
from sklearn.model_selection import train_test_split
import src.audio as audio
from src.variables import AudioVar, DatasetVar, DatabaseVar
import numpy as np
from tensorflow import keras
import matplotlib.pyplot as plt



def decode_input_model(data):
    X = []
    y = []
    for song in data:
        decoded = audio.decode_mfccs(song[0], AudioVar.n_mfcc)
        X.append(decoded)
        y.append(song[1])
    
    return X,y

def split_train_val_test(X, y, test_size = DatasetVar.test_size, val_size = DatasetVar.val_size, random_state = 5):

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state = random_state)

    X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=val_size, random_state = random_state)

    X_train, y_train = split_and_propagate_genre(X_train, y_train)
    X_val, y_val = split_and_propagate_genre(X_val, y_val)
    X_test, y_test = split_and_propagate_genre(X_test, y_test)

    return X_train, y_train, X_val, y_val, X_test, y_test
    





def split_and_propagate_genre(mfcc_list, genre_list):

    new_mfcc_list = []
    new_genre_list = []

    for mfcc, genre in zip(mfcc_list, genre_list):

        mfcc_split = audio.split_mfcc(mfcc)

        num_split = len(mfcc_split)

        genre_model = DatasetVar.genre_dict.get(genre)
        genre_split = [genre_model] * num_split

        new_mfcc_list.extend(mfcc_split)

        
        new_genre_list.extend(genre_split)

    new_mfcc_list = np.array(new_mfcc_list)[..., np.newaxis] #np array needed for keras. New axis needed for convolution channel
    new_genre_list = np.array(new_genre_list)[..., np.newaxis] #np array needed for keras. New axis needed for convolution channel

    return new_mfcc_list, new_genre_list




def plot_history(history):

    """Plots accuracy/loss for training/validation set as a function of the epochs
        :param history: Training history of model
        :return:
    """

    fig, axs = plt.subplots(2)

    # create accuracy sublpot
    axs[0].plot(history.history["accuracy"], label="Train")
    axs[0].plot(history.history['val_accuracy'], label="Val")
    axs[0].set_ylabel("Accuracy %")
    axs[0].legend(loc="lower right")
    axs[0].set_title("Metric eval")

    # create error sublpot
    axs[1].plot(history.history["loss"], label="Train")
    axs[1].plot(history.history["val_loss"], label="Val")
    axs[1].set_ylabel("MSE")
    axs[1].set_xlabel("Epoch")
    axs[1].legend(loc="upper right")
    axs[1].set_title("Error eval")

    plt.subplots_adjust(top = 2)

    

    return fig

    


def get_prediction_prob(model, mfcc):

    mfcc_inputs = np.array(audio.split_mfcc(mfcc))
    mfcc_inputs = mfcc_inputs[..., np.newaxis]

    preds = model.predict(mfcc_inputs).mean(axis=0) #mean to get mean across all mini samples

    return preds


def encode_prediction_prob(preds):
    '''
    input array
    '''
    return ' '.join(str(val)for val in preds)


def find_genre_max(preds):

    ind = preds.argmax()

    genre_dict = DatasetVar.genre_dict

    genre = [key for key, value in genre_dict.items() if value == ind][0]

    return genre


def import_model(model_path):
    model = keras.models.load_model(model_path)
    
    return model


def save_model(model, model_path):
    model.save(model_path)
    





















































