from flask import Blueprint, g, session, request, url_for, redirect, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from ..models import db, Post, User
from flask import jsonify

# This should generate the index template
# grab all the highest rated latest posts from various communities

bp = Blueprint("index", __name__)

@bp.route("/")
def index():
    posts = []
    communities = []
    if g.user:
        communities = g.user.communities
    return render_template("index.html", posts=posts, communities=communities)

@bp.route("/search", methods=("GET",))
def search():
    pattern = request.args.get("value")
    print("Search called with: {}".format(pattern))
    return redirect(url_for("index"))
