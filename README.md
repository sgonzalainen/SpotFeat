 <div style="text-align:center"><img src="img/banner.png" width=800 /></div>




# SpotiFeat (Ironhack Data Bootcamp Final Project)

Have you ever thrown a party and did not know which songs to play on Spotify? Or gone on a road trip and endured your friend's boring songs over and over?

Wouldn't you fancy an app to take care of this and create a playlist that takes into account the musical taste of everyone at just one click?

Let an algorithm and machine learning do the dirty work for you!

For that and much more, I designed Spotifeat as my final project at Ironhack Data Analytics bootcamp.
Take a look at the demo video on my [Linkedin post](https://www.linkedin.com/posts/sergio-gon-rod_machinelearning-bootcamp-activity-6754097773982846976-tjYu) .

With Spotifeat, you can:
* Create automatically playlists for parties
* Discover singular stats about you
* Find and follow on Spotify other Spotifeat users
* See your trending songs
* Listen to a remix of your top50 songs on Spotify

** Disclaimer ** 
My background on html/web dev before this project was none. I just intend to submit a MVP on that terms. Therefore, html views are of course not reactive and can be massively improved.


## How does it work? The Data science behind in brief 🧐

### The Music Genre Classificator

One of the main core components of this project. This classificator "listens" a song and classifies the genre of the song.

#### Training Dataset
I decided to classify songs in the following main music genres:

* Rock
* Electronic 
* Rap
* Classical
* Reggaeton
* Jazz
* Pop

I managed to create my own dataset of classified songs as follows:

On Spotify I manually created playlists for each genre by adding one song of an artist which clearly sticks to this genre. Later on, with the help of Spotify API, I prepared a pipeline which reads the artists of each playlist, find the top 10 songs, donwloads the sample track and converts the audio into an array (MFCCs audio extraction).

Based on this, I get hold of a dataset of more than 1000 songs. 


#### Data Preparation

Dataset is split in train and test.

After that, in order to increase the sample number and also improve model accuracy, I decided to chop the audio samples in 3 parts of 9 seconds each. So that in order to calculate the accuracy of the model, the model classification would be the average of each prediction.

#### Model

The model is a neural network consisting on 3 layers of convolutional + maxpooling, followed by 7 dense layers.


### The Artist Community

#### Concept

Another core component is the concept of artist social network community I created based on the artists-related-to-artist info provided by Spotify Api.
This artist community is a monodirectional community which links artists. This therefore determines how far or close your preferred artists are from someone else's for playlist generation and also for the awesome Camela distance stat.

#### Scraping Algorithm
Spotify artist are infinite. At some point I had to stop scraping them, but basically the approach is that from one seed artist I take the top 20 related artists. For each new artist found in databse I scrape his/her 20 related artist, and so on and so on.... 

My artist community consists of around 70000 artists.


### The Playlist Generator

The playlist generator picks the top 50 scored songs. 

Each member(user) of the party(playlist) provides the top 50 songs at short/medium/long term. With that pool of songs, each song is scored by each member based on several aspects, for example:
* Whether song is on his top songs or not
* Based on the song's genre. Remember each user has his/her top songs, therefore each user has his/her normalize vector of genre musical taste.
* Based on distance of the artist related to top user's artists.

In order to avoid repetition of artists in the playlist caused by users with strong desires for an artist and music genre, there is a penalization process for subsequent songs from same artist.










