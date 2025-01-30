
import insta485
import flask

@insta485.app.route("/likes/", methods=["POST"])
def update_likes():
    

    # Access the current user from session
    # (assuming you store 'logname' in session after login)
    if "logname" not in flask.session:
        # If the user isn't logged in, either redirect or abort(403).
        flask.abort(403, "You must be logged in to like/unlike.")
    logname = flask.session["logname"]

    # Retrieve form inputs from the POST body
    operation = flask.request.form["operation"]  # "like" or "unlike"
    postid = flask.request.form["postid"]        # which post to like/unlike

    # Retrieve the ?target=... query param from the URL, defaulting to "/"
    # For example, "?target=/posts/2/" means redirect to "/posts/2/"
    target_url = flask.request.args.get("target", "/")

    # Connect to the database
    connection = insta485.model.get_db()

    if operation == "like":
        # 1. Check if this user already liked the post
        already = connection.execute(
            "SELECT likeid "
            "FROM likes "
            "WHERE owner = ? AND postid = ?",
            (logname, postid),
        ).fetchone()

        if already is not None:
            # The user already liked it => conflict
            flask.abort(409, "User already liked this post.")
        else:
            # Insert a new like row
            connection.execute(
                "INSERT INTO likes(owner, postid) "
                "VALUES (?, ?)",
                (logname, postid),
            )

    elif operation == "unlike":
        # 1. Check if there's a like row for this user+post
        already = connection.execute(
            "SELECT likeid "
            "FROM likes "
            "WHERE owner = ? AND postid = ?",
            (logname, postid),
        ).fetchone()

        if already is None:
            # The user hasn't liked it => conflict
            flask.abort(409, "User tried to unlike a post they haven't liked.")
        else:
            # Delete the row
            connection.execute(
                "DELETE FROM likes "
                "WHERE owner = ? AND postid = ?",
                (logname, postid),
            )

    else:
        # If someone sent an unexpected operation
        flask.abort(400, f"Invalid operation '{operation}'")

    # Redirect the user back to the 'target_url' they came from.
    return flask.redirect(target_url)
