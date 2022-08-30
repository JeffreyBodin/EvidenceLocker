from flask import *

from evidencelocker.helpers.loaders import *

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
            
        resp = make_response(f(*args, **kwargs))
        resp.headers['Cache-Control'] = "private"
        return resp
    
    wrapper.__name__=f.__name__
    return wrapper
        
def logged_in_police(f):

    def wrapper(*args, **kwargs):

        if not session.get("uid"):
            abort(401)
    
        if session.get("utype") != "p":
            abort(403)

        #24hr automatic timeout for police
        if g.time - session.get("last_request",0) > 86400: #60*60*24
            abort(401)
            
        g.user = get_police_by_id(session.get("uid"))

        if not g.user.otp_secret and request.path != "/set_otp" and not request.path.startswith("/otp_secret_qr/"):
            return redirect("/set_otp")

        if not g.user.is_recently_verified and request.path !="/verify_email":
            return redirect("/verify_email")

        if g.user.banned_utc:
            return render_template('banned.html'), 403
        
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
        elif utype=="p" and g.time-session.get("last_request",0)<86400:
            g.user = get_police_by_id(uid)
        elif utype=="a":
            g.user = get_admin_by_id(uid)
        else:
            abort(401)

        if not g.user.otp_secret and request.path not in ["/set_otp","/verify_email"] and not request.path.startswith("/otp_secret_qr/"):
            return redirect("/set_otp")

        if g.user.type_id.startswith('p') and not g.user.is_recently_verified and request.path not in ["/set_otp","/verify_email"] and not request.path.startswith("/otp_secret_qr/"):
            return redirect("/verify_email")

        if g.user.banned_utc:
            return render_template('banned.html'), 403

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

        if g.user and g.user.type_id.startswith('p') and not g.user.is_recently_verified and request.path not in ["/set_otp","/verify_email"] and not request.path.startswith("/otp_secret_qr/"):
            return redirect("/verify_email")

        if g.user and g.user.banned_utc:
            return render_template('banned.html'), 403

        resp = make_response(f(*args, **kwargs))
        resp.headers['Cache-Control'] = "private" if g.user else "public"
        return resp

    wrapper.__name__=f.__name__
    return wrapper

def not_banned(f):
    """Always use authentication wrapper above this one"""
    
    def wrapper(*args, **kwargs):
        
        if g.user.is_banned:
            return render_template("banned.html"), 403
        
        return f(*args, **kwargs)
    
    wrapper.__name__=f.__name__
    return wrapper


def validate_csrf_token(f):
    """Always use authentication wrapper above this one"""

    def wrapper(*args, **kwargs):

        submitted_key = request.values.get("csrf_token", "none")

        if not g.user.validate_csrf_token(submitted_key):
            abort(401)

        return f(*args, **kwargs)

    wrapper.__name__ = f.__name__
    wrapper.__doc__ = f.__doc__
    return wrapper