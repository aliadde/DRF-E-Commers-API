# run server on development localhost:8000
runserver:
    uv run python src/manage.py runserver 

# clean the environment from chache files and folders
cleaner *args:
    uv run python src/scripts/cleaner.py {{args}}

# format ruff
format file='.':
    uv run ruff format {{file}}

# python manage.py
mange *args:
    uv run python src/manage.py {{args}}

# make migrations
makemigration:
    uv run python src/manage.py makemigrations

# migrate
migrate:
    uv run python src/manage.py migrate

# uv run python src/manage.py shell
django-shell:
    uv run python src/manage.py shell

# run pytest 
pytest *args:
    uv run pytest {{args}}
