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
@logged_in_any
def get_locker_username_certificate(username):

    target_user=get_victim_by_username(username)

    if not target_user.can_be_viewed_by_user(g.user):
        abort(404)

    if request.path.endswith(".py"):
        resp = make_response(str(target_user.public_key))
    elif request.path.endswith(".pem"):
        resp = make_response(target_user.public_key.save_pkcs1())

    resp.headers["Content-Type"] = "text/plain"

    return resp

@app.get("/locker")
@logged_in_police
def get_lockers_leo():

    if g.user.agency.country_code in RESTRICTED_COUNTRIES:
        victims = g.db.query(VictimUser).filter(
            VictimUser.id.in_(
                    g.db.query(LockerShare.victim_id).filter(LockerShare.agency_id==g.user.agency_id).subquery()
                )
            ).all()

    else:

        victims = g.db.query(VictimUser).filter(
            or_(
                and_(
                    VictimUser.country_code==g.user.agency.country_code,
                    VictimUser.allow_leo_sharing==True
                    ),
                VictimUser.id.in_(
                    g.db.query(LockerShare.victim_id).filter(LockerShare.agency_id==g.user.agency_id).subquery()
                    )
                )
            ).all()

    return render_template(
        "police_home.html",
        listing=victims
        )