import requests
import praw
import re
from config import data as config
from string import Template
import time

matchTemplate = Template('>[](${link})\n>###${event}\n>###${time}\n>###${team1}\n>###${team2}\n>###${flair1}\n>###${flair2}\n\n[](#separator)\n\n')
flairdata = config['flair']


def get_data():
    try:
        result_data = requests.get(config['config']['overggupcoming'],  headers={"User-Agent": config['config']['user-agent']})
        result_data.raise_for_status()
        return result_data.json()
    except Exception:
        return None


def find_flair_by_name(team_name):
    team_name = ''.join(x for x in team_name.lower() if x.isalnum())
    for key, flair in flairdata['flairs'].items():
        list_name = ''.join(x for x in flair['name'].lower() if x.isalnum())
        if list_name == team_name:
            return '[](#teams-c' + flair['col'] + '-r' + flair['row'] + ')'
    return '[](#noflair)'
        
        
def make_time(timestamp):
    current_time = time.time()
    if current_time > timestamp:
        return '**LIVE**'
    time_diff = timestamp - current_time
    
    m, s = divmod(time_diff, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)

    if d > 99:
        return None
    elif d > 0:
        return str(int(d)) + 'd'
    elif h > 0:
        return str(int(h)) + 'h'
    else:
        return str(int(m)) + 'm'

    
def make_match_string(match_item):
    match_time = make_time(int(match_item['timestamp']))
    if not match_time:
        return None

    mapping = dict()
    mapping['link'] = match_item['match_link']
    mapping['event'] = match_item['event_name']
    mapping['time'] = match_time
    mapping['team1'] = match_item['teams'][0]['name']
    mapping['team2'] = match_item['teams'][1]['name']
    if not mapping['team1'] or not mapping['team2']:
        return None
    mapping['flair1'] = find_flair_by_name(mapping['team1'])
    mapping['flair2'] = find_flair_by_name(mapping['team2'])

    return matchTemplate.substitute(mapping)


def make_ticker_string(match_data):
    ticker_string = ''
    count = 0
    for match_item in match_data:
        match_string = make_match_string(match_item)
        if not match_string:
            continue
        ticker_string += match_string
        count += 1
        if count == 5:
            break
    return ticker_string


def update_sidebar(ticker_string):
    reddit_praw = praw.Reddit(config['config']['account'], user_agent=config['config']['user-agent'])
    subreddit = reddit_praw.subreddit(config['config']['subreddit'])
    settings = subreddit.mod.settings()
    sidebar = settings['description']
    
    sidebar = re.sub(r"(\[\]\(#mtstart\)\n)(.*)(\[\]\(#mtend\))',r'\1" + ticker_string + r"\3", sidebar, flags=re.M | re.DOTALL)
    
    subreddit.mod.update(description=sidebar)


while True:
    try:
        data = get_data()
        if data:
            ticker_string = make_ticker_string(data['matches'])
            update_sidebar(ticker_string)
    except Exception:
        pass

    time.sleep(10*60)
