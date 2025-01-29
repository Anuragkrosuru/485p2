import insta485

@insta485.app.route('/posts/')
def posts():
    return "Posts page"
