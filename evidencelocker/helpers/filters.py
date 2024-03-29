import qrcode
import io
import base64
import pprint
from urllib.parse import urlparse, urlunparse

from .hashes import *
from .countries import COUNTRY_CODES, RESTRICTED_COUNTRIES
from evidencelocker.classes import *

from flask import session, g

from evidencelocker.__main__ import app

@app.template_filter('qrcode_img_data')
def qrcode_filter(x):
  
    mem=io.BytesIO()
    qr=qrcode.QRCode()
    qr.add_data(x)
    img=qr.make_image(
        fill_color="#2589bd",
        back_color="white",
    )
    img.save(
        mem, 
        format="PNG"
    )
    mem.seek(0)
    
    data=base64.b64encode(mem.read()).decode('ascii')
    return f"data:image/png;base64,{data}"

@app.template_filter('full_link')
def full_link(x):
    return urlunparse(urlparse(x)._replace(scheme=f"http{ 's' if app.config['FORCE_HTTPS'] else '' }", netloc=app.config['SERVER_NAME']))

@app.template_filter('nonce')
def nonce(x):
    return generate_hash(f"{session.get('session_id')}+{x}")

@app.template_filter("path_token")
def path_token(x, user):
    return generate_hash(f"{user.id}+{user.public_link_nonce}+{x}")

@app.template_filter("add_token_param")
def add_token_param(x, user):
        
    parsed_url=urlparse(x)
    return urlunparse(parsed_url._replace(query=f"token={generate_hash(f'{user.id}+{user.public_link_nonce}+{parsed_url.path}')}"))

@app.template_filter('logged_out_token')
def logged_out_token(x):
    return logged_out_csrf_token()


@app.template_filter('CC')
def country_code_filter(x):

    if not x:
        return COUNTRY_CODES

    else:
        return COUNTRY_CODES.get(x)

@app.template_filter("RCC")
def restricted_country_code_filter(x):
    if not x:
        return RESTRICTED_COUNTRIES

    else:
        return RESTRICTED_COUNTRIES.get(x)

@app.template_filter("agency_count")
def agency_count_filter(x):

    return g.db.query(Agency).filter_by(country_code=x).count()

@app.template_filter('pprint')
def pprint_filter(x):

    return pprint.pformat(x)