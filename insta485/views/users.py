import insta485
import flask

@insta485.app.route('/users/<user_url_slug>/')
def users(user_url_slug):
    connection = insta485.model.get_db()
    logname = "awdeorio"

    cur = connection.execute(
        "SELECT * FROM users WHERE username = ?", 
        (user_url_slug, )
    )
    
    # get user profile 
    user = cur.fetchone()
    
    # Check if user exists
    if user is None:
        return flask.abort(404)
    
    # get following status 
    if user_url_slug == logname:
        follow_status = False  # Users cannot follow themselves
    else:
        curr_following = connection.execute(
            "SELECT 1 FROM following WHERE username1 = ? AND username2 = ?",
            (logname, user_url_slug)
        )
        follow_status = curr_following.fetchone() is not None
 
    curr_posts = connection.execute(
        "SELECT * FROM posts WHERE owner = ?",
        (user_url_slug, )
    )
    posts = curr_posts.fetchall()
    modified_posts = []
    for post in posts:
        post_dict = dict(post)  
        filename = post["filename"]
        post_dict["image_url"] = flask.url_for('static', filename=f'uploads/{filename}')
        modified_posts.append(post_dict)


    # get followers
    curr_followers = connection.execute(
        "SELECT COUNT(*) AS followers_count FROM following WHERE username2 = ?",
        (user_url_slug, )
    )
    #get follower count
    followers = curr_followers.fetchone().get('followers_count')

    # get following
    curr_following = connection.execute(
        "SELECT COUNT(*) AS following_count FROM following WHERE username1 = ?",
        (user_url_slug, )
    )
    following = curr_following.fetchone().get('following_count')

    context = {"logname": logname, 
               "user": user, 
               "posts": modified_posts, 
               "total_posts": len(modified_posts),
               "logname_follows_username": follow_status, 
               "followers": followers,
               "following": following}
    return flask.render_template("user.html", **context)
