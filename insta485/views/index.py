"""
Insta485 index (main) view.

URLs include:
/
"""
import flask
import insta485
import arrow
import os


@insta485.app.route('/')
def show_index():
    """Display / route."""

    # Redirect to login if not authenticated
    if "logname" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))

    # Connect to database
    connection = insta485.model.get_db()

    # Query database
    logname = flask.session["logname"]
    # cur = connection.execute(
    #     "SELECT username, fullname "
    #     "FROM users "
    #     "WHERE username != ?",
    #     (logname, )
    # )
    #users = cur.fetchall()
    cur = connection.execute(
        "SELECT * "
        "FROM posts "
    )
    posts = cur.fetchall()
    modified_posts = []
    for post in posts:
        # sql query for comments 
        cur = connection.execute(
            "SELECT owner, text FROM comments WHERE postid = ? ORDER BY commentid ASC",
            (post["postid"],)
        )
        comments = cur.fetchall()
        # sql query for likes 
        cur = connection.execute(
            "SELECT COUNT(*) AS like_count FROM likes WHERE postid = ?",
            (post["postid"],)
        )
        num_likes = cur.fetchone()['like_count']
        # sql query for pfp 
        cur = connection.execute(
            "SELECT filename FROM users WHERE username = ?",
            (post["owner"],)
        )
        owner_info = cur.fetchone()
        # sql query for liked
        cur = connection.execute(
             "SELECT EXISTS("
            "  SELECT 1 FROM likes "
            "  WHERE owner = ? AND postid = ?"
            ") as liked",
            (logname, post["postid"])
        )
        user_liked = cur.fetchone()['liked']
        if owner_info is not None:
            avatar = owner_info["filename"]
        else:
            avatar = "default.jpg" 

        filename = post["filename"]
        modified = {
            "postid": post["postid"],
            "filename": flask.url_for("serve_upload", filename=filename),
            "owner": post["owner"],
            "created": arrow.get(post["created"]).humanize(),
            "owner_pfp": flask.url_for("serve_upload", filename=avatar),
            "likes": num_likes,
            "comments": comments,
            "logname" : logname,
            "liked": bool(user_liked)
        }
        modified_posts.append(modified)


    # Add database info to context
    # context = {"users": users}
    context = {"logname": logname, "posts" : modified_posts}
    return flask.render_template("index.html", **context)



@insta485.app.route("/uploads/<filename>")
def serve_upload(filename):
    """Serve uploaded files from var/uploads/."""
    return flask.send_from_directory(insta485.app.config["UPLOAD_FOLDER"], filename)

