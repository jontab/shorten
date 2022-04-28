from typing import Callable, Tuple
from urllib.parse import urlparse
from functools import wraps
from pathlib import Path
import hashlib
import string
import os


import onetimepass
import hashids
import quart

from shorten.database import CachedFile


def is_valid_link(link: str) -> bool:
    """
    Returns whether the given link is valid and can be shortened.
    """
    try:
        result = urlparse(link)
        return all([result.scheme, result.netloc])
    except:
        return False


def is_valid_vanity(vanity: str) -> bool:
    """
    Returns whether the vanity link is valid and can be used.
    """
    return all([x in string.ascii_letters + string.digits for x in vanity])


def get_hasher() -> hashids.Hashids:
    """
    Returns the instance of the hasher that will be used to map numbers
    to links.
    """
    return hashids.Hashids(quart.current_app.secret_key, min_length=4)


def check_otp(form) -> Tuple[bool, str]:
    """
    Checks the one-time password in a given form; returns whether there was an
    error, and returns a description of it.
    """
    otp = form.get("otp")

    try:
        if not otp:
            return False, "One-time password not provided!"
        elif not onetimepass.valid_totp(int(otp), quart.current_app.secret_key):
            return False, "One-time password is invalid!"
        else:
            return True, "Success!"
    except ValueError:
        return False, "One-time password is invalid!"


def save_file_cache_wrapper(function: Callable) -> Callable:
    """
    Before saving file to storage, checks the database for a file that has the
    same hash.
    """
    @wraps(function)
    async def wrapper(data: bytes, filename: str) -> str:
        hash = hashlib.sha256(data).hexdigest()

        try:
            cached = CachedFile.get(CachedFile.hash == hash)
        except CachedFile.DoesNotExist:
            # Store the result into the database.
            name = await function(data, filename)
            CachedFile.create(hash=hash, filename=name)
            return name
        else:
            # Return the filename of the file with the same hash.
            return cached.filename
    return wrapper


@save_file_cache_wrapper
async def save_file(data: bytes, filename: str) -> str:
    """
    Saves a file to storage by attempting to save it with its current name. If
    there is already a file with that name, numbers are appended to the string.
    """
    folder = Path(quart.current_app.config["UPLOADS_FOLDER"])
    folder.mkdir(parents=True, exist_ok=True)

    prefix = Path(filename).stem
    suffix = Path(filename).suffix

    name = prefix + suffix
    number = 0

    while True:
        try:
            with open(folder / name, "xb") as dest:
                dest.write(data)
        except FileExistsError:
            number += 1
            name = f"{prefix}-{number}{suffix}"
        else:
            break

    return name
