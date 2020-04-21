from backend.models import User, Community, Post, PostVote, db
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

# Karma
def upvote(user_id, post_id):
    # user_id is the voter.
    # we need it to associate the vote with a user so that users
    # won't be able to just upvote or downvote the post infinitely.
    post = Post.query.filter(Post.id == post_id).first()
    user = User.query.filter(User.id == user_id).first()
    vote = PostVote(user_id=user_id, post_id=post_id, vote_type=True) # True == +1
    # Add the vote to the user's post votes list
    user.post_votes.append(vote)
    post.votes.append(vote)
    # Increase the post karma and save changes
    post.karma += 1
    db.session.add(vote)
    db.session.commit()

def downvote(user_id, post_id):
    post = Post.query.filter(Post.id == post_id).first()
    user = User.query.filter(User.id == user_id).first()
    vote = PostVote(user_id=user_id, post_id=post_id, vote_type=False) # -1
    user.post_votes.append(vote)
    post.votes.append(vote)
    post.karma -= 1
    db.session.add(vote)
    db.session.commit()

def unvote(user_id, post_id):
    # Remove the relationship between the post karma and the user,
    # and reset the count according to the karma type it was (upvote or downvote)
    vote = PostVote.query.filter(PostVote.user_id == user_id, PostVote.post_id == post_id).first()
    post = vote.post
    if vote.vote_type:
        # True vote_type means we need to decrease the post's karma in this case
        # because the user removed their upvote
        post.karma -= 1
    else:
        # False means we need to increase the karma because the user removed their downvote
        post.karma += 1
    # Remove the vote object altogether
    db.session.delete(vote)
    db.session.commit()
