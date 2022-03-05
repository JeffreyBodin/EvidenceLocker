from flask import *

from evidencelocker.helpers.loaders import *

def logged_in_victim(f):

    def wrapper(*args, **kwargs):

        if not session.get("uid"):
            abort(401)
    
        if session.get("utype") != "v":
            abort(403)
            
        user = get_victim_by_id(session.get("uid"))
            
        return f(user, *args, **kwargs)
    
    wrapper.__name__=f.__name__
    return wrapper
        
def logged_in_police(f):

    def wrapper(*args, **kwargs):

        if not session.get("uid"):
            abort(401)
    
        if session.get("utype") != "p":
            abort(403)
            
        user = get_police_by_id(session.get("uid"))
            
        return f(user, *args, **kwargs)
    
    wrapper.__name__=f.__name__
    return wrapper

def logged_in_admin(f):

    def wrapper(*args, **kwargs):

        if not session.get("uid"):
            abort(401)

        if session.get("utype") != "a":
            abort(403)

        user=get_admin_by_id(session.get("uid"))

        return f(user, *args, **kwargs)

    wrapper.__name__=f.__name__
    return wrapper

def logged_in_any(f):

    def wrapper(*args, **kwargs):

        if not session.get("uid"):
            abort(401)

        utype=session.get("utype")
        uid=session.get("uid")

        if utype=="v":
            user = get_victim_by_id(uid)
        elif utype=="p":
            user = get_police_by_id(uid)
        elif utype=="a":
            user = get_admin_by_id(uid)

        return f(user, *args, **kwargs)

    wrapper.__name__=f.__name__
    return wrapper



def not_banned(f):
    
    def wrapper(*args, **kwargs):
        
        user=args[0]
        
        if user.is_banned:
            abort(403)
        
        return f(*args, **kwargs)
    
    wrapper.__name__=f.__name__
    return wrapper
