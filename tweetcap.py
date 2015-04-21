import tempfile, subprocess, re, cgi, os, dateutil.parser, dateutil.tz

def tweetcap(template_path, tweet_name, tweet_handle, tweet_avatar, tweet_html, tweet_date):
	tweet_name = cgi.escape(tweet_name)
	tweet_handle = cgi.escape(tweet_handle)
	tweet_date = tweet_date.astimezone(dateutil.tz.tzutc()).strftime('%-I:%M %p - %-d %b %Y')

	with open(template_path, 'r') as template:
		html = template.read()

	html = html\
	.replace('TWEET_NAME', tweet_name)\
	.replace('TWEET_HANDLE', tweet_handle)\
	.replace('TWEET_AVATAR', tweet_avatar)\
	.replace('TWEET_HTML', tweet_html)\
	.replace('TWEET_DATE', tweet_date)

	temp = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False)
	temp.write(html.encode('ascii', 'xmlcharrefreplace'))
	temp.close()

	image = tempfile.NamedTemporaryFile(mode='w', suffix='.png', delete=False)
	image.close()

	subprocess.check_call(['wkhtmltoimage', '-f', 'png', '--width', '660', temp.name, image.name])

	os.remove(temp.name)

	return image.name