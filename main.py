from flask import Flask
from backend.blueprints import index, authentication, community, session_manager
from backend.models import db
from random import choice
from string import ascii_letters, digits
import sys

def create_app(dbname=None):
    if not dbname:
        dbname = "development.db"
    app = Flask(__name__)
    # Blue prints
    app.register_blueprint(session_manager.bp)
    app.register_blueprint(index.bp)
    app.register_blueprint(authentication.bp)
    app.register_blueprint(community.bp)
    # SQL stuff
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///{}".format(dbname) # Test database for now
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # Initialize database session
    db.init_app(app)
    # Fixed endpoint for /
    app.add_url_rule("/", endpoint="index")
    app.add_url_rule("/community", endpoint="community")
    # FIXME: change the secret key!
    app.secret_key = "".join([choice(ascii_letters + digits) for c in range(128)])
    return app

# FIXME: this is a horrible way to initialize the database
# remove this once the application becomes more mature and stable
if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "init-dev-db":
        # Create the development database
        app = create_app()
        app.app_context().push()
        db.drop_all()
        db.create_all(app=app)
