from backend.models import User, Community, Post, db
from sqlalchemy import exc
from sqlalchemy.orm import exc as orm_exc

# FIXME: shitload of verifications in this one, just trust data instead?
def create_post(user_id, community_id, post_title, post_body):
    # This function can only be called when user is logged in
    # So the user id must be a valid one because it's derived from the session handler
    # input: (int, int, str, str)
    # Create a new post
    community = Community.query.filter(Community.id == community_id).first()
    user_obj = User.query.filter(User.id == user_id).first()
    if user_obj is None:
        raise ValueError("user doesn't exist")
    if community is None:
        raise ValueError("community doesn't exist")

    if user_obj in community.banned_users:
        raise PermissionError("user {} is banned on {}".format(user_obj, community))
    if community.is_private and user_obj not in community.users:
        raise PermissionError("community {} is private".format(community))
    # Create it now
    post_obj = Post(user_id=user_id, community_id=community_id, title=post_title, body=post_body)
    db.session.add(post_obj)
    try:
        db.session.commit()
    except (exc.IntegrityError, exc.InterfaceError): 
        # if the title or body is None, IntegrityError
        db.session.rollback()
        raise

def delete_post(post_id):
    # This should not be called by users with no special permissions on the group
    # exc.InterfaceError if post_id is some not-None, not-string, not-int object
    post = Post.query.filter(Post.id == post_id).first()
    try:
        db.session.delete(post)
        db.session.commit()
    except orm_exc.UnmappedInstanceError:
        # post is None
        db.session.rollback()
        raise
# TODO: edit_post(post_id, title, body)
