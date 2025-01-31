"""Account-related views for Insta485."""
import flask
import insta485

@insta485.app.route("/accounts/login/", methods=["GET"])
def show_login():
    """Display the login page or redirect if already logged in."""
    if "username" in flask.session:
        return flask.redirect("/")
    
    return flask.render_template("login.html")


@insta485.app.route('/accounts/create/', methods=["GET"])
def show_create_account():
    """Display account creation page."""
    return flask.render_template("create.html")

