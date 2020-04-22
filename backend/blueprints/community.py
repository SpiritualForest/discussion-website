from flask import Blueprint, g, session, redirect, url_for, render_template, request
from datetime import datetime, timedelta
from backend.blueprints.session_manager import session_manager
from backend.database import community_functions, user_functions

bp = Blueprint("community", __name__)

def get_recent_posts(community):
    # Get all the posts that were added to the community
    # within the last 24 hours
    timeLimit = datetime.utcnow() - timedelta(days=1)
    posts = Post.query.filter(Post.community_id == community.id and Post.post_time >= timeLimit).all()
    return posts

@bp.route("/community/create", methods=("GET", "POST"))
def create():
    if not g.user:
        # Login required
        return redirect(url_for('auth.login'))
    
    if request.method == "GET":
        return render_template("community/create.html")
    
    # Now it's a POST request to create the community
    name = request.form["community_name"] # Community name
    description = request.form["description"] # Description
    
    if not name or not description:
        # TODO: something more meaningful than this shit
        return redirect(url_for("community.create"))
    
    # Create the community
    success = createCommunity(name, description, g.user)
    if not success:
        # Some error occurred?
        return render_template("error.html", error_message="An error occurred when trying to create the community.")
    
    # All is fine, redirect to the community's index page
    return redirect(url_for("community.index", name=community.name))

@bp.route("/community/join", methods=("POST",))
def join():
    # A user joins the community
    if not g.user:
        return redirect(url_for('auth.login'))
    communityName = request.form["name"]
    if not communityName:
        # Error in the request
        return redirect(url_for("community"))
    # Get the community and create the relationship between the user and the community
    community = Community.query.filter(Community.name == communityName).first()
    if not community:
        # Community not found?
        return render_template("error.html", error_message="No such community")

    # Checks passed
    community.users.append(g.user)
    db.session.commit()

@bp.route("/community/ban", methods=("POST",))
def ban():
    # Ban a user from participating in the community
    return

@bp.route("/community/<string:name>", methods=("GET",))
def index(name):
    # Show the community, posts, etc
    community = Community.query.filter(Community.name == name).first()
    if not community:
        # 404 it
        return render_template("404.html"), 404
    # found it, get the latest posts
    posts = getRecentPosts(community)
    return render_template("community/index.html", name=name, posts=posts)

@bp.route("/community/post", methods=("GET", "POST"))
def post():
    if not g.user:
        return redirect(url_for('auth.login'))
    # Add a post to the community
    if request.method == "GET":
        return render_template("community/post.html")
    
    community_id = request.form["community_id"] # Should be a hidden, disabled input in the form
    title = request.form["title"]
    text = request.form["text"]
    
    userObj = g.user
    community = Community.query.filter(Community.id == community_id)
    if not community:
        # ...community doesn't exist?
        # TODO: "something went wrong" page that redirects to index
        error_message = "Community doesn't exist"
        return render_template("error.html", error_message=error_message)
    
    if not post or not title:
        # Meaningful message
        return render_template("error.html", error_message="Post title or body missing")

    if not community in userObj.communities or community in userObj.banned_on:
        # User is not a member of the community, or is banned from participating in it
        return redirect(url_for('community.index', name=community.name))

    # Success
    postObj = Post(user_id=user_id, community_id=community.id, title=title, text=text)
    community.posts.append(postObj)
    db.session.commit()
    return redirect(url_for("community.viewpost", id=postObj.id))

@bp.route("/community/viewpost/<int:id>", methods=("GET",))
def viewpost(id):
    return
