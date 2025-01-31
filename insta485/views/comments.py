"""Handle comments-related routes."""
import flask
import insta485

@insta485.app.route("/comments/", methods=["POST"])
def handle_comments():
    if "logname" not in flask.session:
        return flask.redirect(flask.url_for("login"))
    
    # Extract form data
    text = flask.request.form.get("text")
    postid = flask.request.form.get("postid")
    
    if not text or not postid:
        flask.abort(400)
    
    # Insert into database
    db = insta485.model.get_db()
    db.execute(
        "INSERT INTO comments (owner, postid, text) VALUES (?, ?, ?)",
        (flask.session["logname"], postid, text)
    )
    
    # Redirect back or to target
    target = flask.request.args.get('target', '/')
    return flask.redirect(target)
