import requests
import praw
import re
from config import data as config
from config import flairdata
from string import Template
import time

matchTemplate = Template('>[](${link})\n>###${event}\n>###${time}\n>###${team1}\n>###${team2}\n>###${flair1}\n>###${flair2}\n\n[](#separator)\n\n')

def getData():
	try:
		data = requests.get(config['config']['overggupcoming'],  headers = {"User-Agent": 'r/competitiveoverwatch sidebar match ticker'})
		data.raise_for_status()
		data = data.json()
		return data
	except:
		return None
		
		
def findFlairByName(teamname):
	for key, flair in flairdata['flairs'].items():
		if flair['name'].lower() == teamname.lower():
			return '[](#teams-c' + flair['col'] + '-r' + flair['row'] + ')'
	return '[](#noflair)'
		
		
def makeTime(timestamp):
	currentTime = time.time()
	if currentTime > timestamp:
		return '-'
	timeDiff = timestamp - currentTime
	
	m, s = divmod(timeDiff, 60)
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

	
def makeMatchString(matchItem):
	time = makeTime(int(matchItem['timestamp']))
	if not time:
		return None

	mapping = dict()
	mapping['link'] = matchItem['match_link']
	mapping['event'] = matchItem['event_name']
	mapping['time'] = time
	mapping['team1'] = matchItem['teams'][0]['name']
	mapping['team2'] = matchItem['teams'][1]['name']
	mapping['flair1'] = findFlairByName(mapping['team1'])
	mapping['flair2'] = findFlairByName(mapping['team2'])
	
	matchString = matchTemplate.substitute(mapping)
	return matchString
	
def makeTickerString(matchData):
	tickerString = ''
	for index, matchItem in enumerate(matchData):
		matchString = makeMatchString(matchItem)
		if not matchString:
			continue
		tickerString += matchString
		if index == 5:
			break
	return tickerString
	
def updateSidebar(tickerString):
	redditPraw = praw.Reddit(client_id=config['creds']['redditBotClientId'], client_secret=config['creds']['redditBotClientSecret'], redirect_uri=config['creds']['redditBotRedirectURI'], user_agent='rankification by u/jawoll', username = config['creds']['redditBotUserName'], password = config['creds']['redditBotPassword'])
	subreddit = redditPraw.subreddit(config['config']['subreddit'])
	settings = subreddit.mod.settings()
	sidebar = settings['description']
	
	sidebar = re.sub('(\[\]\(#mtstart\)\n)(.*)(\[\]\(#mtend\))',r'\1' + tickerString + r'\3',sidebar,flags=re.M|re.DOTALL)
	
	subreddit.mod.update(description=sidebar)
	
def main():
	while True:
		data = getData()
		if data:
			tickerString = makeTickerString(data['matches'])
			updateSidebar(tickerString)
	
		time.sleep(10*60)
main()