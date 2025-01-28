# scp -r -i %USERPROFILE%/.ssh/vdsina D:/Github/olymp root@89.110.80.181:/root/
# cat /var/log/nginx.denball.xyz.access_log | grep -v 5.35.38.201 | more

# nix-shell -p python312 python312Packages.flask python312Packages.pyyaml
# python3.12 main.py

from __future__ import annotations
import sys
from pathlib import Path
import gzip
import json

from event import load, Event

DEBUG = sys.platform == 'win32'

data = load(Path() / 'events')

from flask import Flask, jsonify, render_template_string, make_response

app = Flask(__name__)


@app.route('/')
def index():
    return render_template_string((Path() / 'index.html').read_text())


@app.route('/data.json')
def get_data():
    text = [e.display() for _, e in data.items()]
    # return jsonify(text)
    content = gzip.compress(json.dumps(text).encode('utf8'), 5)
    response = make_response(content)
    response.headers['Content-Length'] = str(len(content))
    response.headers['Content-Encoding'] = 'gzip'
    return response


@app.route('/columns')
def get_columns():
    return jsonify(Event.table_columns)


@app.route('/raw.json')
def get_raw():
    response = make_response(json.dumps(
        {e.id: e.dump() for _, e in data.items()},
        indent=2,
        ensure_ascii=False,
    ))
    response.headers['Content-Type'] = 'application/json'
    return response


if __name__ == '__main__':
    app.run(debug=True)
