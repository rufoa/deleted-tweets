## deleted-tweets

this is a twitter bot that monitors specific twitter account(s) and tweets screenshots of any messages which they subsequently delete

### dependencies

these are the debian package names, other distros may vary

- wkhtmltopdf
    - needs an X server - `xvfb-run` may be useful on headless servers
- python-twython
- python-dateutil
- python-sqlite
- python-requests
- python-requests-oauthlib
- python-pystache
- python-pil

### initial setup

- create a new twitter app with write permission
- run `./watch.py init`
- enter consumer key and secret
- go to the url provided and log in to twitter
- enter the pin shown in your web browser
- enter list of users to track, separated by whitespace or commas

## use

- run `./watch.py` without any arguments
- you'll probably want to use something like `runit` for process supervision

## configuration

- by default the sqlite database is called `tweets.db` and the template is called `template.html`, located in the same directory as the python script
- these paths can be overridden using the `DB` and `TEMPLATE` environmental variables, respectively
    - e.g. `DB=~/bot1.db ./watch.py init`
    - and `DB=~/bot1.db TEMPLATE=~/bot1.html ./watch.py`
- this allows you to run multiple accounts using one copy of this code