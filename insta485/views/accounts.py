"""Account-related views for Insta485."""
import flask
import insta485
import hashlib
import uuid

@insta485.app.route("/accounts/login/", methods=["GET"])
def show_login():
    """Display the login page or redirect if already logged in."""
    # If "logname" in session, user is already logged in -> redirect
    if "logname" in flask.session:
        return flask.redirect("/")

    return flask.render_template("login.html")


@insta485.app.route("/accounts/create/", methods=["GET"])
def show_create_account():
    """Display account creation page."""
    return flask.render_template("create.html")


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
    else:
        flask.abort(400, f"Bad operation '{operation}'")

@insta485.app.route("/accounts/logout/", methods=["POST"])
def show_logout():
    """Handle logout."""
    if "logname" not in flask.session:
        flask.abort(403)
    
    flask.session.clear()
    return flask.redirect(flask.url_for("show_login"))
