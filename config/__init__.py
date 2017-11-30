import json

data = dict()

with open("config/config.json") as config_data:
    data['config'] = json.load(config_data)

with open("config/creds.json") as creds_data:
    data['creds'] = json.load(creds_data)

flair_data = None
with open("config/flairs.json") as raw_flair_data:
    flair_data = json.load(raw_flair_data)
