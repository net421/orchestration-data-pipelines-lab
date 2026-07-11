.PHONY: install generate run scenarios test verify clean-generated clean

install:
	python -m pip install -r requirements.txt
	python -m pip install -e .

generate:
	python data/generate_synthetic_data.py

run: generate
	python -m analytics_pipeline.cli --input-dir data/raw --output-dir data/published --run-dir runs

scenarios:
	python validation/run_scenarios.py

test:
	python -m pytest -q

verify: clean-generated generate scenarios test

clean-generated:
	rm -rf validation/generated .pytest_cache
	rm -f data/raw/*.csv

clean: clean-generated
	rm -rf data/published/*.csv runs/*
	touch data/raw/.gitkeep data/published/.gitkeep runs/.gitkeep
