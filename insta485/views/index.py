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

    # Connect to database
    connection = insta485.model.get_db()

    # Query database
    logname = "awdeorio"
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

        modified = {
            "postid": post["postid"],
            "filename": post["filename"],
            "owner": post["owner"],
            "created": arrow.get(post["created"]).humanize(),
            "owner_pfp": avatar,
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
