import csv
import io
import json
import os
import time
import uuid

import dictionary
import requests
import x
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SESSION_TYPE"] = "filesystem"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
Session(app)


##############################
# HELPERS
##############################
def set_language(lan: str | None = None):
    if lan in x.allowed_languages:
        session["lan"] = lan
        x.set_language(lan)
    return session.get("lan", x.allowed_languages[0])


@app.context_processor
def inject_globals():
    return dict(dictionary=dictionary, lan=session.get("lan", "english"), session_user=session.get("user"))


##############################
# PUBLIC PAGES
##############################
@app.get("/lang/<lan>")
def set_lang(lan="english"):
    set_language(lan)
    return redirect(request.referrer or url_for("index"))


@app.get("/", endpoint="index")
@app.get("/<lan>")
def index(lan=None):
    set_language(lan)
    if session.get("user"):
        return redirect(url_for("home"))
    return render_template("index.html")


@app.get("/login")
@app.get("/login/<lan>")
def view_login(lan=None):
    lan = set_language(lan)
    if session.get("user"):
        return redirect(url_for("home"))
    return render_template("login.html", error=None)


@app.post("/login")
@app.post("/login/<lan>")
def login(lan=None):
    lan = set_language(lan)
    try:
        user_email = x.validate_user_email(lan)
        user_password = x.validate_user_password(lan)
        db, cursor = x.db()
        cursor.execute("SELECT * FROM users WHERE user_email = %s", (user_email,))
        user = cursor.fetchone()
        if not user:
            raise Exception(dictionary.user_not_found[lan], 400)
        if user["user_blocked_at"]:
            raise Exception(dictionary.user_blocked[lan], 400)
        if user["user_verification_key"]:
            raise Exception(dictionary.user_not_verified[lan], 400)
        if not check_password_hash(user["user_password"], user_password):
            raise Exception(dictionary.invalid_credentials[lan], 400)
        user.pop("user_password")
        session["user"] = user
        return redirect(url_for("home"))
    except Exception as ex:
        msg = ex.args[0] if ex.args else "System under maintenance"
        status = ex.args[1] if len(ex.args) > 1 else 500
        return render_template("login.html", error=msg), status
    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()


@app.get("/signup")
@app.get("/signup/<lan>")
def view_signup(lan=None):
    lan = set_language(lan)
    if session.get("user"):
        return redirect(url_for("home"))
    return render_template("signup.html", error=None)


@app.post("/signup")
@app.post("/signup/<lan>")
def signup(lan=None):
    lan = set_language(lan)
    try:
        user_email = x.validate_user_email(lan)
        user_password = x.validate_user_password(lan)
        user_username = x.validate_user_username(lan)
        user_first_name = x.validate_user_first_name(lan)
        user_last_name = x.validate_user_last_name(lan)

        user_pk = uuid.uuid4().hex
        verification_key = uuid.uuid4().hex
        hashed = generate_password_hash(user_password)
        avatar_path = "https://avatar.iran.liara.run/public/40"
        now = int(time.time())

        db, cursor = x.db()
        cursor.execute(
            "INSERT INTO users (user_pk, user_email, user_password, user_username, user_first_name, user_last_name, user_avatar_path, user_bio, user_verification_key, user_verified_at, user_reset_key, user_reset_expires, user_role, user_blocked_at, user_created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, '', 0, 'user', 0, %s)",
            (
                user_pk,
                user_email,
                hashed,
                user_username,
                user_first_name,
                user_last_name,
                avatar_path,
                "",
                verification_key,
                0,
                now,
            ),
        )
        db.commit()

        verify_html = render_template("_email_verify_account.html", user_verification_key=verification_key)
        x.send_email(user_email, "Verify your VinylVibes account", verify_html)

        return render_template("signup.html", error=None, ok=dictionary.verify_email_sent[lan])
    except Exception as ex:
        if "db" in locals():
            db.rollback()
        msg = ex.args[0] if ex.args else "System under maintenance"
        if "Duplicate entry" in str(ex):
            msg = dictionary.email_taken[lan] if user_email in str(ex) else dictionary.username_taken[lan]
        return render_template("signup.html", error=msg), 400
    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()


@app.get("/verify-account")
def verify_account():
    lan = set_language()
    try:
        key = x.validate_uuid(request.args.get("key", ""), "verification", lan)
        db, cursor = x.db()
        cursor.execute(
            "UPDATE users SET user_verification_key = '', user_verified_at = %s WHERE user_verification_key = %s",
            (int(time.time()), key),
        )
        db.commit()
        return redirect(url_for("view_login"))
    except Exception as ex:
        if "db" in locals():
            db.rollback()
        msg = ex.args[0] if ex.args else "Cannot verify user"
        status = ex.args[1] if len(ex.args) > 1 else 500
        return msg, status
    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("view_login"))


##############################
# PASSWORD RESET
##############################
@app.get("/forgot-password")
def view_forgot_password():
    set_language()
    return render_template("forgot_password.html", error=None, ok=None)


@app.post("/forgot-password")
def forgot_password():
    lan = set_language()
    try:
        user_email = x.validate_user_email(lan)
        reset_key = uuid.uuid4().hex
        expires = int(time.time() + 3600)
        db, cursor = x.db()
        cursor.execute("UPDATE users SET user_reset_key = %s, user_reset_expires = %s WHERE user_email = %s", (reset_key, expires, user_email))
        db.commit()
        if cursor.rowcount != 1:
            raise Exception(dictionary.user_not_found[lan], 400)
        reset_html = render_template("_email_forgot_password.html", reset_key=reset_key)
        x.send_email(user_email, "Reset your VinylVibes password", reset_html)
        return render_template("forgot_password.html", ok=dictionary.reset_email_sent[lan], error=None)
    except Exception as ex:
        if "db" in locals():
            db.rollback()
        msg = ex.args[0] if ex.args else "System under maintenance"
        status = ex.args[1] if len(ex.args) > 1 else 500
        return render_template("forgot_password.html", error=msg, ok=None), status
    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()


@app.get("/reset-password/<reset_key>")
def view_reset_password(reset_key):
    set_language()
    return render_template("reset_password.html", reset_key=reset_key, error=None)


@app.post("/reset-password/<reset_key>")
def reset_password(reset_key):
    lan = set_language()
    try:
        reset_key = x.validate_uuid(reset_key, "reset", lan)
        new_password = x.validate_user_password(lan)
        confirm = x.validate_user_password_confirm(lan)
        if new_password != confirm:
            raise Exception(dictionary.password_mismatch[lan], 400)

        db, cursor = x.db()
        cursor.execute("SELECT user_pk, user_reset_expires FROM users WHERE user_reset_key = %s", (reset_key,))
        user = cursor.fetchone()
        if not user or user["user_reset_expires"] < int(time.time()):
            raise Exception(dictionary.invalid_reset[lan], 400)

        cursor.execute(
            "UPDATE users SET user_password = %s, user_reset_key = '', user_reset_expires = 0 WHERE user_pk = %s",
            (generate_password_hash(new_password), user["user_pk"]),
        )
        db.commit()
        return redirect(url_for("view_login"))
    except Exception as ex:
        if "db" in locals():
            db.rollback()
        msg = ex.args[0] if ex.args else "System under maintenance"
        status = ex.args[1] if len(ex.args) > 1 else 500
        return render_template("reset_password.html", reset_key=reset_key, error=msg), status
    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()


##############################
# HOME / FEED
##############################
@app.get("/home")
def home():
    lan = set_language()
    user = session.get("user")
    if not user or user.get("user_blocked_at", 0):
        return redirect(url_for("view_login"))
    try:
        db, cursor = x.db()
        cursor.execute(
            """
            SELECT p.*, u.user_username, u.user_first_name, u.user_last_name, u.user_avatar_path,
                IFNULL((SELECT COUNT(*) FROM post_likes WHERE like_post_fk=p.post_pk),0) AS like_count,
                EXISTS(SELECT 1 FROM post_likes WHERE like_post_fk=p.post_pk AND like_user_fk=%s) AS liked_by_me,
                IFNULL((SELECT COUNT(*) FROM comments WHERE comment_post_fk=p.post_pk),0) AS comment_count
            FROM posts p
            JOIN users u ON u.user_pk = p.post_user_fk
            WHERE (p.post_blocked_at = 0)
            ORDER BY p.post_created_at DESC
            LIMIT 50
            """,
            (user["user_pk"],),
        )
        posts = cursor.fetchall()

        post_ids = [p["post_pk"] for p in posts]
        comments_map = {}
        if post_ids:
            placeholders = ",".join(["%s"] * len(post_ids))
            cursor.execute(
                f"""
                SELECT c.*, u.user_username, u.user_first_name, u.user_avatar_path
                FROM comments c
                JOIN users u ON u.user_pk = c.comment_user_fk
                WHERE c.comment_post_fk IN ({placeholders})
                ORDER BY c.comment_created_at DESC
                """,
                tuple(post_ids),
            )
            for comment in cursor.fetchall():
                comments_map.setdefault(comment["comment_post_fk"], []).append(comment)

        cursor.execute(
            """
            SELECT user_pk, user_username, user_first_name, user_last_name, user_avatar_path,
                   EXISTS(SELECT 1 FROM follows WHERE follow_follower_fk=%s AND follow_following_fk=user_pk) AS following
            FROM users
            WHERE user_pk != %s AND user_blocked_at = 0
            ORDER BY RAND() LIMIT 5
            """,
            (user["user_pk"], user["user_pk"]),
        )
        suggestions = cursor.fetchall()

        return render_template("home.html", posts=posts, comments_map=comments_map, suggestions=suggestions)
    except Exception as ex:
        print("HOME ERROR:", ex, flush=True)
        return "System under maintenance", 500
    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()


##############################
# POSTS
##############################
@app.post("/api/posts")
def create_post():
    lan = set_language()
    user = session.get("user")
    if not user or user.get("user_blocked_at", 0):
        return jsonify({"status": "error", "message": "Login required"}), 401
    try:
        message = x.validate_post(lan)
        media = request.files.get("media")
        media_path = x.save_upload(media, x.UPLOAD_MEDIA_FOLDER, prefix="post")
        post_pk = uuid.uuid4().hex
        db, cursor = x.db()
        cursor.execute(
            "INSERT INTO posts (post_pk, post_user_fk, post_message, post_total_likes, post_image_path, post_blocked_at, post_created_at) VALUES (%s, %s, %s, 0, %s, 0, %s)",
            (post_pk, user["user_pk"], message, media_path, int(time.time())),
        )
        db.commit()
        post = {
            "post_pk": post_pk,
            "post_user_fk": user["user_pk"],
            "post_message": message,
            "post_total_likes": 0,
            "post_image_path": media_path,
            "liked_by_me": 0,
            "like_count": 0,
            "comment_count": 0,
            "user_first_name": user["user_first_name"],
            "user_last_name": user["user_last_name"],
            "user_username": user["user_username"],
            "user_avatar_path": user["user_avatar_path"],
        }
        html = render_template("components/post_card.html", post=post, comments=[], session_user=user, lan=lan)
        return jsonify({"status": "ok", "html": html, "message": dictionary.post_created[lan]})
    except Exception as ex:
        if "db" in locals():
            db.rollback()
        msg = ex.args[0] if ex.args else "System under maintenance"
        status = ex.args[1] if len(ex.args) > 1 else 500
        return jsonify({"status": "error", "message": msg}), status
    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()


@app.patch("/api/posts/<post_pk>")
def update_post(post_pk):
    lan = set_language()
    user = session.get("user")
    if not user or user.get("user_blocked_at", 0):
        return jsonify({"status": "error", "message": "Login required"}), 401
    try:
        post_pk = x.validate_uuid(post_pk, "post", lan)
        message = x.validate_post(lan)
        db, cursor = x.db()
        cursor.execute("SELECT post_user_fk FROM posts WHERE post_pk = %s", (post_pk,))
        owner = cursor.fetchone()
        if not owner:
            raise Exception(dictionary.post_not_found[lan], 404)
        if owner["post_user_fk"] != user["user_pk"] and user["user_role"] != "admin":
            raise Exception(dictionary.not_allowed[lan], 403)
        cursor.execute("UPDATE posts SET post_message = %s WHERE post_pk = %s", (message, post_pk))
        db.commit()
        return jsonify({"status": "ok", "message": dictionary.post_updated[lan]})
    except Exception as ex:
        if "db" in locals():
            db.rollback()
        msg = ex.args[0] if ex.args else "System under maintenance"
        status = ex.args[1] if len(ex.args) > 1 else 500
        return jsonify({"status": "error", "message": msg}), status
    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()


@app.delete("/api/posts/<post_pk>")
def delete_post(post_pk):
    lan = set_language()
    user = session.get("user")
    if not user or user.get("user_blocked_at", 0):
        return jsonify({"status": "error", "message": "Login required"}), 401
    try:
        post_pk = x.validate_uuid(post_pk, "post", lan)
        db, cursor = x.db()
        cursor.execute("SELECT post_user_fk FROM posts WHERE post_pk = %s", (post_pk,))
        owner = cursor.fetchone()
        if not owner:
            raise Exception(dictionary.post_not_found[lan], 404)
        if owner["post_user_fk"] != user["user_pk"] and user["user_role"] != "admin":
            raise Exception(dictionary.not_allowed[lan], 403)
        cursor.execute("DELETE FROM comments WHERE comment_post_fk = %s", (post_pk,))
        cursor.execute("DELETE FROM post_likes WHERE like_post_fk = %s", (post_pk,))
        cursor.execute("DELETE FROM posts WHERE post_pk = %s", (post_pk,))
        db.commit()
        return jsonify({"status": "ok", "message": dictionary.post_deleted[lan]})
    except Exception as ex:
        if "db" in locals():
            db.rollback()
        msg = ex.args[0] if ex.args else "System under maintenance"
        status = ex.args[1] if len(ex.args) > 1 else 500
        return jsonify({"status": "error", "message": msg}), status
    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()


@app.post("/api/posts/<post_pk>/like")
def toggle_like(post_pk):
    lan = set_language()
    user = session.get("user")
    if not user or user.get("user_blocked_at", 0):
        return jsonify({"status": "error", "message": "Login required"}), 401
    try:
        post_pk = x.validate_uuid(post_pk, "post", lan)
        db, cursor = x.db()
        cursor.execute("SELECT like_pk FROM post_likes WHERE like_post_fk = %s AND like_user_fk = %s", (post_pk, user["user_pk"]))
        existing = cursor.fetchone()
        if existing:
            cursor.execute("DELETE FROM post_likes WHERE like_pk = %s", (existing["like_pk"],))
            liked = False
        else:
            cursor.execute("INSERT INTO post_likes (like_pk, like_post_fk, like_user_fk, like_created_at) VALUES (%s, %s, %s, %s)", (uuid.uuid4().hex, post_pk, user["user_pk"], int(time.time())))
            liked = True
        cursor.execute("SELECT COUNT(*) AS total FROM post_likes WHERE like_post_fk = %s", (post_pk,))
        total = cursor.fetchone()["total"]
        cursor.execute("UPDATE posts SET post_total_likes = %s WHERE post_pk = %s", (total, post_pk))
        db.commit()
        return jsonify({"status": "ok", "liked": liked, "likes": total})
    except Exception as ex:
        if "db" in locals():
            db.rollback()
        msg = ex.args[0] if ex.args else "System under maintenance"
        status = ex.args[1] if len(ex.args) > 1 else 500
        return jsonify({"status": "error", "message": msg}), status
    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()


##############################
# COMMENTS
##############################
@app.post("/api/posts/<post_pk>/comment")
def add_comment(post_pk):
    lan = set_language()
    user = session.get("user")
    if not user or user.get("user_blocked_at", 0):
        return jsonify({"status": "error", "message": "Login required"}), 401
    try:
        post_pk = x.validate_uuid(post_pk, "post", lan)
        comment = x.validate_comment(lan)
        comment_pk = uuid.uuid4().hex
        db, cursor = x.db()
        cursor.execute(
            "INSERT INTO comments (comment_pk, comment_post_fk, comment_user_fk, comment_body, comment_created_at) VALUES (%s, %s, %s, %s, %s)",
            (comment_pk, post_pk, user["user_pk"], comment, int(time.time())),
        )
        db.commit()
        cursor.execute(
            """
            SELECT c.*, u.user_username, u.user_first_name, u.user_avatar_path
            FROM comments c JOIN users u ON u.user_pk = c.comment_user_fk WHERE c.comment_pk = %s
            """,
            (comment_pk,),
        )
        comment_row = cursor.fetchone()
        html = render_template("components/comment.html", comment=comment_row, session_user=user)
        return jsonify({"status": "ok", "html": html, "post_pk": post_pk})
    except Exception as ex:
        if "db" in locals():
            db.rollback()
        msg = ex.args[0] if ex.args else "System under maintenance"
        status = ex.args[1] if len(ex.args) > 1 else 500
        return jsonify({"status": "error", "message": msg}), status
    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()


@app.delete("/api/comments/<comment_pk>")
def delete_comment(comment_pk):
    lan = set_language()
    user = session.get("user")
    if not user or user.get("user_blocked_at", 0):
        return jsonify({"status": "error", "message": "Login required"}), 401
    try:
        comment_pk = x.validate_uuid(comment_pk, "comment", lan)
        db, cursor = x.db()
        cursor.execute("SELECT comment_user_fk, comment_post_fk FROM comments WHERE comment_pk = %s", (comment_pk,))
        row = cursor.fetchone()
        if not row:
            raise Exception(dictionary.comment_not_found[lan], 404)
        if row["comment_user_fk"] != user["user_pk"] and user["user_role"] != "admin":
            raise Exception(dictionary.not_allowed[lan], 403)
        cursor.execute("DELETE FROM comments WHERE comment_pk = %s", (comment_pk,))
        db.commit()
        return jsonify({"status": "ok", "post_pk": row["comment_post_fk"]})
    except Exception as ex:
        if "db" in locals():
            db.rollback()
        msg = ex.args[0] if ex.args else "System under maintenance"
        status = ex.args[1] if len(ex.args) > 1 else 500
        return jsonify({"status": "error", "message": msg}), status
    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()


##############################
# FOLLOW
##############################
@app.post("/api/follow/<user_pk>")
def toggle_follow(user_pk):
    lan = set_language()
    user = session.get("user")
    if not user or user.get("user_blocked_at", 0):
        return jsonify({"status": "error", "message": "Login required"}), 401
    try:
        target_pk = x.validate_uuid(user_pk, "user", lan)
        if target_pk == user["user_pk"]:
            raise Exception(dictionary.not_allowed[lan], 403)
        db, cursor = x.db()
        cursor.execute("SELECT follow_pk FROM follows WHERE follow_follower_fk = %s AND follow_following_fk = %s", (user["user_pk"], target_pk))
        existing = cursor.fetchone()
        if existing:
            cursor.execute("DELETE FROM follows WHERE follow_pk = %s", (existing["follow_pk"],))
            following = False
        else:
            cursor.execute("INSERT INTO follows (follow_pk, follow_follower_fk, follow_following_fk, follow_created_at) VALUES (%s, %s, %s, %s)", (uuid.uuid4().hex, user["user_pk"], target_pk, int(time.time())))
            following = True
        db.commit()
        return jsonify({"status": "ok", "following": following})
    except Exception as ex:
        if "db" in locals():
            db.rollback()
        msg = ex.args[0] if ex.args else "System under maintenance"
        status = ex.args[1] if len(ex.args) > 1 else 500
        return jsonify({"status": "error", "message": msg}), status
    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()


##############################
# PROFILE
##############################
@app.post("/api/profile")
def update_profile():
    lan = set_language()
    user = session.get("user")
    if not user or user.get("user_blocked_at", 0):
        return jsonify({"status": "error", "message": "Login required"}), 401
    try:
        email = x.validate_user_email(lan)
        username = x.validate_user_username(lan)
        first_name = x.validate_user_first_name(lan)
        last_name = x.validate_user_last_name(lan)
        bio = request.form.get("bio", "").strip()[:160]
        db, cursor = x.db()
        cursor.execute(
            "UPDATE users SET user_email = %s, user_username = %s, user_first_name = %s, user_last_name = %s, user_bio = %s WHERE user_pk = %s",
            (email, username, first_name, last_name, bio, user["user_pk"]),
        )
        db.commit()
        session["user"].update(
            {
                "user_email": email,
                "user_username": username,
                "user_first_name": first_name,
                "user_last_name": last_name,
                "user_bio": bio,
            }
        )
        return jsonify({"status": "ok", "message": dictionary.profile_updated[lan]})
    except Exception as ex:
        if "db" in locals():
            db.rollback()
        msg = ex.args[0] if ex.args else "System under maintenance"
        if "Duplicate entry" in str(ex):
            msg = dictionary.email_taken[lan] if "user_email" in str(ex) else dictionary.username_taken[lan]
        status = ex.args[1] if len(ex.args) > 1 else 500
        return jsonify({"status": "error", "message": msg}), status
    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()

# Profile page
@app.get("/profile")
def profile():
    lan = set_language()
    user = session.get("user")
    if not user or user.get("user_blocked_at", 0):
        return redirect(url_for("view_login"))
    return render_template("profile.html", lan=lan, user=user)


@app.post("/api/profile/avatar")
def update_avatar():
    lan = set_language()
    user = session.get("user")
    if not user or user.get("user_blocked_at", 0):
        return jsonify({"status": "error", "message": "Login required"}), 401
    try:
        avatar = request.files.get("avatar")
        path = x.save_upload(avatar, x.UPLOAD_AVATAR_FOLDER, {"png", "jpg", "jpeg", "webp", "gif"}, "avatar")
        if not path:
            raise Exception(dictionary.invalid_avatar[lan], 400)
        db, cursor = x.db()
        cursor.execute("UPDATE users SET user_avatar_path = %s WHERE user_pk = %s", (path, user["user_pk"]))
        db.commit()
        session["user"]["user_avatar_path"] = path
        return jsonify({"status": "ok", "avatar": f"/{path}"})
    except Exception as ex:
        if "db" in locals():
            db.rollback()
        msg = ex.args[0] if ex.args else "System under maintenance"
        status = ex.args[1] if len(ex.args) > 1 else 500
        return jsonify({"status": "error", "message": msg}), status
    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()


@app.post("/api/delete-account")
def delete_account():
    lan = set_language()
    user = session.get("user")
    if not user or user.get("user_blocked_at", 0):
        return jsonify({"status": "error", "message": "Login required"}), 401
    try:
        db, cursor = x.db()
        cursor.execute("DELETE FROM comments WHERE comment_user_fk = %s", (user["user_pk"],))
        cursor.execute("DELETE FROM post_likes WHERE like_user_fk = %s", (user["user_pk"],))
        cursor.execute("DELETE FROM follows WHERE follow_follower_fk = %s OR follow_following_fk = %s", (user["user_pk"], user["user_pk"]))
        cursor.execute("DELETE FROM posts WHERE post_user_fk = %s", (user["user_pk"],))
        cursor.execute("DELETE FROM users WHERE user_pk = %s", (user["user_pk"],))
        db.commit()
        session.clear()
        return jsonify({"status": "ok", "redirect": url_for("index")})
    except Exception as ex:
        if "db" in locals():
            db.rollback()
        msg = ex.args[0] if ex.args else "System under maintenance"
        status = ex.args[1] if len(ex.args) > 1 else 500
        return jsonify({"status": "error", "message": msg}), status
    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()


##############################
# SEARCH
##############################
@app.post("/api/search")
def api_search():
    lan = set_language()
    user = session.get("user")
    if not user or user.get("user_blocked_at", 0):
        return jsonify({"status": "error", "message": "Login required"}), 401
    try:
        search_for = request.form.get("search_for", "").strip()
        if len(search_for) < 2:
            raise Exception(dictionary.invalid_search[lan], 400)
        like_term = f"%{search_for}%"
        db, cursor = x.db()
        cursor.execute(
            "SELECT user_pk, user_username, user_first_name, user_last_name, user_avatar_path FROM users WHERE (user_username LIKE %s OR user_first_name LIKE %s OR user_last_name LIKE %s) AND user_blocked_at = 0 LIMIT 10",
            (like_term, like_term, like_term),
        )
        users = cursor.fetchall()
        cursor.execute(
            """
            SELECT p.post_pk, p.post_message, u.user_username, u.user_first_name, u.user_avatar_path
            FROM posts p JOIN users u ON u.user_pk = p.post_user_fk
            WHERE p.post_message LIKE %s AND p.post_blocked_at = 0
            LIMIT 10
            """,
            (like_term,),
        )
        posts = cursor.fetchall()
        return jsonify({"status": "ok", "users": users, "posts": posts})
    except Exception as ex:
        msg = ex.args[0] if ex.args else "System under maintenance"
        status = ex.args[1] if len(ex.args) > 1 else 500
        return jsonify({"status": "error", "message": msg}), status
    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()


##############################
# ADMIN
##############################
@app.get("/admin")
def admin_home():
    user = session.get("user")
    if not user or user.get("user_role") != "admin":
        return redirect(url_for("view_login"))
    lan = set_language()
    try:
        db, cursor = x.db()
        cursor.execute("SELECT * FROM users ORDER BY user_created_at DESC")
        users = cursor.fetchall()
        cursor.execute("SELECT * FROM posts ORDER BY post_created_at DESC LIMIT 50")
        posts = cursor.fetchall()
        return render_template("admin.html", users=users, posts=posts, lan=lan)
    except Exception as ex:
        print("ADMIN ERROR", ex, flush=True)
        return "System under maintenance", 500
    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()


@app.post("/admin/block-user")
def block_user():
    lan = set_language()
    user = session.get("user")
    if not user or user.get("user_role") != "admin":
        return jsonify({"status": "error", "message": "Admin only"}), 403
    try:
        target = x.validate_uuid(request.form.get("user_pk", ""), "user", lan)
        action = request.form.get("action", "block")
        blocked_at = int(time.time()) if action == "block" else 0
        db, cursor = x.db()
        cursor.execute("UPDATE users SET user_blocked_at = %s WHERE user_pk = %s", (blocked_at, target))
        db.commit()
        cursor.execute("SELECT user_email FROM users WHERE user_pk = %s", (target,))
        row = cursor.fetchone()
        if row:
            status_text = "blocked" if action == "block" else "unblocked"
            body = render_template("_email_block_notice.html", status=status_text)
            x.send_email(row["user_email"], "Account status updated", body)
        return jsonify({"status": "ok", "blocked_at": blocked_at})
    except Exception as ex:
        if "db" in locals():
            db.rollback()
        msg = ex.args[0] if ex.args else "System under maintenance"
        status = ex.args[1] if len(ex.args) > 1 else 500
        return jsonify({"status": "error", "message": msg}), status
    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()


@app.post("/admin/block-post")
def block_post():
    lan = set_language()
    user = session.get("user")
    if not user or user.get("user_role") != "admin":
        return jsonify({"status": "error", "message": "Admin only"}), 403
    try:
        post_pk = x.validate_uuid(request.form.get("post_pk", ""), "post", lan)
        action = request.form.get("action", "block")
        blocked_at = int(time.time()) if action == "block" else 0
        db, cursor = x.db()
        cursor.execute("UPDATE posts SET post_blocked_at = %s WHERE post_pk = %s", (blocked_at, post_pk))
        db.commit()
        cursor.execute(
            "SELECT u.user_email FROM posts p JOIN users u ON u.user_pk = p.post_user_fk WHERE p.post_pk = %s",
            (post_pk,),
        )
        row = cursor.fetchone()
        if row:
            status_text = "blocked" if action == "block" else "unblocked"
            body = render_template("_email_block_notice.html", status=status_text)
            x.send_email(row["user_email"], "Post status updated", body)
        return jsonify({"status": "ok", "blocked_at": blocked_at})
    except Exception as ex:
        if "db" in locals():
            db.rollback()
        msg = ex.args[0] if ex.args else "System under maintenance"
        status = ex.args[1] if len(ex.args) > 1 else 500
        return jsonify({"status": "error", "message": msg}), status
    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()


@app.get("/admin/sync-languages")
def sync_languages():
    user = session.get("user")
    if not user or user.get("user_role") != "admin":
        return jsonify({"status": "error", "message": "Admin only"}), 403
    try:
        sheet_key = os.getenv("GOOGLE_SHEET_KEY", "")
        if not sheet_key:
            raise Exception("Missing GOOGLE_SHEET_KEY", 400)
        url = f"https://docs.google.com/spreadsheets/d/{sheet_key}/export?format=csv&id={sheet_key}"
        res = requests.get(url=url)
        csv_text = res.content.decode("utf-8")
        csv_file = io.StringIO(csv_text)
        reader = csv.DictReader(csv_file)
        data = {}
        for row in reader:
            data[row["key"]] = {
                "english": row.get("english", ""),
                "danish": row.get("danish", ""),
                "spanish": row.get("spanish", ""),
            }
        with open("dictionary.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2))
        return jsonify({"status": "ok", "message": "Dictionary synced"})
    except Exception as ex:
        msg = ex.args[0] if ex.args else "System under maintenance"
        status = ex.args[1] if len(ex.args) > 1 else 500
        return jsonify({"status": "error", "message": msg}), status


##############################
# MAIN
##############################
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
