from flask import Flask, render_template, session, redirect, request, url_for, flash, jsonify
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import Python3Lexer
from pygments.styles import get_all_styles
from utils import take_screenshot_from_url
from os import environ as env
from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv

import csv
import base64
import requests
import json

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

user_info_dict = {}

PLACEHOLDER_CODE = ""
DEFAULT_STYLE = "github-dark"
NO_CODE_FALLBACK = "# No Code Entered"

def save_into_csv():
    with open('information.csv', mode='w', newline='') as file:
        fieldnames = ['email', 'given_name', 'family_name', 'nickname', 'picture']
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        for email, userinfo in user_info_dict.items():
            writer.writerow({
                'email': email,
                'given_name': userinfo.get('given_name', ''),
                'family_name': userinfo.get('family_name', ''),
                'nickname': userinfo.get('nickname', ''),
                'picture': userinfo.get('picture', '')
            })

@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    userinfo = token.get('userinfo', {})
    email = userinfo.get('email')
    
    if email:
        user_info_dict[email] = userinfo
    else:
       None
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("code", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

@app.route("/", methods=["GET"])
def code():
    user = session.get("user")
    if user:
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
    else:
        return render_template("form.html", session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4))

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
    
    if not image_bytes:
        flash("Failed to download image!", "error")
        return render_template("image.html", message="Failed to take screenshot!")

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    
    context = {
        "message": "Done! 🎉",
        "image_b64": base64.b64encode(image_bytes).decode("utf-8"),
    }
    
    flash("Image downloaded successfully", "success")
    return render_template("image.html", **context)

@app.route("/load_github_file", methods=["POST"])
def load_github_file():
    github_url = request.form.get("github_url")
    if github_url:

        if "github.com" in github_url and "/blob/" in github_url:
            raw_url = github_url.replace("github.com","raw.githubusercontent.com").replace("/blob/", "/")
        
            try:
                response = requests.get(raw_url)
                response.raise_for_status()
                session["code"] = response.text
            except requests.RequestException as e:
                flash("Failed to load the file", "danger")
        else:

            try:
                response = requests.get(github_url)
                response.raise_for_status()
                session["code"] = response.text
            except requests.RequestException as e:
                flash("Failed to load the file", "danger")
    
    else:
        flash("GitHub URL cannot be empty.", "danger")
    return redirect(url_for("code"))

@app.route('/logs', methods=["GET"])
def data():
    return jsonify(user_info_dict), 200

@app.route('/logs', methods=['DELETE'])
def delete():
    user_info_dict.clear()
    return jsonify({"message": "All user information deleted."}), 200

@app.route('/logs/export', methods=["GET"])
def export():
    save_into_csv()
    return jsonify({"message": "User information exported to CSV."}), 200

if __name__ == '__main__':
        app.run(host="0.0.0.0", port=env.get("PORT", 3000))


