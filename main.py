'''
nix-shell -p git python312 python312Packages.flask python312Packages.pyyaml

git clone https://github.com/denballakh/olymp.git
cd olymp

git pull
python3.12 -m flask --app main run --host 0.0.0.0 --port 5555

python3.12 -m flask --app main --debug run
'''

from __future__ import annotations
import sys
from pathlib import Path
import gzip
import json
import functools

from flask import Flask, jsonify, render_template, make_response

from event import load, Event

dir_this = Path(__file__).parent
dir_events = dir_this / 'events'
dir_templates = dir_this / 'templates'


DEBUG = '--debug' in sys.argv

app = Flask(__name__)


@(lambda x: x) if DEBUG else functools.cache
def load_data():
    return load(dir_events)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/data.json')
def get_data():
    content = []
    for id, e in load_data().items():
        try:
            content += [e.display()]
        except Exception:
            import traceback

            print(f'Failed to display {id}:')
            traceback.print_exc()
    content = gzip.compress(json.dumps(content).encode('utf8'), 5)
    response = make_response(content)
    response.headers['Content-Length'] = str(len(content))
    response.headers['Content-Encoding'] = 'gzip'
    return response


@app.route('/columns')
def get_columns():
    return jsonify(Event.table_columns)


@app.route('/raw.json')
def get_raw():
    response = make_response(
        json.dumps(
            {e.id: e.dump() for _, e in load_data().items()},
            indent=2,
            ensure_ascii=False,
        )
    )
    response.headers['Content-Type'] = 'application/json'
    return response


DEBUG = '--debug' in sys.argv

if __name__ == '__main__':
    app.run(
        host='localhost' if DEBUG else '0.0.0.0',
        port=5000 if DEBUG else 5001,
        debug=DEBUG,
    )
