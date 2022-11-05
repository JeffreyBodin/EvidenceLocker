import bleach
import mistletoe
import pyotp
from werkzeug.utils import safe_join

from evidencelocker.decorators.auth import *
from evidencelocker.helpers.text import raw_to_html
from evidencelocker.helpers.countries import COUNTRY_CODES

from evidencelocker.__main__ import app


@app.get("/settings")
@logged_in_victim
def get_settings():
    return redirect("/settings/profile")


@app.get("/settings/<page>")
@logged_in_victim
def get_settings_page(page):

    return render_template(
        f"{safe_join('settings/', page)}.html"
        )

@app.post("/settings/<page>")
@logged_in_victim
def post_settings_page(page):

    if page=="profile":


        g.user.name=request.form.get("name") or g.user.name

        if request.form.get("country_code")!=g.user.country_code:
            if request.form.get("country_code") not in COUNTRY_CODES:
                return jsonify({"error":"Invalid country selection"}), 400
            g.user.allow_leo_sharing=False
            g.user.country_code=request.form.get("country_code") or g.user.country_code

    elif page=="security":
        


        if request.form.get("function")=="pw_reset":

            if not g.user.validate_password(request.form.get("password")) or not g.user.validate_otp(request.form.get("otp_code")):
                return jsonify({'error':'Invalid password or two-factor code.'}), 401

            if request.form.get("new_pw") != request.form.get("confirm_pw"):
                return jsonify({'error': "Passwords don't match"}), 400

            g.user.pw_hash = werkzeug.security.generate_password_hash(request.form.get("password"))

        elif request.form.get("function")=="otp_reset":

            if not g.user.validate_password(request.form.get("password")) or not g.user.validate_otp(request.form.get("otp_code"), allow_reset=True):
                return jsonify({'error':'Invalid password or two-factor code.'}), 401

            g.user.otp_secret=None
            g.db.add(g.user)
            g.db.commit()
            return redirect("/set_otp")

    elif page=="sharing":

        if request.form.get("function")=="toggle_sharing":
            g.user.allow_leo_sharing=bool(request.form.get("allow_sharing", False))

        elif request.form.get("function")=="revoke_public":
            g.user.public_link_nonce +=1
            g.db.add(g.user)
            g.db.commit()
            return jsonify({"message":"Public links revoked"})

    else:
        abort(404)

    g.db.add(g.user)
    g.db.commit()

    return jsonify({"message": "Settings updated"})