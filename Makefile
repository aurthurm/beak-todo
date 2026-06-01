.PHONY: build-ui run test

build-ui:
	beak-flow build-ui

run: build-ui
	beak-flow run

test:
	pytest -q
