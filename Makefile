.PHONY: install prepare status agreement finalize run test notebooks

install:
	python -m pip install -r requirements-lock.txt
	python -m pip install -e .

prepare:
	python -m phasma_review.cli prepare-annotations

status:
	python -m phasma_review.cli status

agreement:
	python -m phasma_review.cli build-adjudication

finalize:
	python -m phasma_review.cli finalize-labels

run:
	python -m phasma_review.cli run-all

test:
	python -m pytest

notebooks:
	python scripts/build_notebooks.py