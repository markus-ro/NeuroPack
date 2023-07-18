upload: setup.py
		python setup.py sdist
		twine upload dist/*
		rm -rf dist
		rm -rf MANIFEST

clean:
	rm -rf **/*.pyc
	rm -rf **/__pycache__
	rm -rf **/*.egg-info
	rm -rf dist