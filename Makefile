venv: venv/touchfile

.PHONY: virtualenv
virtualenv:
	pip3 install virtualenv

venv/touchfile: requirements.txt
	test -d venv || virtualenv venv
	. venv/bin/activate; pip install -Ur requirements.txt
	touch venv/touchfile

local: venv virtualenv
	. venv/bin/activate && (\
		cd baryon; \
		python manage.py runserver \
	)

test-types: venv virtualenv
	. venv/bin/activate && (\
		cd baryon; \
		mypy . \
	)

deploy-prod:
	docker compose stop
	docker compose build
	docker compose up -d
