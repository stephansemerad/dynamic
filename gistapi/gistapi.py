# coding=utf-8
"""
Exposes a simple HTTP API to search a users Gists via a regular expression.
Github provides the Gist service as a pastebin analog for sharing code and
other develpment artifacts.  See http://gist.github.com for details.  This
module implements a Flask server exposing two endpoints: a simple ping
endpoint to verify the server is up and responding and a search endpoint
providing a search across all public Gists for a given Github account.
"""

import requests, re, urllib3
from datetime import datetime
from flask import Flask, jsonify, request, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
from dateutil import parser

# *The* app object
app = Flask(__name__,template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI']           = 'sqlite:///database.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']    = False

db = SQLAlchemy(app)

class Search(db.Model):
    id              = db.Column(db.Integer, primary_key = True)
    raw_url         = db.Column(db.String(), nullable = False)
    username        = db.Column(db.String(), nullable = False)
    pattern         = db.Column(db.String(), nullable = False)
    gist_id         = db.Column(db.String(), nullable = False)
    updated_at      = db.Column(db.DateTime, nullable = False)
    filename        = db.Column(db.String(), nullable = False)
    content         = db.Column(db.String(), nullable = False)
    highlighted     = db.Column(db.String(), nullable = False)

db.create_all()

@app.route("/ping")
def ping():
    """Provide a static response to a simple GET request."""
    return "pong"

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

def gists_for_user(username):
    """Provides the list of gist metadata for a given user.
    This abstracts the /users/:username/gist endpoint from the Github API.
    See https://developer.github.com/v3/gists/#list-a-users-gists for
    more information.
    Args:
        username (string): the user to query gists for
    Returns:
        The dict parsed from the json response from the Github API.  See
        the above URL for details of the expected structure.
    """
    gists_url = 'https://api.github.com/users/{username}/gists'.format(username=username)
    response = requests.get(gists_url)
    return response

    # BONUS: What failures could happen?
    # *** STEPHAN : 
    # API Limit reached
    # Special Charactes in username.
    # username and pattern not provided
    # Site not available
    # Time out
    # Wrong Request Method  

    # BONUS: Paging? How does this work for users with tons of gists?
    # *** STEPHAN : 
    # requests will have 30 items by default, you can use page or per_page to loop throught them. 
    # however per_page will need to be tested as "for technical reasons not all endpoints respect the per_page"
    # https://api.github.com/user/repos?page=3&per_page=100>

@app.route("/api/v1/search", methods=['POST'])
def search():
    """Provides matches for a single pattern across a single users gists.
    Pulls down a list of all gists for a given user and then searches
    each gist for a given regular expression.
    Returns:
        A Flask Response object of type application/json.  The result
        object contains the list of matches along with a 'status' key
        indicating any failure conditions.
    """   
    # Check what type of request it is
    post_data = request.get_json()
    username  = post_data['username']
    pattern   = post_data['pattern']


    # BONUS: Validate the arguments?
    # Validate username and pattern, could be done also with Flask Marshmallow, but since 
    # its only 2, and they are strings, I thought it be easier this way. 
    if username == None or username == '':
        return jsonify({ 'status': 'error', 'message' : f"Please provide a username"}), 400

    if pattern == None or pattern == '':
        return jsonify({ 'status': 'error', 'message' : f"Please provide a pattern"}), 400

    # #making username lower just to handle it better and stripping white space incase of mistake
    username    = username.lower().strip(' ')

    # # BONUS: Handle invalid users?
    # # Check if the username is valid
    # # Stephan: Sure
    # # Github username may only contain alphanumeric characters or hyphens.
    # # Github username cannot have multiple consecutive hyphens.
    # # Github username cannot begin or end with a hyphen.
    # # Maximum is 39 characters.

    user_name_check = re.search(r"^[a-z\d](?:[a-z\d]|-(?=[a-z\d])){0,38}$", username)
    user_name_check = bool(user_name_check)
    if not user_name_check:
        return jsonify({ 'status': 'error', 'message' : f"Github username provided is invalid"}), 400


    response        = gists_for_user(username)
    gists           = response.json()

    limit           = response.headers['X-RateLimit-Limit']
    remaining       = response.headers['X-RateLimit-Remaining']
    reset           = datetime.fromtimestamp(int(response.headers['X-RateLimit-Reset']))

    # Check if there are still free remaining API calls
    if int(remaining) == 0: 
        return jsonify({'status': 'error', 'message' : f'Exceeded API calls Limit({limit}), reset will be at {reset}'}), 429
       

    # # REQUIRED: Fetch each gist and check for the pattern

    # # BONUS: What about huge gists?
    # # *** STEPHAN : Huge gitst need are displayed if states in the git that "truncated": true
    # # we will need to do a get to the raw_url I did this with url lib. 
    # # if larger than 10 MB we will need to clone using the git_pull_url
    # # https://docs.github.com/en/rest/reference/gists#list-a-users-gists [Truncation][2nd Paragrah]
    # # here the best solution would be to check the size that is bein pased and if its > 10 MB then we should pull. 
    # # Here there is 2 methods, but the best way would to do it with git and then with os go through the files. 
    # # import git 
    # # g = git.cmd.Git(git_dir)
    # # g.pull()

    # # BONUS: Can we cache results in a datastore/db?
    # # Yes, this would save us from not having to search for a pattern again in large gists. 
    # # I did it by getting all raw_urls where pattern + username match in the db and then checkin and returning if the retrieved url 
    # # exist in the db. 

    # # For fun I also highlighted the pattern in the gists so its visible in HTML. 
    result = {}
    result['matches']  = []
    result['highlighted']  = []

    for gist in gists:
        gist_id     = gist['id']
        updated_at  = gist['updated_at']
        updated_at  = parser.isoparse(updated_at) # converting Z time to datetime to insert into db
        files       = gist['files']     

        # Caching
        # get values that already have been searched before. 
        db_raw_urls = db.session.query(Search.raw_url).filter(Search.username == username, Search.pattern == pattern).all()
        db_raw_urls = [r.raw_url for r in db_raw_urls]

        for file in files:
            filename    = files[file]['filename']
            raw_url     = files[file]['raw_url']
            
            if raw_url in db_raw_urls:
                # Cached
                db_gist = db.session.query(Search).filter(Search.raw_url==raw_url).first()  
                result['matches'].append(db_gist.raw_url)
                result['highlighted'].append({db_gist.filename : db_gist.highlighted})
            else:
                # Not Cached
                response    = requests.get(raw_url)
                content     = response.content.decode("utf-8")
                print(pattern)
                matches     = re.findall(pattern, content)
                print(matches)
                highlighted = content #

                # Only adding matched when a match really was found. 
                if matches != []:

                    # added highlighted HTML for fun, could be done nicely with a template. 
                    for match in matches:
                        highlighted = highlighted.replace(match, '<span style="background-color: #aaffaa; color: #227722;">' + str(match) + '</span>')
                    highlighted = highlighted.replace('\n', '<br>')
                    
                    result['matches'].append(raw_url)
                    result['highlighted'].append({filename : highlighted})
                    search = Search(
                        username       = username, 
                        pattern        = pattern, 
                        raw_url        = raw_url, 
                        gist_id        = gist_id, 
                        updated_at     = updated_at, 
                        filename       = filename, 
                        content        = content, 
                        highlighted    = highlighted,                     
                    )
                    db.session.add(search)
                    db.session.commit()

    result['status']    = 'success'
    result['username']  = username
    result['pattern']   = pattern
    return jsonify(result), 200


if __name__ == '__main__':
    app.run(debug=True, 
            host='0.0.0.0',
            port=9876)
