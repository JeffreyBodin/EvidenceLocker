import io
import pyotp
import qrcode
import random
import time
import werkzeug.security
import requests
import re

from flask import *

from evidencelocker.helpers.hashes import *
from evidencelocker.decorators.auth import *
from evidencelocker.classes import *
from evidencelocker.helpers.loaders import *
from evidencelocker.helpers.mail import send_email

from evidencelocker.__main__ import app

valid_username_regex = re.compile("^[a-zA-Z0-9_]{5,25}$")
valid_password_regex = re.compile("^.{8,100}$")

@app.post("/login")
def login_victim():

    #define the response for an invalid login attempt
    #Random sleep is to ensure timing analysis cannot be used to deduce which part of the login failed
    def invalid_login_victim(e):
        time.sleep(max(0, random.gauss(1.5, 0.33)))
        return render_template(
            "login_victim.html",
            token=logged_out_csrf_token(),
            error=e
            )

    user = get_victim_by_username(request.form.get("username"), graceful=True)
    if not user:
        return invalid_login_victim("Invalid username, password, or two-factor code")

    if not user.validate_password(request.form.get("password")):
        return invalid_login_victim("Invalid username, password, or two-factor code")

    if not user.validate_otp(request.form.get("otp_code"), allow_reset=True):
        return invalid_login_victim("Invalid username, password, or two-factor code")

    #set cookie and continue to locker
    session["utype"]="v"
    session["uid"]=user.id

    return redirect(user.permalink)

@app.post("/logout")
def logout():

    session.pop("utype")
    session.pop("uid")

    return redirect ("/")


@app.get("/otp_secret_qr/<secret>.png")
@logged_in_any
def mfa_qr(secret):
    x = pyotp.TOTP(secret)
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_L
    )
    issuer_name = request.args.get("issuer","TEL")
    qr.add_data(x.provisioning_uri(g.user.username, issuer_name=issuer_name))
    img = qr.make_image(fill_color="#2589bd", back_color="white")

    mem = io.BytesIO()

    img.save(mem, format="PNG")
    mem.seek(0, 0)
    return send_file(mem, mimetype="image/png", as_attachment=False)

@app.get("/login")
@logged_in_desired
def get_login_victim():

    if g.user:
        return redirect("/")

    return render_template(
        "login_victim.html",
        token=logged_out_csrf_token()
        )

@app.get("/signup")
@logged_in_desired
def get_signup_victim():

    if g.user:
        return redirect("/")
    
    return render_template(
        "signup_victim.html",
        token=logged_out_csrf_token(),
        hcaptcha = app.config["HCAPTCHA_SITEKEY"]
        )

@app.get("/set_otp")
@logged_in_any
def get_set_otp():

    if g.user.otp_secret:
        return redirect("/")

    otp_secret=pyotp.random_base32()
    recovery = compute_otp_recovery_code(g.user, otp_secret)
    recovery=" ".join([recovery[i:i+5] for i in range(0,len(recovery),5)])

    return render_template(
        "set_otp.html",
        otp_secret = otp_secret,
        recovery = recovery,
        )

@app.post("/set_otp")
@logged_in_any
def post_set_otp():
    otp_secret = request.form.get("otp_secret")
    code = request.form.get("otp_code")

    totp = pyotp.TOTP(otp_secret)

    if not werkzeug.security.check_password_hash(g.user.pw_hash, request.form.get("password")):
        return redirect('/set_otp?error=Incorrect%20password')

    if not totp.verify(code):
        return redirect('/set_otp?error=Incorrect%20code')

    g.user.otp_secret=otp_secret
    g.db.add(g.user)
    g.db.commit()

    return redirect("/")


@app.post("/signup")
def post_signup_victim():

    def invalid_signup_victim(error=None):
        return render_template(
            "signup_victim.html",
            token=logged_out_csrf_token(),
            hcaptcha = app.config["HCAPTCHA_SITEKEY"],
            error=error
            )
    
    username=request.form.get("username")
    existing_user=get_victim_by_username(username, graceful=True)

    #basic checks
    if existing_user:
        return invalid_signup_victim("Username already taken.")
        
    if request.form.get("password") != request.form.get("password_confirm"):
        return invalid_signup_victim("Passwords do not match.")

    if request.form.get("terms_agree") != "true":
        return invalid_signup_victim("You must agree to the terms of use.")

    #user/pass regex checks
    if not re.fullmatch(valid_username_regex, username):
        return invalid_signup_victim("Invalid username. Username must be 5-25 characters, using letters, numbers, or _")

    if not re.fullmatch(valid_password_regex, request.form.get("password")):
        return invalid_signup_victim("Invalid password. Passwords must be at least 8 characters long.")
    
    #verify hcaptcha
    token = request.form.get("h-captcha-response")
    if not token:
        abort(400)

    data = {"secret": app.config["HCAPTCHA_SECRET"],
            "response": token,
            "sitekey": app.config["HCAPTCHA_SITEKEY"]}
    url = "https://hcaptcha.com/siteverify"

    x = requests.post(url, data=data)

    if not x.json()["success"]:
        return invalid_signup_victim("hCaptcha verification failed. Please try again.")
    
    #create new vic user
    g.user = VictimUser(
        username=username,
        pw_hash=werkzeug.security.generate_password_hash(request.form.get("password")),
        created_utc=g.time,
        created_country=request.headers.get("cf-ipcountry"),
        country_code=request.headers.get("cf-ipcountry")
    )

    g.db.add(g.user)
    g.db.commit()

    session["utype"]='v'
    session["uid"]=g.user.id

    return redirect("/set_otp")

@app.get("/verify_email")
@logged_in_any
def get_verify_email():

    if not request.args.get("token"):

        return render_template(
            "confirm_email.html"
            )

    t=int(request.args.get('t'))
    if g.time - t > 60 * 60 *24:
        return render_template(
            "confirm_email.html",
            expired=True
            )
    
    if not validate_hash(f"verify_email+{g.user.type_id}+{g.user.email}+{t}", request.args.get('token','')):
        return render_template(
            "confirm_email.html",
            invalid=True
            )

    #(re)confirmation successful
    g.user.last_verified_utc=g.time
    g.db.add(g.user)
    g.db.commit()
    return redirect("/")

@app.post("/verify_email")
@logged_in_any
def post_verify_email():

    if g.user.last_verified_utc:
        subject="Reconfirm your email"
    else:
        subject="Confirm your email"

    token=generate_hash(f"verify_email+{g.user.type_id}+{g.user.email}+{g.time}")

    send_email(
        g.user,
        "police_reconfirm",
        subject=subject,
        link_text="Confirm Email",
        link_url=f"/verify_email?t={g.time}&token={token}"
        )
    
    return render_template("check_your_email.html")

