import tempfile, subprocess, re, cgi, os, dateutil.parser, dateutil.tz, pystache

def tweetcap(template_path, tweet_name, tweet_handle, tweet_avatar, tweet_html, tweet_date):
	tweet_date = tweet_date.astimezone(dateutil.tz.tzutc()).strftime('%-I:%M %p - %-d %b %Y')

	values = {'name': tweet_name, 'handle': tweet_handle, 'avatar': tweet_avatar, 'tweet_html': tweet_html, 'date': tweet_date}

	with open(template_path, 'r') as template:
		html = template.read()

	html = pystache.render(html, values)

	temp = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False)
	temp.write(html.encode('ascii', 'xmlcharrefreplace'))
	temp.close()

	image = tempfile.NamedTemporaryFile(mode='w', suffix='.png', delete=False)
	image.close()

	subprocess.check_call(['wkhtmltoimage', '-f', 'png', '--width', '660', temp.name, image.name])

	os.remove(temp.name)

	return image.name