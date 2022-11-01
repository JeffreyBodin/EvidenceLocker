from evidencelocker.decorators.auth import *
from evidencelocker.helpers.text import raw_to_html
from evidencelocker.helpers.countries import RESTRICTED_COUNTRIES

from evidencelocker.classes import *
from evidencelocker.__main__ import app

@app.get("/locker/<username>")
@app.get("/locker/<username>.json")
@logged_in_any
def get_locker_username(username):

    target_user = get_victim_by_username(username)

    if not target_user.can_be_viewed_by_user(g.user):
        abort(404)

    if request.path.endswith('.json'):
        return jsonify(target_user.json)

    return render_template(
        "victim_userpage.html",
        target_user=target_user
        )

@app.get("/locker/<username>/certificate.py")
@app.get("/locker/<username>/certificate.pem")
@logged_in_desired
def get_locker_username_certificate(username):

    target_user=get_victim_by_username(username)

    if not target_user.can_be_viewed_by_user(g.user):
        abort(404)

    if request.path.endswith(".py"):
        resp = make_response("rsa."+str(target_user.public_key))
    elif request.path.endswith(".pem"):
        resp = make_response(target_user.public_key.save_pkcs1())

    resp.headers["Content-Type"] = "text/plain"

    return resp


# @app.get("/locker/<username>/private.py")
# @app.get("/locker/<username>/private.pem")
# @logged_in_victim
# def get_locker_username_private_certificate(username):

#     target_user=get_victim_by_username(username)

#     if g.user != target_user:
#         abort(403)

#     if request.path.endswith(".py"):
#         resp = make_response("rsa."+str(target_user.private_key))
#     elif request.path.endswith(".pem"):
#         resp = make_response(target_user.private_key.save_pkcs1())

#     resp.headers["Content-Type"] = "text/plain"

#     return resp