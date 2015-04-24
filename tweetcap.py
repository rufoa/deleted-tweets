import tempfile, subprocess, re, cgi, os, dateutil.parser, dateutil.tz, pystache
from PIL import Image, ImageChops, ImageDraw

def trim(path, margin):
	image = Image.open(path).convert('RGB')
	colour = image.getpixel((0,0))
	background = Image.new('RGB', image.size, colour)
	diff = ImageChops.difference(image, background)
	l,t,r,b = diff.getbbox()
	w = r - l
	h = b - t
	bbox = (l - margin, t - margin, r + margin, b + margin)
	image = image.crop(bbox)
	draw = ImageDraw.Draw(image)
	draw.rectangle([0, 0, w+2*margin-1, margin-1], fill=colour)
	draw.rectangle([0, margin, margin-1, h+margin-1], fill=colour)
	draw.rectangle([w+margin, margin, w+2*margin-1, h+margin-1], fill=colour)
	draw.rectangle([0, h+margin, w+2*margin-1, h+2*margin-1], fill=colour)
	del draw
	image.save(path)

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

	subprocess.check_call(['wkhtmltoimage', '-f', 'png', temp.name, image.name])
	os.remove(temp.name)
	trim(image.name, 5)
	return image.name