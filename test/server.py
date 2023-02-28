# app.py

from flask import Flask
from plugins.github import github_bp

app = Flask(__name__)

app.register_blueprint(github_bp)

@app.route("/", methods=["GET"])
def working():
    return "baka"

app.run(host='0.0.0.0', port=8000)