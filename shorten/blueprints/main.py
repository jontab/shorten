from shorten.database import ShortenedLink
from shorten.helpers import *


import mimetypes


from peewee import IntegrityError
from quart import current_app
import quart


bp = quart.Blueprint("main", __name__)


@bp.get("/")
async def index() -> quart.ResponseReturnValue:
    """
    Returns the primary page which contains the forms for creating new shortened
    links and uploading files.
    """
    return await quart.render_template("index.html")


@bp.post("/shorten")
async def shorten() -> quart.ResponseReturnValue:
    """
    Shortens a link by consuming it from a form.
    """
    form = await quart.request.form
    error = None

    original = form.get("original")
    vanity = form.get("vanity")

    if not original:
        error = "Link not provided!"
    elif not is_valid_link(original):
        error = "Link is invalid!"
    elif vanity and not is_valid_vanity(vanity):
        error = "Vanity is invalid!"
    elif quart.current_app.config["REQUIRE_OTP"]:
        success, message = check_otp(form)
        if not success:
            error = message

    if vanity:
        # Check if this vanity has already been taken.
        try:
            ShortenedLink.get(ShortenedLink.vanity == vanity)
        except ShortenedLink.DoesNotExist:
            ...
        else:
            error = "Vanity is already taken!"

    if not error:
        link = ShortenedLink.create(
            original=original,
            vanity=vanity,
        )

        # TODO: It is theoretically possibly that the default vanity is taken
        # and then it is transformed into an already taken vanity. We would
        # need to increment the identifier or something in this case.
        if not link.vanity:
            while True:
                try:
                    link.vanity = get_hasher().encode(link.id)
                    link.save()
                except IntegrityError:
                    link.id += 1
                else:
                    break

        return await quart.render_template("index.html", link=link)
    else:
        await quart.flash(error)
        return await quart.render_template("index.html")


@bp.get("/<vanity>")
async def redirect(vanity: str) -> quart.ResponseReturnValue:
    """
    Redirects to an original link given its associated vanity link.
    """
    try:
        link = ShortenedLink.get(ShortenedLink.vanity == vanity)
    except ShortenedLink.DoesNotExist:
        await quart.flash("Link not found!")
        return quart.redirect(quart.url_for("main.index"))
    else:
        link.hits += 1
        link.save()
        return quart.redirect(link.original)


@bp.post("/upload")
async def upload() -> quart.ResponseReturnValue:
    """
    Uploads a file to the server by consuming it from a form.
    """
    files = await quart.request.files
    error = None

    file = files.get("file")

    if not file:
        error = "File not provided!"
    elif not file.filename:
        error = "File has no name!"
    elif current_app.config["REQUIRE_OTP"]:
        success, message = check_otp(await quart.request.form)
        if not success:
            error = message

    if not error:
        name = await save_file(file.read(), file.filename)
        return await quart.render_template("index.html", filename=name)
    else:
        await quart.flash(error)
        return await quart.render_template("index.html")


@bp.get("/preview/<filename>")
async def preview(filename: str) -> quart.ResponseReturnValue:
    """
    Attempts to preview a file given its contents.
    """
    guessed = mimetypes.guess_type(filename)[0]
    error = None

    if not guessed:
        error = "Cannot preview this file!"
    elif not guessed.startswith("text/"):
        error = "Cannot preview this file!"

    if not error:
        path = Path(current_app.config["UPLOADS_FOLDER"]) / filename

        try:
            with path.open("r") as f:
                contents = f.read()
        except FileNotFoundError:
            error = "That file does not exist!"
        else:
            return await quart.render_template(
                "preview.html",
                filename=filename,
                contents=contents,
            )

    await quart.flash(error)
    return quart.redirect(quart.url_for("main.index"))


@bp.get("/raw/<filename>")
async def raw(filename: str) -> quart.ResponseReturnValue:
    """
    Return the download link for a given file.
    """
    path = Path(current_app.config["UPLOADS_FOLDER"]) / filename

    try:
        with path.open("rb") as f:
            contents = f.read()
    except FileNotFoundError:
        await quart.flash("That file does not exist!")
        return quart.redirect(quart.url_for("main.index"))

    guessed = mimetypes.guess_type(filename)[0]
    return quart.Response(
        contents,
        mimetype=guessed or "application/octet-stream",
    )
