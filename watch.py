#!/usr/bin/python

from tweetcap import tweetcap
from datetime import datetime
import dateutil.tz, sqlite3, sys, json, os, re
from twython import Twython, TwythonStreamer
from twython.exceptions import TwythonAuthError

def nice_interval(count):
	if count == 1:
		unit = 'second'
	else:
		unit = 'seconds'
	units = [(60, 'minute', 'minutes'), (60, 'hour', 'hours'), (24, 'day', 'days'), (30, 'month', 'months'), (12, 'year', 'years')]
	for max, singular, plural in units:
		if count >= max:
			count /= max
			if count == 1:
				unit = singular
			else:
				unit = plural
		else:
			break
	return str(count) + ' ' + unit

def get_setting(name):
	global cur
	cur.execute("SELECT value FROM settings WHERE name = ?" , (name,))
	row = cur.fetchone()
	if row is None:
		return None
	else:
		return row[0]

class MyStreamer(TwythonStreamer):
	def on_success(self, data):
		global cur, rest, follow_ids

		if 'text' in data:
			if data['user']['id_str'] in follow_ids:
				data_json = json.dumps(data)
				cur.execute('INSERT OR IGNORE INTO tweets(id_str, json) VALUES (?,?)', (data['id_str'], data_json))
				print 'inserted ' + data['id_str']

		elif 'delete' in data:
			deleted_status = data['delete']['status']

			cur.execute('SELECT json FROM tweets WHERE id_str = ?', (deleted_status['id_str'],))
			row = cur.fetchone()
			if row is None:
				print deleted_status['id_str'] + ' not found in db'
			else:
				tweet = json.loads(row[0])
				elapsed = (int(data['delete']['timestamp_ms']) - int(tweet['timestamp_ms'])) / 1000
				status = 'deleted after ' + nice_interval(elapsed)
				if len(tweet['entities']['urls']) > 0:
					status += "\nlinks in original tweet:"
					for url in tweet['entities']['urls']:
						status += ' ' + url['expanded_url']
				image_path = tweetcap(\
					tweet['user']['name'],\
					tweet['user']['screen_name'],\
					tweet['user']['profile_image_url'],\
					Twython.html_for_tweet(tweet),\
					datetime.fromtimestamp(int(tweet['timestamp_ms']) / 1000).replace(tzinfo=dateutil.tz.tzutc()))
				image = open(image_path, 'rb')
				rest.update_status_with_media(status=status, media=image)
				image.close()
				os.remove(image_path)

	def on_error(self, status_code, data):
		if status_code == 420:
			print 'hit ratelimit, disconnecting'
			self.disconnect()

db_path_default = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tweets.db')
db_path = os.getenv('DB', db_path_default)

con = sqlite3.connect(db_path, isolation_level=None)
with con:
	cur = con.cursor()

	if len(sys.argv) == 2 and sys.argv[1] == 'init':

		consumer_key_old = get_setting('consumer_key')
		prompt = 'Enter consumer key'
		if consumer_key_old:
			prompt += ' [' + consumer_key_old + ']'
		consumer_key = raw_input(prompt + ': ')
		if consumer_key == '':
			if consumer_key_old:
				consumer_key = consumer_key_old
			else:
				print "No consumer key provided"
				exit(1)

		consumer_secret_old = get_setting('consumer_secret')
		prompt = 'Enter consumer secret'
		if consumer_secret_old:
			prompt += ' [' + consumer_secret_old + ']'
		consumer_secret = raw_input(prompt + ': ')
		if consumer_secret == '':
			if consumer_secret_old:
				consumer_secret = consumer_secret_old
			else:
				print "No consumer secret provided"
				exit(1)

		rest = Twython(consumer_key, consumer_secret)

		try:
			auth = rest.get_authentication_tokens()
		except TwythonAuthError:
			print "Bad API keys"
			exit(1)

		access_token_old = get_setting('access_token')
		access_token_secret_old = get_setting('access_token_secret')

		if access_token_old is not None and access_token_secret_old is not None:
			keep = raw_input('Use saved access token? [Y/n]: ')
			keep = not (keep == 'n' or keep == 'N')
		else:
			keep = False

		if keep:
			access_token = access_token_old
			access_token_secret = access_token_secret_old
		else:
			print "\nGo to this URL and log in:\n" + auth['auth_url'] + "\n"
			rest = Twython(consumer_key, consumer_secret, auth['oauth_token'], auth['oauth_token_secret'])
			pin = raw_input('Enter PIN code: ')

			try:
				tokens = rest.get_authorized_tokens(pin)
				access_token = tokens['oauth_token']
				access_token_secret = tokens['oauth_token_secret']
			except TwythonAuthError:
				print "Invalid or expired PIN"
				exit(1)

		rest = Twython(consumer_key, consumer_secret, access_token, access_token_secret)

		follow = raw_input('List of twitter accounts to follow: ')
		follow_list = []
		for account in re.split('[\s,]+', follow):
			if account.isdigit():
				user = rest.show_user(user_id=account)
			else:
				if account[0] == '@':
					account = account[1:]
				user = rest.show_user(screen_name=account)
			if 'id_str' in user:
				print "@" + user['screen_name'] + " (user ID " + user['id_str'] + ") found"
				follow_list.append(user['id_str'])
			else:
				print account + " not found, aborting"
				exit(1)
		follow_ids = ','.join(follow_list)

		cur.execute('CREATE TABLE IF NOT EXISTS settings(name TEXT PRIMARY KEY, value TEXT)')

		values = [('consumer_key', consumer_key), ('consumer_secret', consumer_secret), ('access_token', access_token), ('access_token_secret', access_token_secret), ('follow', follow_ids)]
		cur.executemany('INSERT OR REPLACE INTO settings(name, value) VALUES (?,?)', values)

		cur.execute('DROP TABLE IF EXISTS tweets')
		cur.execute('CREATE TABLE tweets(id_str TEXT PRIMARY KEY, json TEXT)')

		for user_id in follow_list:
			print "Backfilling user ID " + user_id
			tweets = rest.get_user_timeline(user_id=user_id, count=200)
			count = 1
			for tweet in tweets:
				if 'text' in tweet and tweet['user']['id_str'] == user_id:
					tweet_json = json.dumps(tweet)
					cur.execute('INSERT OR IGNORE INTO tweets(id_str, json) VALUES (?,?)', (tweet['id_str'], tweet_json))
					print "\r" + str(count) + '/' + str(len(tweets)),
					sys.stdout.flush()
					count += 1
			print "\n"

		print "\nDone"

	else:

		consumer_key = get_setting('consumer_key')
		consumer_secret = get_setting('consumer_secret')
		access_token = get_setting('access_token')
		access_token_secret = get_setting('access_token_secret')
		
		follow_ids = get_setting('follow').split(',')

		print "Following user IDs: " + ', '.join(follow_ids)

		rest = Twython(consumer_key, consumer_secret, access_token, access_token_secret)
		streaming = MyStreamer(consumer_key, consumer_secret, access_token, access_token_secret)
		streaming.statuses.filter(follow=','.join(follow_ids))