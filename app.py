from flask import Flask, render_template, session, redirect, request, url_for, flash
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import Python3Lexer
from pygments.styles import get_all_styles
from utils import take_screenshot_from_url

import base64
import requests

app = Flask(__name__)
app.secret_key = "c6298e4547281ec26fff3c05490ea15fcbbf8bb046800ea32a21a0931d057398"


PLACEHOLDER_CODE = "print('Hello, World!')"
DEFAULT_STYLE = "github-dark"
NO_CODE_FALLBACK = "# No Code Entered"

@app.route("/", methods=["GET"])
def code():

    if session.get("code") is None:
        session["code"] = PLACEHOLDER_CODE
    lines = session["code"].split("\n")
    context = {
        "message": "Paste Your Python Code 🐍",
        "code": session["code"],
        "num_lines": len(lines),
        "max_chars": len(max(lines, key=len)),
    }
    return render_template("code_input.html", **context)

@app.route("/save_code", methods=["POST"])
def save_code():
    session["code"] = request.form.get("code") or NO_CODE_FALLBACK
    return redirect(url_for("code"))

@app.route("/reset_session", methods=["POST"])
def reset_session():
    session.clear()
    session["code"] = PLACEHOLDER_CODE
    return redirect(url_for("code"))

@app.route("/style", methods=["GET"])
def style():
    if session.get("style") is None:
        session["style"] = DEFAULT_STYLE
    formatter = HtmlFormatter(style=session["style"])
    context = {
        "message": "Select Your Style 🎨",
        "all_styles": list(get_all_styles()),
        "style_definitions": formatter.get_style_defs(),
        "style_bg_color": formatter.style.background_color,
        "highlighted_code": highlight(
            session["code"], Python3Lexer(), formatter
        ),
    }
    return render_template("style_selection.html", **context)

@app.route("/save_style", methods=["POST"])
def save_style():
    if request.form.get("style") is not None:
        session["style"] = request.form.get("style")
    if request.form.get("code") is not None:
        session["code"] = request.form.get("code") or NO_CODE_FALLBACK
    return redirect(url_for("style"))

@app.route("/image", methods=["GET"])
def image():
    session_data = {
        "name": app.config["SESSION_COOKIE_NAME"],
        "value": request.cookies.get(app.config["SESSION_COOKIE_NAME"]),
        "url": request.host_url,
    }
    target_url = request.host_url + url_for("style")
    image_bytes = take_screenshot_from_url(target_url, session_data)
    context = {
        "message": "Done! 🎉",
        "image_b64": base64.b64encode(image_bytes).decode("utf-8"),
    }
    return render_template("image.html", **context)

@app.route("/load_github_file", methods=["POST"])
def load_github_file():
    github_url = request.form.get("github_url")
    if github_url:
        if "github.com" in github_url and "/blob/" in github_url:
            flash("Please provide a raw GitHub URL. You can follow the tutorial to convert it.", "error")
        else:
            try:
                response = requests.get(github_url)
                response.raise_for_status()
                session["code"] = response.text
                flash("Code loaded successfully from GitHub!", "success")
            except requests.RequestException as e:
                flash(f"Failed to load the file: {e}", "error")
    else:
        flash("GitHub URL cannot be empty.", "error")
    return redirect(url_for("code"))

@app.route("/tutorial_raw", methods=["GET"])
def tutorial_raw():
    return render_template("tut.html")
if __name__ == '__main__':
    app.run(debug=True)


