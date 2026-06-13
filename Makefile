PYTHON=python

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

test:
	pytest -q

lint:
	@echo "No linter configured. Install flake8 or similar."

package:
	$(PYTHON) -m pip install -e .
