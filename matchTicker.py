import requests
import praw
import re
from config import data as config
from config import flair_data
from string import Template
import time

matchTemplate = Template('>[](${link})\n>###${event}\n>###${time}\n>###${team1}\n>###${team2}\n>###${flair1}\n>###${'
                         'flair2}\n\n[](#separator)\n\n')


def get_data():
    try:
        data = requests.get(config['config']['overggupcoming'],
                            headers={"User-Agent": 'r/competitiveoverwatch sidebar match ticker'})
        data.raise_for_status()
        data = data.json()
        return data
    except:
        return None


def find_flair_by_name(team_name):
    for key, flair in flair_data['flairs'].items():
        if flair['name'].lower() == team_name.lower():
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
    time_string = make_time(int(match_item['timestamp']))
    if not time_string:
        return None

    mapping = dict()
    mapping['link'] = match_item['match_link']
    mapping['event'] = match_item['event_name']
    mapping['time'] = time_string
    mapping['team1'] = match_item['teams'][0]['name']
    mapping['team2'] = match_item['teams'][1]['name']
    mapping['flair1'] = find_flair_by_name(mapping['team1'])
    mapping['flair2'] = find_flair_by_name(mapping['team2'])

    match_string = matchTemplate.substitute(mapping)
    return match_string


def make_ticker_string(match_data):
    ticker_string = ''
    for index, matchItem in enumerate(match_data):
        match_string = make_match_string(matchItem)

        if not match_string:
            continue

        ticker_string += match_string

        if index == 5:
            break

    return ticker_string


def update_sidebar(ticker_string):
    reddit_praw = praw.Reddit(client_id=config['creds']['redditBotClientId'],
                              client_secret=config['creds']['redditBotClientSecret'],
                              redirect_uri=config['creds']['redditBotRedirectURI'],
                              user_agent='rankification by u/jawoll', username=config['creds']['redditBotUserName'],
                              password=config['creds']['redditBotPassword'])
    subreddit = reddit_praw.subreddit(config['config']['subreddit'])
    settings = subreddit.mod.settings()
    sidebar = settings['description']

    sidebar = re.sub('(\[\]\(#mtstart\)\n)(.*)(\[\]\(#mtend\))', r'\1' + ticker_string + r'\3', sidebar,
                     flags=re.M | re.DOTALL)

    subreddit.mod.update(description=sidebar)


def main():
    while True:
        data = get_data()
        if data:
            ticker_string = make_ticker_string(data['matches'])
            update_sidebar(ticker_string)

        time.sleep(10 * 60)


main()
