# gistapi

Gistapi is a simple HTTP API server implemented in Flask for searching a user's public Github Gists. The gistapi code in this repository has
been left incomplete for you to finish.

## Challenge

The existing code already implements most of the Flask boilerplate for you. The main functionality is left for you to implement.  The goal is to
implement an endpoint that searches a user's Gists with a regular expression.  For example, I'd like to know all Gists for user `justdionysus` that
contain the pattern `import requests`. There is also a failing test that should pass once you've successfully implemented the search
process (and should illustrate the expected format of the response).  The code in `gistapi.py` contains some comments to help you find your way.

To complete the challenge, you'll have to write some HTTP queries from `Gistapi` to the Github API to pull down each Gist for the target user.
Please don't use a github API client (i.e. using an HTTP request library like requests or aiohttp or urllib3 is fine but not PyGithub or similar).

There are also a number of places in the code marked `# BONUS` where additional code would yield a more robust or performant service.  If you
finish the above quickly, feel free to investigate these added features or anything else you think might make for an interesting demo.  Please
don't work on the additional optional features before the main task is complete.

# Running the app

```bash
# Directly
python -m gistapi.gistapi

# Via gunicorn
gunicorn gistapi.gistapi:app

# Via Docker
docker build . -t flask-app
docker run -p 8000:8000 flask-app

# Via docker-compose
docker-compose up
```
