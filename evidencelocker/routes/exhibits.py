import bleach
import mistletoe
import pyotp
from pprint import pprint, pformat
from io import BytesIO
import magic
import mistletoe
from pprint import pprint

from evidencelocker.decorators.auth import *
from evidencelocker.helpers.text import raw_to_html, bleachify
from evidencelocker.helpers.aws import s3_upload_file, s3_download_file, s3_delete_file
from evidencelocker.helpers.hashes import generate_hash, validate_hash

from evidencelocker.__main__ import app

@app.get("/create_exhibit")
@logged_in_victim
def get_create_exhibit():

    return render_template(
        "create_exhibit.html",
        )

@app.post("/create_exhibit")
@logged_in_victim
def post_create_exhibit():

    title = bleachify(request.form.get("title"))

    body_raw = request.form.get("body").replace('\r', '')

    body_html = raw_to_html(body_raw)

    signed = request.form.get("oath_perjury", False)

    #check for duplicates

    existing = g.db.query(Exhibit).filter_by(
        author_id=g.user.id,
        title=title,
        text_html=body_html).first()

    if existing:    
        return redirect(existing.permalink)

    if signed:
        if not g.user.validate_password(request.form.get("password")) or not g.user.validate_otp(request.form.get("otp_code")):
            return render_template(
                "create_exhibit.html",
                error="Invalid signature",
                title=title,
                body=body_raw
                )

    exhibit = Exhibit(
        text_raw=body_raw,
        text_html=body_html,
        title=title,
        created_utc=g.time,
        author_id=g.user.id,
        created_country = request.headers.get("cf-ipcountry"),
        created_ip  = request.remote_addr
        )


    g.db.add(exhibit)
    g.db.flush()
    g.db.refresh(exhibit)

    #handle attached file
    if request.files.get("file"):
        file=request.files["file"]

        #check file type
        mime = magic.from_buffer(file.read(2048), mime=True)
        if not mime.startswith("image/"):
            return render_template(
                "create_exhibit.html",
                error="Invalid file type, must be image",
                title=title,
                body=body_raw
                )

        exhibit.image_type=mime.split(";")[0].split('/')[1].split('+')[0]
        
        file.seek(0)
        exhibit.image_sha256=hashlib.sha256(file.read()).hexdigest()

        file.seek(0)
        s3_upload_file(exhibit.pic_permalink, file)
        g.db.add(exhibit)


    if signed:
        exhibit.signed_ip = request.remote_addr
        exhibit.signed_country  = request.headers.get("cf-ipcountry")
        exhibit.signed_utc=g.time
        g.db.add(exhibit)
        g.db.commit()
        g.db.refresh(exhibit)
        exhibit.signing_sha256 = exhibit.live_sha256

    g.db.commit()
    return redirect(exhibit.permalink)

@app.get("/locker/<username>/exhibit/<eid>/<anything>")
@app.get("/locker/<username>/exhibit/<eid>/<anything>.json")
@logged_in_any
def get_locker_username_exhibit_eid_anything(username, eid, anything):

    exhibit = get_exhibit_by_id(eid)

    if not exhibit.author.can_be_viewed_by_user(g.user):
        abort(404)

    if username != exhibit.author.username:
        abort(404)

    if request.path != exhibit.permalink and request.path != exhibit.jsonlink:
        return redirect(exhibit.permalink)

    if request.path.endswith(".json"):
        return jsonify(exhibit.json)

    return render_template(
        "exhibit_page.html",
        e=exhibit,
        )

@app.delete("/locker/<username>/exhibit/<eid>/<anything>")
@logged_in_victim
@validate_csrf_token
def delete_locker_username_exhibit_eid_anything(username, eid, anything):
    exhibit = get_exhibit_by_id(eid)

    if exhibit.author != g.user:
        abort(404)

    if username != exhibit.author.username:
        abort(404)

    if exhibit.signed_utc:
        return jsonify({"error":"Cannot delete signed content"}), 403

    if exhibit.image_sha256:
        s3_delete_file(exhibit.pic_permalink)

    g.db.delete(exhibit)
    g.db.commit()
    return jsonify({"redirect":f"/locker/{g.user.username}"}), 302

@app.get("/locker/<username>/exhibits")
@logged_in_victim
def get_locker_username_all_signed_exhibits(username):

    target_user = get_victim_by_username(username)
    if g.user != target_user:
        abort(404)

    exhibits=[e for e in target_user.exhibits if e.signed_utc]

    exhibit_ids=','.join([e.b36id for e in exhibits])

    verification_link=f"/locker/{target_user.username}/exhibits/{exhibit_ids}"

    return render_template(
        "exhibits_all.html",
        target_user=target_user,
        exhibits=exhibits,
        verification_link=verification_link,
        )

@app.get("/locker/<username>/exhibits/<exhibit_ids>")
@logged_in_desired
def get_locker_username_exhibit_verification(username, exhibit_ids):

    target_user=get_victim_by_username(username)

    if not validate_hash(f"{target_user.id}+{target_user.public_link_nonce}+{request.path}", request.args.get("token",'')):
        abort(403)
    
    exhibit_ids=exhibit_ids.split(",")
    exhibits=get_exhibits_by_ids(exhibit_ids)

    if any([e.author_id != target_user.id for e in exhibits]):
        abort(403)

    return render_template(
        "exhibits_all.html",
        target_user=target_user,
        exhibits=exhibits,
        )


@app.post("/locker/<username>/exhibit/<eid>/<anything>")
@logged_in_victim
def post_locker_username_exhibit_eid_anything(username, eid, anything):

    exhibit = get_exhibit_by_id(eid)

    if exhibit.author != g.user:
        abort(404)

    #Exhibits with invalid signatures may be re-signed
    if exhibit.signed_utc and exhibit.sig_valid:
        abort(403)

    elif exhibit.signed_utc and not exhibit.sig_valid:

        signed = request.form.get("oath_perjury", False)
        if not g.user.validate_password(request.form.get("password")) or not g.user.validate_otp(request.form.get("otp_code")):
            return jsonify({"error":"Invalid signature"}), 400

        print(f"old saved sig: {exhibit.signing_sha256}")
        print(f"old live sig:  {exhibit.live_sha256}")

        exhibit.signed_utc = g.time if signed else exhibit.signed_utc
        exhibit.signed_ip = request.remote_addr if signed else None
        exhibit.signed_country = request.headers.get("cf-ipcountry") if signed else None

        exhibit.clear_cache("live_sha256")
        pprint(exhibit.json_for_sig)
        exhibit.signing_sha256 = exhibit.live_sha256 if signed else None



        print(f"new saved sig: {exhibit.signing_sha256}")
        print(f"new live sig:  {exhibit.live_sha256}")

        g.db.add(exhibit)
        g.db.commit()

        return jsonify({"redirect":exhibit.permalink}), 302


    title = bleachify(request.form.get("title"))

    body_raw = request.form.get("body").replace('\r', '')

    body_html = raw_to_html(body_raw)


    #process edits to attached image
    image_action=request.form.get("image_action")
    
    if image_action=="replace":
        if exhibit.image_sha256:
            s3_delete_file(exhibit.pic_permalink)

        file=request.files["file"]

        #check file type
        mime = magic.from_buffer(file.read(2048), mime=True)
        if not mime.startswith("image/"):
            return jsonify({"error":"Invalid file type, must be image"}), 400

        exhibit.image_type=mime.split(";")[0].split('/')[1].split('+')[0]

        file.seek(0)
        exhibit.image_sha256=hashlib.sha256(file.read()).hexdigest()
        file.seek(0)

        #print(exhibit.image_sha256, exhibit.pic_permalink)
        s3_upload_file(exhibit.pic_permalink, file)

    elif image_action=="delete":
        s3_delete_file(exhibit.pic_permalink)
        exhibit.image_sha256=None
        exhibit.image_type=None


    signed = request.form.get("oath_perjury", False)

    if signed:
        if not g.user.validate_password(request.form.get("password")) or not g.user.validate_otp(request.form.get("otp_code")):
            return jsonify({"error":"Invalid signature"}), 400

    edited = (body_raw != exhibit.text_raw) or (title != exhibit.title) or (image_action != None)

    exhibit.edited_utc = g.time if edited else exhibit.edited_utc
    exhibit.edited_ip = request.remote_addr if edited else exhibit.edited_ip
    exhibit.edited_country = request.headers.get("cf-ipcountry") if edited else exhibit.edited_country
    exhibit.signed_utc = g.time if signed else exhibit.signed_utc
    exhibit.signed_ip = request.remote_addr if signed else None
    exhibit.signed_country = request.headers.get("cf-ipcountry") if signed else None
    exhibit.text_raw = body_raw
    exhibit.text_html = body_html
    exhibit.title = title

    exhibit.signing_sha256 = exhibit.live_sha256 if signed else None

    g.db.add(exhibit)
    g.db.commit()

    return jsonify({"redirect":exhibit.permalink}), 302


@app.get("/exhibit_image/<eid>/<digits>.<filetype>")
@logged_in_desired
def get_exhibit_image_eid_png(eid, digits, filetype):

    exhibit = get_exhibit_by_id(eid)

    if not exhibit.author.can_be_viewed_by_user(g.user):
        abort(404)

    if not exhibit.image_sha256:
        abort(404)

    if exhibit.image_sha256[-6:] != digits:
        abort(404)

    if request.path != exhibit.pic_permalink:
        return redirect(request.pic_permalink)

    return send_file(
        s3_download_file(exhibit.pic_permalink),
        mimetype=f"image/{exhibit.image_type}"
        )

@app.get("/locker/<username>/exhibit/<eid>/<anything>/signature")
@logged_in_desired
def get_locker_username_exhibit_eid_anything_signature(username, eid, anything):

    exhibit = get_exhibit_by_id(eid)

    if not exhibit.author.can_be_viewed_by_user(g.user):
        return jsonify({"error": "Exhibit not found"}), 404

    if username != exhibit.author.username:
        return jsonify({"error": "Exhibit not found"}), 404

    if request.path != exhibit.sig_permalink:
        return redirect(exhibit.sig_permalink)

    if not exhibit.signed_utc:
        return jsonify({"error":"Exhibit is not signed"}), 400

    data={
        "json_for_sig": escape(pformat(exhibit.json_for_sig)),
        "live_sha256_with_fresh_image_hash": exhibit.live_sha256_with_fresh_image_hash,
        "signing_sha256": exhibit.signing_sha256,
        "signed_string": exhibit.signed_string,
        "sig_valid": exhibit.sig_valid_with_fresh_image,
        "title": exhibit.title
        }

    if exhibit.image_sha256:
        data.update({
            "pic_permalink": exhibit.pic_permalink
            })

    return jsonify(data)