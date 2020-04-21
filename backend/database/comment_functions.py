# Comment handling functions
# Not Python comments ;)

from backend.models import User, Community, Post, Comment, db
from sqlalchemy.orm import exc as orm_exc

# FIXME: the function will still create a comment even if the user_id doesn't exist in the database
def create_comment(user_id, post_id, text):
    # Create a comment and add it to the post
    user_obj = User.query.filter(User.id == user_id).first()
    post_obj = Post.query.filter(Post.id == post_id).first()
    community = post_obj.community # Raises AttributeError if post_obj is None
    # Permission checks
    if user_obj is None:
        raise ValueError("user doesn't exist")
    if user_obj in community.banned_users:
        # User is banned from the community and is therefore not allowed to comment
        raise PermissionError("user {} is banned in community {}".format(user_obj, community))
    # Locked post check
    if post_obj.is_locked:
        # FIXME: owners, admins, and mods should still be able to comment on locked posts
        raise PermissionError("post {} is locked".format(post_obj))
    # Privacy setting checks - in practice, the user shouldn't even be able to see
    # the thread at all if the community is set to private.
    # But, until we implement the verification in a different layer of the request processing,
    # we will verify it here, for now.
    if community.is_private and user_obj not in community.users:
        raise PermissionError("community {} is private".format(community))
    # Checks passed, let's create the post.
    comment = Comment(user_id=user_id, post_id=post_id, text=text)
    db.session.add(comment)
    try:
        db.session.commit()
    except exc.IntegrityError:
        # some field in the comment object is None
        db.session.rollback()
        raise

# NOTE: this function should only be callable by the user who is the author of the comment
# or mods/admins/owners in the community
def delete_comment(comment_id):
    # Delete a comment
    comment_obj = Comment.query.filter(Comment.id == comment_id).first()
    # Err...
    db.session.delete(comment_obj)
    try:
        db.session.commit()
    except orm_exc.UnmappedInstanceError:
        # Comment object is None
        db.session.rollback()
        raise

# Karma
def upvote(user_id, comment_id):
    # user_id is the voter.
    # we need it to associate the vote with a user so that users
    # won't be able to just upvote or downvote the post infinitely.
    comment = Comment.query.filter(Comment.id == comment_id).first()
    user = User.query.filter(User.id == user_id).first()
    vote = CommentVote(user_id=user_id, comment_id=comment_id, vote_type=True) # True == +1
    # Add the vote to the user's comment votes list
    user.comment_votes.append(vote)
    comment.votes.append(vote)
    # Increase the post karma and save changes
    comment.karma += 1
    db.session.add(vote)
    db.session.commit()

def downvote(user_id, post_id):
    comment = Comment.query.filter(Comment.id == post_id).first()
    user = User.query.filter(User.id == user_id).first()
    vote = CommentKarma(user_id=user_id, comment_id=comment_id, vote_type=False) # -1
    user.comment_votes.append(karma)
    comment.votes.append(vote)
    comment.karma -= 1
    db.session.add(vote)
    db.session.commit()

def unvote(user_id, comment_id):
    # Remove the relationship between the post karma and the user,
    # and reset the count according to the karma type it was (upvote or downvote)
    vote = CommentVote.query.fiter(_and(CommentVote.user_id == user_id, CommentVote.comment_id == comment_id)).first()
    user.comment_votes.remove(vote)
    comment.votes.remove(comment)
    if vote.vote_type:
        # True vote_type means we need to decrease the comment's karma in this case
        # because the user removed their upvote
        comment.karma -= 1
    else:
        # False means we need to increase the karma because the user removed their downvote
        comment.karma += 1
    # Remove the vote object altogether
    db.session.delete(vote)
    db.session.commit()
