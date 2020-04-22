# Our session manager.
# I implemented this so that we won't have to store the user ID
# in the session cookie.
from flask import Blueprint
from string import ascii_letters, digits
from random import choice
from datetime import timedelta
from backend.token_expiration_manager import TokenExpirationManager

bp = Blueprint("session_manager", __name__)

# Tokens and sessions will expire after approximately 2 hours, give or take 10 minutes.
session_manager = TokenExpirationManager(session_timeout=timedelta(hours=2), expiration_proximity=timedelta(minutes=10))

def generate_random_tag(length=128):
    # Generates a random session tag (ID)
    characters = ascii_letters + digits + "_" # url safe shit
    tag = "".join([choice(characters) for c in range(length)])
    return tag

# Session object
class Session:
    def __init__(self, user_id):
        self.session_id = generate_random_tag()
        self.user_id = user_id
    def __repr__(self):
        return "<Session {}>".format(self.session_id)

# Call this before processing each request, to remove any expired sessions
@bp.before_app_request
def purge_expired():
   session_manager.purge_expired_tokens()
