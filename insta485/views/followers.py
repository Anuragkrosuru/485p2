"""
Insta485 followers view.

URLs include:
/users/<user_url_slug>/followers/
/following/
"""
import flask
import insta485


@insta485.app.route('/users/<user_url_slug>/followers/')
def show_followers(user_url_slug):
    """Display /users/<user_url_slug>/followers/ route."""
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

    # Get list of followers for user_url_slug
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
        JOIN users u ON f.username1 = u.username
        WHERE f.username2 = ?
        ORDER BY u.username
        """,
        (logname, user_url_slug)
    )
    followers = cur.fetchall()

    # Add URL prefix to user images
    for follower in followers:
        follower['user_img_url'] = flask.url_for(
            "serve_upload", 
            filename=follower['user_img_url']
        )

    # Render template
    return flask.render_template(
        "followers.html",
        logname=logname,
        followers=followers
    )

# @insta485.app.route("/uploads/<filename>")
# def serve_upload(filename):
#     """Serve uploaded files from var/uploads/."""
#     return flask.send_from_directory(insta485.app.config["UPLOAD_FOLDER"], filename)
