if ! [ -d "venv" ]; then
	python3 -m venv venv
fi

source venv/bin/activate

if [[ "$(pip freeze)" != *"requests"* ]]; then
	pip install requests
fi

if [[ "$(pip freeze)" != *"Flask"* ]]; then
	pip install Flask
fi

python ./main.py
