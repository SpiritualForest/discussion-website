from backend.models import User, Community, db
from main import create_app

def setup_test_environment():
    app = create_app("test/database.db")
    app.app_context().push()
    db.drop_all()
    db.create_all()

def create_test_user():
    user = User(username="shit", password="fuckoff", salt="testsalt")
    db.session.add(user)
    db.session.commit()
    return user

def create_test_community():
    name = "TestCommunity"
    com = Community(name=name, description="A test community")
    db.session.add(com)
    db.session.commit()
    return com

def cleanup(*models):
    # Execute <model>.query.delete() on all the given models
    # Used to clean out the database without having to drop all the tables
    for model in models:
        model.query.delete()
    db.session.commit()
