"""
Insta485 index (main) view.

URLs include:
/
"""
import flask
import insta485
import arrow


@insta485.app.route('/')
def show_index():
    """Display / route."""
    if "logname" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))

    connection = insta485.model.get_db()
    logname = flask.session["logname"]

    # Modified query to only get posts from users that logname follows (and their own posts)
    cur = connection.execute(
        "SELECT DISTINCT p.* "
        "FROM posts p "
        "LEFT JOIN following f ON p.owner = f.username2 "
        "WHERE f.username1 = ? OR p.owner = ? "
        "ORDER BY p.postid DESC",
        (logname, logname)
    )
    posts = cur.fetchall()
    
    modified_posts = []
    for post in posts:
        # Get comments
        cur = connection.execute(
            "SELECT owner, text FROM comments "
            "WHERE postid = ? "
            "ORDER BY commentid ASC",
            (post["postid"],)
        )
        comments = cur.fetchall()

        # Get like count
        cur = connection.execute(
            "SELECT COUNT(*) AS like_count "
            "FROM likes "
            "WHERE postid = ?",
            (post["postid"],)
        )
        num_likes = cur.fetchone()['like_count']

        # Get owner's profile picture
        cur = connection.execute(
            "SELECT filename "
            "FROM users "
            "WHERE username = ?",
            (post["owner"],)
        )
        owner_info = cur.fetchone()

        # Check if user liked the post
        cur = connection.execute(
            "SELECT EXISTS("
            "  SELECT 1 FROM likes "
            "  WHERE owner = ? AND postid = ?"
            ") as liked",
            (logname, post["postid"])
        )
        user_liked = cur.fetchone()['liked']

        avatar = owner_info["filename"] if owner_info else "default.jpg"

        modified = {
            "postid": post["postid"],
            "filename": flask.url_for("serve_upload", filename=post["filename"]),
            "owner": post["owner"],
            "created": arrow.get(post["created"]).humanize(),
            "owner_pfp": flask.url_for("serve_upload", filename=avatar),
            "likes": num_likes,
            "comments": comments,
            "logname": logname,
            "liked": bool(user_liked)
        }
        modified_posts.append(modified)

    context = {"logname": logname, "posts": modified_posts}
    return flask.render_template("index.html", **context)


@insta485.app.route("/uploads/<filename>")
def serve_upload(filename):
    """Serve uploaded files from var/uploads/."""
    return flask.send_from_directory(insta485.app.config["UPLOAD_FOLDER"], filename)