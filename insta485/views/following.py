"""
Insta485 following view.

URLs include:
/users/<user_url_slug>/following/
/following/
"""
import flask
import insta485


@insta485.app.route('/users/<user_url_slug>/following/')
def show_following(user_url_slug):
    """Display /users/<user_url_slug>/following/ route."""
    # Connect to database
    connection = insta485.model.get_db()

    # Check if user is logged in
    if 'logname' not in flask.session:
        return flask.redirect(flask.url_for('show_login'))
    
    logname = flask.session['logname']

    # Check if the requested user exists
    cur = connection.execute(
        "SELECT username FROM users WHERE username = ?",
        (user_url_slug,)
    )
    if not cur.fetchone():
        flask.abort(404)

    # Get list of users that user_url_slug is following
    cur = connection.execute(
        """
        SELECT 
            u.username,
            u.filename AS user_img_url,
            EXISTS(
                SELECT 1 
                FROM following f2 
                WHERE f2.username1 = ? AND f2.username2 = u.username
            ) AS logname_follows_username
        FROM following f
        JOIN users u ON f.username2 = u.username
        WHERE f.username1 = ?
        ORDER BY u.username
        """,
        (logname, user_url_slug)
    )
    following = cur.fetchall()

    # Add URL prefix to user images
    for follow in following:
        follow['user_img_url'] = flask.url_for(
           "serve_upload", 
            filename=follow['user_img_url']
        )

    # Render template
    return flask.render_template(
        "following.html",
        logname=logname,
        following=following
    )


@insta485.app.route("/following/", methods=["POST"])
def handle_following():
    """Handle POST requests for follow/unfollow operations."""
    if "logname" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))

    # Get target URL for redirect after operation
    target = flask.request.args.get("target", "/")
    
    # Connect to database
    connection = insta485.model.get_db()
    logname = flask.session["logname"]
    
    # Get POST request operation and username
    operation = flask.request.form.get("operation")
    username2 = flask.request.form.get("username")

    # Verify both username2 and operation are provided
    if not username2 or not operation:
        flask.abort(400)

    # Verify user exists
    cur = connection.execute(
        "SELECT username FROM users WHERE username = ?",
        (username2,)
    )
    if not cur.fetchone():
        flask.abort(404)

    if operation == "follow":
        # Check if already following
        cur = connection.execute(
            "SELECT * FROM following WHERE username1 = ? AND username2 = ?",
            (logname, username2)
        )
        if cur.fetchone():
            flask.abort(409)  # Already following

        # Create new following relationship
        connection.execute(
            "INSERT INTO following (username1, username2) VALUES (?, ?)",
            (logname, username2)
        )

    elif operation == "unfollow":
        # Check if following exists
        cur = connection.execute(
            "SELECT * FROM following WHERE username1 = ? AND username2 = ?",
            (logname, username2)
        )
        if not cur.fetchone():
            flask.abort(409)  # Not following

        # Delete following relationship
        connection.execute(
            "DELETE FROM following WHERE username1 = ? AND username2 = ?",
            (logname, username2)
        )

    else:
        flask.abort(400)  # Invalid operation

    # Return to target page after operation
    return flask.redirect(target)

# @insta485.app.route("/uploads/<filename>")
# def serve_upload(filename):
#     """Serve uploaded files from var/uploads/."""
#     return flask.send_from_directory(insta485.app.config["UPLOAD_FOLDER"], filename)