"""Account-related views for Insta485."""
import flask
import insta485
import hashlib
import uuid
import os
from werkzeug.utils import secure_filename

@insta485.app.route("/accounts/login/", methods=["GET"])
def show_login():
    """Display the login page or redirect if already logged in."""
    # If "logname" in session, user is already logged in -> redirect
    if "logname" in flask.session:
        return flask.redirect("/")

    return flask.render_template("login.html")

@insta485.app.route("/accounts/edit/", methods=["GET"])
def show_edit_account():
    """Display account edit page."""
    if "logname" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))

    # Get current user's info
    connection = insta485.model.get_db()
    logname = flask.session["logname"]

    cur = connection.execute(
        "SELECT fullname, email, filename FROM users WHERE username = ?",
        (logname,)
    )
    user = cur.fetchone()

    context = {
        "logname": logname,
        "user_img_url": user["filename"],
        "fullname": user["fullname"],
        "email": user["email"]
    }
    return flask.render_template("edit.html", **context)

@insta485.app.route("/accounts/create/", methods=["GET"])
def show_create_account():
    """Display account creation page."""
    return flask.render_template("create.html")

@insta485.app.route("/accounts/delete/", methods=["GET"])
def show_delete_account():
    """Display account deletion confirmation."""
    if "logname" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    return flask.render_template("delete.html", logname=flask.session["logname"])


@insta485.app.route("/accounts/", methods=["POST"])
def accounts_operation():
    """
    Perform an account-related operation: create, login, delete, etc.
    Then redirect to ?target=... or a default.
    """
    operation = flask.request.form["operation"]  # "create", "login", etc.
    target_url = flask.request.args.get("target", "/")

    connection = insta485.model.get_db()

    if operation == "create":
        # 1) Grab form data
        username = flask.request.form["username"]
        password = flask.request.form["password"]

        # 2) Check if username already exists
        existing = connection.execute(
            "SELECT username FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        if existing is not None:
            flask.abort(409, f"Username '{username}' already exists.")

        # 3) Hash the password with salt
        algorithm = "sha512"
        salt = uuid.uuid4().hex
        hash_obj = hashlib.new(algorithm)
        hash_obj.update((salt + password).encode("utf-8"))
        db_hash = hash_obj.hexdigest()
        password_db_string = f"{algorithm}${salt}${db_hash}"

        # 4) Insert into DB
        connection.execute(
            "INSERT INTO users(username, fullname, email, filename, password) "
            "VALUES (?, ?, ?, ?, ?)",
            (username, "New User", "fake@example.com", "default.jpg", password_db_string)
        )
        connection.commit()

        # 5) Log them in: set session["logname"]
        flask.session["logname"] = username

        return flask.redirect(target_url)

    elif operation == "login":
        # 1) Extract form data
        username = flask.request.form["username"]
        password = flask.request.form["password"]

        # 2) Retrieve row from DB
        row = connection.execute(
            "SELECT password FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if row is None:
            # No such user => 403
            flask.abort(403, "Username does not exist")

        # row["password"] is "sha512$<salt>$<hash>"
        password_db_string = row["password"]
        algorithm, salt, db_hash = password_db_string.split("$")

        # 3) Re-hash to compare
        hash_obj = hashlib.new(algorithm)
        hash_obj.update((salt + password).encode("utf-8"))
        calc_hash = hash_obj.hexdigest()

        if calc_hash != db_hash:
            # Wrong password => 403
            flask.abort(403, "Incorrect password")

        # 4) If matching => set session
        flask.session["logname"] = username

        return flask.redirect(target_url)

    elif operation == "logout":
        """Handle logout."""
        if "logname" not in flask.session:
            flask.abort(403)
    
        flask.session.clear()
        return flask.redirect(flask.url_for("show_login"))
     
    elif operation == "delete":
        if "logname" not in flask.session:  # Changed from username to logname
            flask.abort(403)
            
        username = flask.session["logname"]  # Changed from username to logname
        
        # Delete user's posts and their images
        posts = connection.execute(
            "SELECT filename FROM posts WHERE owner = ?", (username,)
        ).fetchall()
        
        for post in posts:
            filepath = insta485.app.config["UPLOAD_FOLDER"]/post["filename"]
            if os.path.exists(filepath):
                os.remove(filepath)
        
        # Delete user's profile image
        user = connection.execute(
            "SELECT filename FROM users WHERE username = ?", (username,)
        ).fetchone()
        if user:
            filepath = insta485.app.config["UPLOAD_FOLDER"]/user["filename"]
            if os.path.exists(filepath):
                os.remove(filepath)
        
        # Delete all database entries
        connection.execute("DELETE FROM users WHERE username = ?", (username,))
        connection.commit()  # Don't forget to commit changes
        
        flask.session.clear()
        return flask.redirect(target_url) 
    
    elif operation == "edit_account":
        if "logname" not in flask.session:
            flask.abort(403)
            
        username = flask.session["logname"]
        new_name = flask.request.form["fullname"]
        new_email = flask.request.form["email"]

        # Handle file upload if provided
        if 'file' in flask.request.files and flask.request.files['file'].filename:
            fileobj = flask.request.files['file']
            
            # Create unique filename
            stem = uuid.uuid4().hex
            suffix = os.path.splitext(fileobj.filename)[1].lower()
            filename = f"{stem}{suffix}"
            
            # Get old filename
            cur = connection.execute(
                "SELECT filename FROM users WHERE username = ?",
                (username,)
            )
            old_filename = cur.fetchone()['filename']
            
            # Save new file
            path = insta485.app.config["UPLOAD_FOLDER"]/filename
            fileobj.save(path)
            
            # Delete old file if it wasn't default
            if old_filename != 'default.jpg':
                old_path = insta485.app.config["UPLOAD_FOLDER"]/old_filename
                if os.path.exists(old_path):
                    os.remove(old_path)
            
            # Update database with new filename
            connection.execute(
                "UPDATE users SET filename = ?, fullname = ?, email = ? "
                "WHERE username = ?",
                (filename, new_name, new_email, username)
            )
        else:
            # Update without changing photo
            connection.execute(
                "UPDATE users SET fullname = ?, email = ? WHERE username = ?",
                (new_name, new_email, username)
            )

        connection.commit()
        return flask.redirect(target_url)

    elif operation == "update_password":
        username = flask.session["logname"]
        old_password = flask.request.form["password"]
        new_password1 = flask.request.form["new_password1"]
        new_password2 = flask.request.form["new_password2"]
       
        # check if old password is right 
        row = connection.execute(
            "SELECT password FROM users WHERE username = ?",
            (username, )
        ).fetchone()

        if row is None:
            flask.abort(403, "Username does not exist")

        password_db_string = row["password"]
        algorithm, salt, db_hash = password_db_string.split("$")

        compare_hash_obj = hashlib.new(algorithm)
        compare_hash_obj.update((salt + old_password).encode("utf-8"))
        compare_calc_hash = compare_hash_obj.hexdigest()

        if compare_calc_hash != db_hash:
            flask.abort(403, "Incorrect password")
        
        # check if passwords are matching 
        if new_password1 != new_password2:
            flask.abort(403, "Passwords do not match")
        
        # set new password 
        salt = uuid.uuid4().hex
        new_hash_obj = hashlib.new(algorithm)
        new_hash_obj.update((salt + new_password1).encode("utf-8"))
        new_db_hash = new_hash_obj.hexdigest()
        new_password_db_string = f"{algorithm}${salt}${new_db_hash}"

        connection.execute(
            "UPDATE users SET password = ? WHERE username = ?",
            (new_password_db_string, username)
        )
        connection.commit()

        return flask.redirect(target_url)

    else:
        flask.abort(400, f"Bad operation '{operation}'")

@insta485.app.route("/accounts/logout/", methods=["POST"])
def show_logout():
    """Handle logout."""
    if "logname" not in flask.session:
        flask.abort(403)
    
    flask.session.clear()
    return flask.redirect(flask.url_for("show_login"))

# @insta485.app.route("/accounts/edit/", methods=["GET"])
# def show_edit():
#     """Display the login page or redirect if already logged in."""
#     # If "logname" in session, user is already logged in -> redirect
#     if "logname" not in flask.session:
#         flask.abort(403)

#     # get logname from usertable 
#     connection = insta485.model.get_db()
#     cur = connection.execute(
#         "SELECT * FROM users WHERE username = ?", 
#         (flask.session["logname"], )
#     )
#     user = dict(cur.fetchone())
#     user["filename"] = flask.url_for('serve_upload', filename=user["filename"])

#     context = {"user": user}
#     return flask.render_template("edit.html", **context)
    
@insta485.app.route('/accounts/auth/')
def show_auth():
    """Return 200 if user is logged in, 403 if not."""
    if "logname" not in flask.session:
        flask.abort(403)
    return '', 200 
    
@insta485.app.route("/accounts/password/", methods=["GET"])
def show_password():
    """Display password change page."""
    if "logname" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    return flask.render_template("password.html", logname=flask.session["logname"])
