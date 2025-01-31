import insta485
import flask
import sqlite3

@insta485.app.route('/explore/')
def explore():
    
    #logname = "awdeorio"
    if "logname" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))

    # Connect to database
    #connection = insta485.model.get_db()

    # Query database
    logname = flask.session["logname"]
    connection = insta485.model.get_db()
    connection.row_factory = sqlite3.Row

    # get all of the ppl logname does not follow
    curr = connection.execute(
        """
        SELECT u.username, u.filename
        FROM users u
        WHERE u.username <> ?
        AND NOT EXISTS (
            SELECT 1 from following f
            WHERE f.username1 = ?
            AND f.username2 = u.username
        )
        """,
        (logname, logname)  
    )

    not_following = curr.fetchall()
    not_following = [dict(user) for user in not_following]
    for user in not_following:
        user["filename"] = flask.url_for('serve_upload', filename=user["filename"])

    context = {"logname": logname,
               "not_following": not_following}

    return flask.render_template("explore.html", **context)

# @insta485.app.route("/uploads/<filename>")
# def serve_upload(filename):
#     """Serve uploaded files from var/uploads/."""
#     return flask.send_from_directory(insta485.app.config["UPLOAD_FOLDER"], filename)
        