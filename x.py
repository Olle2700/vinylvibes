import json
import os
import re
import smtplib
import time
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import wraps

import dictionary
import mysql.connector
from flask import make_response, request
from werkzeug.utils import secure_filename

##############################
# GLOBALS / CONFIG
##############################
allowed_languages = ["english", "danish", "spanish"]
default_language = "english"
UPLOAD_AVATAR_FOLDER = os.path.join("static", "uploads", "avatars")
UPLOAD_MEDIA_FOLDER = os.path.join("static", "uploads", "media")
os.makedirs(UPLOAD_AVATAR_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_MEDIA_FOLDER, exist_ok=True)

EMAIL_REGEX = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
USERNAME_MIN, USERNAME_MAX = 3, 20
NAME_MIN, NAME_MAX = 2, 40
PASSWORD_MIN, PASSWORD_MAX = 6, 64
POST_MIN_LEN, POST_MAX_LEN = 1, 280
COMMENT_MIN_LEN, COMMENT_MAX_LEN = 1, 240


##############################
# DATABASE
##############################
def db():
    """
    Returns a database connection and cursor with dictionary results.
    """
    conn = mysql.connector.connect(
        host="mariadb",
        user="root",
        password="password",
        database="vinylvibes",
    )
    return conn, conn.cursor(dictionary=True)


##############################
# LANGUAGE HELPERS
##############################
def set_language(lan: str):
    global default_language
    if lan in allowed_languages:
        default_language = lan
    return default_language


def lans(key: str, lan: str | None = None):
    """
    Fetches a translation from dictionary.json first, falling back to dictionary.py constants.
    """
    active_lang = lan if lan in allowed_languages else default_language
    try:
        with open("dictionary.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            return data.get(key, {}).get(active_lang, key)
    except Exception:
        pass

    value = getattr(dictionary, key, {})
    return value.get(active_lang, value.get(active_lang[:2], value.get("english", key)))


##############################
# DECORATORS
##############################
def no_cache(view):
    @wraps(view)
    def no_cache_view(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    return no_cache_view


##############################
# VALIDATION
##############################
def validate_user_email(lan: str = "english"):
    user_email = request.form.get("email", "").strip().lower()
    if not re.match(EMAIL_REGEX, user_email):
        raise Exception(dictionary.invalid_email[lan], 400)
    return user_email


def validate_user_username(lan: str = "english"):
    user_username = request.form.get("username", "").strip()
    error = dictionary.invalid_username.get(lan, "Invalid username")
    if len(user_username) < USERNAME_MIN or len(user_username) > USERNAME_MAX:
        raise Exception(error, 400)
    return user_username


def validate_user_first_name(lan: str = "english"):
    user_first_name = request.form.get("first_name", "").strip()
    error = dictionary.invalid_first_name.get(lan, "Invalid first name")
    if len(user_first_name) < NAME_MIN or len(user_first_name) > NAME_MAX:
        raise Exception(error, 400)
    return user_first_name


def validate_user_last_name(lan: str = "english"):
    user_last_name = request.form.get("last_name", "").strip()
    error = dictionary.invalid_last_name.get(lan, "Invalid last name")
    if len(user_last_name) > NAME_MAX:
        raise Exception(error, 400)
    return user_last_name


def validate_user_password(lan: str = "english"):
    user_password = request.form.get("password", "").strip()
    if len(user_password) < PASSWORD_MIN or len(user_password) > PASSWORD_MAX:
        raise Exception(dictionary.invalid_password[lan], 400)
    return user_password


def validate_user_password_confirm(lan: str = "english"):
    user_password_confirm = request.form.get("password_confirm", "").strip()
    if len(user_password_confirm) < PASSWORD_MIN or len(user_password_confirm) > PASSWORD_MAX:
        raise Exception(dictionary.invalid_password[lan], 400)
    return user_password_confirm


def validate_post(lan: str = "english"):
    post = request.form.get("message", "").strip()
    if len(post) < POST_MIN_LEN or len(post) > POST_MAX_LEN:
        raise Exception(dictionary.invalid_post[lan], 400)
    return post


def validate_comment(lan: str = "english"):
    comment = request.form.get("comment", "").strip()
    if len(comment) < COMMENT_MIN_LEN or len(comment) > COMMENT_MAX_LEN:
        raise Exception(dictionary.invalid_comment[lan], 400)
    return comment


# Hex-based keys (verification/reset)
def validate_uuid(value: str, field_name: str = "id", lan: str = "english"):
    value = value.strip()
    if not re.fullmatch(r"[0-9a-f]{32}", value):
        raise Exception(dictionary.invalid_uuid.get(lan, f"Invalid {field_name}"), 400)
    return value


# Auto-increment primary keys (numeric)
def validate_pk(value: str, field_name: str = "id", lan: str = "english"):
    value = str(value).strip()
    if not value.isdigit():
        raise Exception(dictionary.invalid_uuid.get(lan, f"Invalid {field_name}"), 400)
    return int(value)


def validate_search_term(lan: str = "english"):
    term = request.values.get("q", "").strip()
    if len(term) < 2:
        raise Exception(dictionary.invalid_search.get(lan, "Search too short"), 400)
    return term


##############################
# FILE UPLOADS
##############################
def save_upload(file_storage, target_folder, allowed_extensions=None, prefix="upload"):
    if not file_storage:
        return ""
    filename = secure_filename(file_storage.filename)
    if not filename:
        return ""
    ext = filename.rsplit(".", 1)[-1].lower()
    allowed = allowed_extensions or {"png", "jpg", "jpeg", "gif", "webp", "mp4", "mov", "pdf", "mp3"}
    if ext not in allowed:
        raise Exception("Invalid file type", 400)
    unique_name = f"{prefix}_{uuid.uuid4().hex}.{ext}"
    os.makedirs(target_folder, exist_ok=True)
    path = os.path.join(target_folder, unique_name)
    file_storage.save(path)
    return path.replace("\\", "/")


##############################
# EMAIL
##############################
def send_email(to_email: str, subject: str, template: str):
    """
    Sends an email via SMTP. Falls back to console logging if credentials are missing.
    """
    sender_email = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASSWORD", "")

    if not sender_email or not password:
        print(f"[email disabled] To: {to_email} | Subject: {subject}")
        print(template)
        return "email logged"

    try:
        message = MIMEMultipart()
        message["From"] = "VinylVibes"
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(template, "html"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, to_email, message.as_string())

        return "email sent"
    except Exception as ex:
        print("email error", ex)
        raise Exception("cannot send email", 500)
