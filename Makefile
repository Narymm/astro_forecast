install:
		pip install poetry && \
		poetry install

start:
		poetry run python astro_forecast/forecast.py