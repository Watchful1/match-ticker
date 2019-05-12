import requests
import praw
import re
from string import Template
import time
import logging.handlers
import os
import json
import sys
import traceback
import configparser

matchTemplate = Template('>[](${link})\n>###${event}\n>###${time}\n>###${team1}\n>###${team2}\n>###${flair1}\n>###${flair2}\n\n[](#separator)\n\n')
overggupcoming = "https://api.over.gg/matches/upcoming"
FLAIR_LIST = "http://rcompetitiveoverwatch.com/static/flairs.json"
SUBREDDIT = "Competitiveoverwatch"
USER_AGENT = "Sidebar ticker (u/Watchful1)"
LOG_LEVEL = logging.INFO


LOG_FOLDER_NAME = "logs"
if not os.path.exists(LOG_FOLDER_NAME):
    os.makedirs(LOG_FOLDER_NAME)
LOG_FILENAME = LOG_FOLDER_NAME+"/"+"bot.log"
LOG_FILE_BACKUPCOUNT = 5
LOG_FILE_MAXSIZE = 1024 * 1024 * 16

log = logging.getLogger("bot")
log.setLevel(LOG_LEVEL)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
log_stderrHandler = logging.StreamHandler()
log_stderrHandler.setFormatter(log_formatter)
log.addHandler(log_stderrHandler)
if LOG_FILENAME is not None:
    log_fileHandler = logging.handlers.RotatingFileHandler(
        LOG_FILENAME,
        maxBytes=LOG_FILE_MAXSIZE,
        backupCount=LOG_FILE_BACKUPCOUNT)
    log_fileHandler.setFormatter(log_formatter)
    log.addHandler(log_fileHandler)

once = False
user = None
if len(sys.argv) >= 2:
    user = sys.argv[1]
    for arg in sys.argv:
        if arg == 'once':
            once = True
        elif arg == 'debug':
            log.setLevel(logging.DEBUG)
else:
    log.error("No user specified, aborting")
    sys.exit(0)

try:
    r = praw.Reddit(
        user,
        user_agent=USER_AGENT)
except configparser.NoSectionError:
    log.error("User "+user+" not in praw.ini, aborting")
    sys.exit(0)

try:
    response = requests.get(url=FLAIR_LIST, headers={'User-Agent': USER_AGENT})
    with open("flairs.json", 'w') as raw_flair_data:
        raw_flair_data.write(response.text)
except Exception as err:
    log.warning("Flair load request failed")

with open("flairs.json", 'r') as raw_flair_data:
    flair_data = json.load(raw_flair_data)


def find_flair_by_name(team_name):
    team_name = ''.join(x for x in team_name.lower() if x.isalnum())
    for key, flair in flair_data['flairs'].items():
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


while True:
    try:
        log.debug("Starting run")
        result_data = requests.get(overggupcoming, headers={"User-Agent": USER_AGENT})
        result_data.raise_for_status()
        data = result_data.json()

        ticker_string = ''
        count = 0
        for match_item in data['matches']:
            log.debug(f"Match: {match_item['teams'][0]['name']} vs {match_item['teams'][1]['name']}")
            match_string = make_match_string(match_item)
            if not match_string:
                continue
            ticker_string += match_string
            count += 1
            if count == 5:
                break

        sub = r.subreddit(SUBREDDIT)
        settings = sub.mod.settings()
        sidebar = settings['description']

        sidebar = re.sub(r"(\[\]\(#mtstart\)\n)(.*)(\[\]\(#mtend\))", r"\1" + ticker_string + r"\3", sidebar, flags=re.M | re.DOTALL)

        sub.mod.update(description=sidebar)
        log.debug("Run complete")
    except Exception as err:
        log.warning("Hit an error in main loop")
        log.warning(traceback.format_exc())

    if once:
        break

    time.sleep(10*60)
