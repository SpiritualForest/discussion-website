# This stuff deals with user registration and authentication
from flask import Blueprint, session, redirect, url_for, render_template, request, g
from werkzeug.security import generate_password_hash, check_password_hash
from random import choice # for salt creation
from string import ascii_letters, punctuation, digits # for salt
from backend.models import User, db
from backend.blueprints.session_manager import Session, CSRFToken, session_manager, csrf_manager

bp = Blueprint("auth", __name__)

# TODO: make a REST API for some database functions
# so that we can use jQuery or some other library
# to query the database and check for stuff like
# whether a username is already taken, an email has already been registered with another user,
# and so forth.
# Make the HTML form unsubmitable in case the required
# criteria for registration (unique username, unique email, etc) are not met.

@bp.route("/register", methods=("GET", "POST"))
def register():
    # TODO: more error checks, and do something to inform the user when an error occurs
    if request.method == "GET":
        # display the registration template
        return render_template("auth/register.html")

    # POST request here
    username = request.form["username"]
    password = request.form["password"]
    email = request.form["email"]
    if not username or not password or not email:
        # Error
        # TODO: some notification to the user
        return redirect(url_for("index"))
    userObj = User.query.filter(User.username == username).first()
    if userObj:
        # Username already exists
        return render_template("error.html", error_message="Username already exists in the database")
    
    # Proceed to register
    success = add_user(username, password, email)
    if not success:
        return render_template("error.html", error_message="An error occurred when trying to register")
    
    # Registration succeeded. 
    # Create a session for the user and redirect them to the index page
    session_obj = Session(userObj.id)
    session["session_id"] = session_obj.session_id
    session_manager.add_token(sesson_obj.session_id, session_obj)
    return redirect(url_for("index"))

@bp.route("/login", methods=("GET", "POST"))
def login():
    # TODO: more error checking
    if request.method == "GET":
        return render_template("auth/login.html")

    username = request.form["username"]
    password = request.form["password"]

    userObj = User.query.filter(User.username == username).first()
    if not userObj:
        # Not found
        # TODO: display some error
        return redirect(url_for("index"))
    if check_password_hash(userObj.password, password + userObj.salt):
        # Success. Create the session cookie and all that shit
        session_obj = Session(userObj.id)
        session["session_id"] = session_obj.session_id
        session_manager.add_token(session_obj.session_id, session_obj)
    return redirect(url_for("index"))

@bp.route("/logout", methods=("GET",))
def logout():
    # Clear out the session
    session_manager.expire_token(session.get("session_id"))
    session.clear()
    g.user = None
    return redirect(url_for("index"))

@bp.before_app_request
def get_logged_in_user():
    # Get the logged in user based on the session ID
    session_id = session.get("session_id")
    session_object = session_manager.get_token_object(session_id)
    if session_object is None:
        g.user = None
    else:
        # an active session was found
        user = User.query(User.id == session_object.user_id).first()
        g.user = user # None if not found
