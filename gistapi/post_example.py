import requests

url = 'http://0.0.0.0:9876/api/v1/search'
data = {
        'username': 'justdionysus',
        'pattern' : 'import requests',
       }

response = requests.post(url, json = data)
print(response.status_code)
print(response.text)

data = {
        'username': 'justdionysus',
        'pattern' : 'TerbiumLabsChallenge_[0-9]+',
       }

response = requests.post(url, json = data)
print(response.status_code)
print(response.text)
