import insta485
import sqlite3
import flask
import arrow

@insta485.app.route('/posts/<postid_url_slug>/')
def posts(postid_url_slug):
    if "logname" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))

    # Connect to database
    #connection = insta485.model.get_db()

    # Query database
    logname = flask.session["logname"]
    connection = insta485.model.get_db()
    connection.row_factory = sqlite3.Row
    #logname = "awdeorio"

    cur = connection.execute(
        "SELECT * FROM posts WHERE postid = ?",
        (postid_url_slug, )
    )
    post = cur.fetchone()
    modified_post = dict(post)
    modified_post["created"] = arrow.get(post["created"]).humanize()
    filename = post["filename"]
    modified_post["filename"] = flask.url_for('serve_upload', filename=filename)

    # get owner pfp 
    owner = post["owner"]
    cur_pfp = connection.execute(
        "SELECT filename FROM users WHERE username = ?",
        (owner, )
    )
    pfp = cur_pfp.fetchone()

    # get comments
    cur_comments = connection.execute(
        "SELECT * FROM comments WHERE postid = ?",
        (postid_url_slug, )
    )
    comments = cur_comments.fetchall()

    # get number of likes 
    cur_likes = connection.execute(
        "SELECT COUNT(*) AS like_count FROM likes WHERE postid = ?",
        (postid_url_slug, )
    )
    like_count = cur_likes.fetchone()['like_count']

    # get like status
    cur_like_status = connection.execute(
        "SELECT EXISTS(SELECT 1 FROM likes WHERE postid = ? AND owner = ?)",
        (postid_url_slug, logname)
    )
    like_status = cur_like_status.fetchone()[0]

    context = {"logname": logname, 
               "post": modified_post, 
               "comments": comments,
               "likes": like_count,
               "like_status": like_status,
               "owner_img_url": pfp}
    return flask.render_template("post.html", **context)

# @insta485.app.route("/uploads/<filename>")
# def serve_upload(filename):
#     """Serve uploaded files from var/uploads/."""
#     return flask.send_from_directory(insta485.app.config["UPLOAD_FOLDER"], filename)
