# This stuff deals with user registration and authentication
from flask import Blueprint, session, redirect, url_for, render_template, request, g
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email
from backend.database import user_functions
from backend.blueprints.session_manager import Session, session_manager
from sqlalchemy import exc # For various database exceptions

bp = Blueprint("auth", __name__)

class UserRegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    password_confirm = PasswordField("Confirm password", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Register")

class UserLoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")

@bp.route("/register", methods=("GET", "POST"))
def register():
    form = UserRegistrationForm()
    if request.method == "GET":
        # display the registration template
        return render_template("auth/register.html", form=form)

    # POST request here
    if not form.validate_on_submit():
        # FIXME: actually do something meaningful here
        return render_template("error.html", "Form not valid")
    # If execution reached here, the request is valid, let's register
    try:
        # Register the user
        username = form.username.data
        password = form.password.data
        email = form.email.data
        user_functions.register_user(username, password, email)
    except ValueError:
        # Username or password is an empty string
        return render_template("error.html", error_message="Username or password is empty")
    except TypeError:
        # This should never even occur, but the function raises this exception,
        # so we have to catch it
        return render_template("error.html", error_message="Password error")
    except exc.IntegrityError:
        # Will occur if one of the fields is not unique (exists in the database)
        # FIXME: REST API and shit for this crap, making it possible to see the error
        # in real time on the web browser, rather than only after the request.
        return render_template("error.html", error_message="Username or email already exists")
    # If execution reached here, the registration was successful
    # Create a session for the user and redirect them to the index page
    user_obj = user_functions.get_user_by_name(username)
    session_obj = Session(user_obj.id)
    session["session_id"] = session_obj.session_id
    session_manager.add_token(session_obj.session_id, session_obj)
    return redirect(url_for("index"))

@bp.route("/login", methods=("GET", "POST"))
def login():
    form = UserLoginForm()
    if request.method == "GET":
        return render_template("auth/login.html", form=form)

    if not form.validate_on_submit():
        return render_template("error.html", error_message="Form not valid")
    
    try:
        username, password = form.username.data, form.password.data
        verified = user_functions.verify_user(username, password)
    except (AttributeError, TypeError):
        # Verification failed due an error
        return render_template("error.html", error_message="Verification failed")
    if verified:
        # Success. Create the session cookie and all that shit
        user_obj = user_functions.get_user_by_name(username)
        session_obj = Session(user_obj.id)
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
        user = user_functions.get_user_by_id(session_object.user_id)
        g.user = user # None if not found
