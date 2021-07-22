SHELL=/usr/bin/bash

all: update start

app:
	@nohup python -m app -O [StudCabBot] &

debug:
	@python -m app [StudCabBot] [DEBUG]

start: app

update: install
	@pybabel compile -f -d locales -D bot

install:
	@pip install -r requirements.txt

.PHONY: all app start update install
