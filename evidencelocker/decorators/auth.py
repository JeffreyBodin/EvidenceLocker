from flask import *

from evidencelocker.helpers.loaders import *
from evidencelocker.helpers.debug import debug


#this isn't a wrapper; it's just called by them
def validate_csrf_token():

    if request.method not in ["POST", "PUT", "PATCH", "DELETE"]:
        debug("req does not need csrf")
        return

    submitted_key = request.values.get("csrf_token", "none")

    #logged in users
    if g.user:
        if not g.user.validate_csrf_token(submitted_key):
            debug('logged in user, failed token')
            abort(401)

    else:
        #logged out users
        t=int(request.values.get("time", 0))

        if g.time-t > 3600:
            debug('logged out user, token expired')
            abort(401)

        if not validate_hash(f"{t}+{session['session_id']}", token):
            debug('logged out user, invalid token')
            abort(401)

    debug("successful csrf")

def logged_in_victim(f):

    def wrapper(*args, **kwargs):

        if not session.get("uid"):
            abort(401)
    
        if session.get("utype") != "v":
            abort(403)

        #1hr automatic timeout for victims
        if g.time - session.get("last_request",0) > 3600:
            abort(401)
            
        g.user = get_victim_by_id(session.get("uid"))

        if not g.user.otp_secret and request.path != "/set_otp" and not request.path.startswith("/otp_secret_qr/"):
            return redirect("/set_otp")

        if g.user.banned_utc:
            return render_template('banned.html'), 403

        validate_csrf_token()

        resp = make_response(f(*args, **kwargs))
        resp.headers['Cache-Control'] = "private"
        return resp
    
    wrapper.__name__=f.__name__
    return wrapper

def logged_in_admin(f):

    def wrapper(*args, **kwargs):

        if not session.get("uid"):
            abort(401)

        if session.get("utype") != "a":
            abort(403)

        g.user=get_admin_by_id(session.get("uid"))

        if not g.user.otp_secret and request.path != "/set_otp" and not request.path.startswith("/otp_secret_qr/"):
            return redirect("/set_otp")

        if g.user.banned_utc:
            return render_template('banned.html'), 403

        validate_csrf_token()

        resp = make_response(f(*args, **kwargs))
        resp.headers['Cache-Control'] = "private"
        return resp

    wrapper.__name__=f.__name__
    return wrapper

def logged_in_any(f):

    def wrapper(*args, **kwargs):

        if not session.get("uid"):
            abort(401)

        utype=session.get("utype")
        uid=session.get("uid")

        # timeouts
        if utype=="v" and g.time-session.get("last_request",0)<3600:
            g.user = get_victim_by_id(uid)
        elif utype=="a":
            g.user = get_admin_by_id(uid)
        else:
            abort(401)

        if not g.user.otp_secret and request.path not in ["/set_otp","/verify_email"] and not request.path.startswith("/otp_secret_qr/"):
            return redirect("/set_otp")

        if g.user.banned_utc:
            return render_template('banned.html'), 403

        validate_csrf_token()

        resp = make_response(f(*args, **kwargs))
        resp.headers['Cache-Control'] = "private"
        return resp

    wrapper.__name__=f.__name__
    return wrapper

def logged_in_desired(f):

    def wrapper(*args, **kwargs):

        utype=session.get("utype")
        uid=session.get("uid")

        if utype=="v":
            g.user = get_victim_by_id(uid)
        elif utype=="p":
            g.user = get_police_by_id(uid)
        elif utype=="a":
            g.user = get_admin_by_id(uid)
        else:
            g.user=None

        if g.user and not g.user.otp_secret and request.path not in ["/set_otp","/verify_email"] and not request.path.startswith("/otp_secret_qr/"):
            return redirect("/set_otp")

        if g.user and g.user.banned_utc:
            return render_template('banned.html'), 403

        validate_csrf_token()

        resp = make_response(f(*args, **kwargs))
        resp.headers['Cache-Control'] = "private" if g.user else "public"
        return resp

    wrapper.__name__=f.__name__
    return wrapper