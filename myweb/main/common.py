from functools import wraps
from main import session, redirect, request, url_for, ALLOWED_EXTENSIONS
from string import digits, ascii_uppercase, ascii_lowercase
import random
import re
import os
from werkzeug.security import generate_password_hash, check_password_hash


# implement login password security
def hash_password(password):
    return generate_password_hash(password)

def check_password(hashed_password, user_password):
    return check_password_hash(hashed_password, user_password)

# secure_filename() function
def check_filename(filename):
    reg = re.compile("[^A-Za-z0-9_.가-힝-]")
    for sep in os.path.sep, os.path.altsep:
        if sep:
            filename = filename.replace(sep, ' ')
            print(filename)
            filename = str(reg.sub('', '_'.join(filename.split()))).strip('._')
    return filename


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1] in ALLOWED_EXTENSIONS

def rand_generator(length=8):
    char = ascii_lowercase + ascii_uppercase + digits
    return "".join(random.sample(char, length))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("id") is None or session.get("id") == "":
            return redirect(url_for("member.member_login", next_url=request.url))
        return f(*args, **kwargs)
    return decorated_function