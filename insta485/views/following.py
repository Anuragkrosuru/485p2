"""
Insta485 following view.

URLs include:
/users/<user_url_slug>/following/
"""
import flask
import insta485


@insta485.app.route('/users/<user_url_slug>/following/')
def show_following(user_url_slug):
    """Display /users/<user_url_slug>/following/ route."""
    # Connect to database
    connection = insta485.model.get_db()

    # Check if user is logged in
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('show_login'))
    
    logname = flask.session['username']

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
            'show_file', 
            filename=follow['user_img_url']
        )

    # Render template
    return flask.render_template(
        "following.html",
        logname=logname,
        following=following
    )