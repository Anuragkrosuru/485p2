import pathlib
import uuid
import os
import flask
import insta485

def save_uploaded_file(fileobj):
    """
    Save an uploaded file using a UUID-based filename and return the new filename.
    """
    original_filename = fileobj.filename
    stem = uuid.uuid4().hex
    suffix = pathlib.Path(original_filename).suffix.lower()
    uuid_basename = f"{stem}{suffix}"
    # Check if the file type is allowed
    if suffix[1:] not in insta485.app.config['ALLOWED_EXTENSIONS']:
        flask.abort(400, "Invalid file type")
    # Build the path and save the file
    path = insta485.app.config["UPLOAD_FOLDER"] / uuid_basename
    fileobj.save(path)
    return uuid_basename

@insta485.app.route("/posts/", methods=["POST"])
def create_or_delete_post():
    # Determine the target URL to redirect to.
    target = flask.request.args.get("target")
    if not target:
        target = flask.url_for("users", user_url_slug=flask.session["logname"])
    
    # Get the operation from the form data.
    operation = flask.request.form.get("operation")
    if not operation:
        flask.abort(400, "Operation not specified")
    
    # Open a database connection.
    connection = insta485.model.get_db()

    if operation == "create":
        # Create operation: make sure a file was uploaded.
        if "file" not in flask.request.files:
            flask.abort(400, "No file uploaded")
        fileobj = flask.request.files["file"]
        if fileobj.filename == "":
            flask.abort(400, "Empty file uploaded")
        
        # Save the file and get the UUID-based filename.
        filename = save_uploaded_file(fileobj)
        
        # Insert a new post record with the filename and owner.
        connection.execute(
            "INSERT INTO posts(filename, owner) VALUES (?, ?)",
            (filename, flask.session["logname"])
        )
        connection.commit()
        return flask.redirect(target)
    
    elif operation == "delete":
        # Delete operation: we expect a postid from the form.
        postid = flask.request.form.get("postid")
        if not postid:
            flask.abort(400, "Post ID not provided for deletion")
        
        # Look up the post in the database.
        cur = connection.execute(
            "SELECT * FROM posts WHERE postid = ?",
            (postid,)
        )
        post = cur.fetchone()
        if not post:
            flask.abort(404, "Post not found")
        
        # Ensure that the logged-in user owns the post.
        if post["owner"] != flask.session["logname"]:
            flask.abort(403, "Cannot delete a post you do not own")
        
        # Delete the file from the filesystem.
        file_path = insta485.app.config["UPLOAD_FOLDER"] / post["filename"]
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete any related records (e.g., likes and comments) then the post record itself.
        connection.execute("DELETE FROM likes WHERE postid = ?", (postid,))
        connection.execute("DELETE FROM comments WHERE postid = ?", (postid,))
        connection.execute("DELETE FROM posts WHERE postid = ?", (postid,))
        connection.commit()
        return flask.redirect(target)
    
    else:
        flask.abort(400, "Invalid operation")
