import json

data = dict()

with open("config/config.json") as config_data:
    data['config'] = json.load(config_data)

with open("config/flairs.json") as raw_flair_data:
    data['flair'] = json.load(raw_flair_data)
