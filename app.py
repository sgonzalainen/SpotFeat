from flask import Flask, request, render_template, session, redirect
from src.spotifyAPI import SpotifyAPI
import time
#from flask_session import Session
import datetime
import src.spotify1 as spot
import src.dataset_functions as dataset
import base64
from io import BytesIO



app =Flask(__name__)


#sess = Session()
#sess.init_app(app)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

#app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'


@app.route('/')
def index():

    session['access_token'] = None
    session['access_token_expires'] = datetime.datetime.now()
    session['refresh_token'] = None
    session['access_token_did_expire'] = True

    return render_template('index.html')

@app.route('/start')
def start():
    r = spot.get_auth()

    return f""

@app.route('/callback')
def callback():

    code = request.args.get('code', -1) #this is optional


    answer = spot.get_first_token(code)

    session['access_token'] = answer[0]
    session['access_token_expires'] = answer[2]
    session['refresh_token'] = answer[1]
    session['access_token_did_expire'] = answer[3]

    return redirect("http://localhost:5000/intro", code=302)

    


@app.route('/intro')
def intro():

    headers, access_token, access_token_expires = spot.get_resource_header(session['access_token'], session['access_token_expires'], session['refresh_token'])
    

    session['access_token'] = access_token
    session['access_token_expires'] = access_token_expires

    user_profile, user_top_songs = dataset.update_user_profile_data(headers)

    #here comes new function to get popoularity rating of user
    pop_rating = dataset.get_rating_pop_user(user_id)


    user_name = user_profile.get('name')
    user_id = user_profile.get('user_id')
    user_img = user_profile.get('img_url')
    if user_img == '':
        user_img = 'https://pbs.twimg.com/media/EFIv5HzUcAAdjhl?format=png&name=360x360'

    



    fig, similarity = dataset.get_chart_genres(user_id)
    tmpfile = BytesIO()
    fig.savefig(tmpfile, format='png')
    encoded = base64.b64encode(tmpfile.getvalue()).decode('utf-8')

    other_users = dataset.get_all_users(user_id)


    ######## Camela distance  #######

    avg_distance, min_distance, path_distance = dataset.get_info_distances_artist_ref(user_id)






    session['main_user'] = {'id': user_id, 'name': user_name, 'img_url': user_img }



    
    return render_template('intro.html', user_id = user_id, user_name = user_name, user_img = user_img, fig = encoded, other_users = other_users)


@app.route('/compare')
def compare():

    user2_id =request.args.get('user2', -1)

    headers, access_token, access_token_expires = spot.get_resource_header(session['access_token'], session['access_token_expires'], session['refresh_token'])
    
    user2_profile = dataset.fetch_user2_profile(user2_id)

    user2_name = user2_profile.get('name')
    user2_id = user2_profile.get('user_id')
    user2_img = user2_profile.get('img_url')
    if user2_img == '':
        user2_img = 'https://pbs.twimg.com/media/EFIv5HzUcAAdjhl?format=png&name=360x360'

    user_name = session.get('main_user').get('name')
    user_id = session.get('main_user').get('id')
    user_img = session.get('main_user').get('img_url')

    session['secon_user'] = {'id': user2_id, 'name': user2_name, 'img_url': user2_img }
    
    

    return render_template('compare.html', user_id = user_id, user_name = user_name, user_img = user_img, user2_id = user2_id, user2_name=user2_name, user2_img=user2_img)


@app.route('/playlist')
def playlist():

    headers, access_token, access_token_expires = spot.get_resource_header(session['access_token'], session['access_token_expires'], session['refresh_token'])

    main_user_id = session.get('main_user').get('id')
    secon_user_id = session.get('secon_user').get('id')


    txt_output = dataset.create_mix_playlist(main_user_id, secon_user_id, headers)

    return render_template('playlist.html', txt_output = txt_output)



































app.run(debug=True)