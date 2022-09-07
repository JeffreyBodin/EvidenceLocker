import time
import secrets
import werkzeug.security
import pyotp
from hmac import compare_digest

from evidencelocker.decorators.lazy import lazy
from evidencelocker.helpers.b36 import *
from evidencelocker.helpers.countries import COUNTRY_CODES
from evidencelocker.helpers.hashes import *

from flask import *

class b36ids():

    @property
    def b36id(self):
        return base36encode(self.id)
    

class time_mixin():

    @property
    @lazy
    def created_string(self):
        return f'{time.strftime("%d %B %Y at %H:%M:%S", time.gmtime(self.created_utc))} UTC'

    @property
    @lazy
    def created_iso(self):
        return time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(self.created_utc))

    @property
    @lazy
    def created_date(self):
        return f'{time.strftime("%d %B %Y", time.gmtime(self.created_utc))} UTC'
    
    @property
    def age(self):
        return int(time.time()) - self.created_utc

class user_mixin():

    @property
    def is_banned(self):
        return bool(self.banned_utc)

    @property
    def csrf_token(self):

        if "session_id" not in session:
            session["session_id"]=secrets.token_hex(16)

        msg = f"{session['session_id']}+{self.type_id}+{self.login_nonce}"

        return generate_hash(msg)

    def validate_csrf_token(self, token):
        return validate_hash(f"{session['session_id']}+{self.type_id}+{self.login_nonce}", token)

    def validate_password(self, x):
        return werkzeug.security.check_password_hash(self.pw_hash, x)

    def validate_otp(self, x, allow_reset=False):

        if not self.otp_secret:
            return True

        if x==self.last_otp_code:
            return False
            
        totp=pyotp.TOTP(self.otp_secret)
        if totp.verify(x, valid_window=1):
            self.last_otp_code=x
            g.db.add(self)
            g.db.commit()
            return True
        elif allow_reset and compare_digest(x.replace(' ','').upper(), self.otp_secret_reset_code):
            self.otp_secret==None
            self.last_otp_code=None
            g.db.add(self)
            g.db.commit()
            return True
        return False

    @property
    def otp_secret_reset_code(self):

        return compute_otp_recovery_code(self, self.otp_secret)

class json_mixin():

    @property
    def json_core(self):

        disallowed_values=[
            'login_nonce',
            'otp_secret',
            'pw_hash',
            '_lazy'
            ]  

        data = {x: self.__dict__[x] for x in self.__dict__ if x not in disallowed_values}

        for entry in [x for x in data.keys()]:
            if type(data[entry]) not in [str, int, type(None)]:
                data.pop(entry)

        if "id" in data:
            data["id"]=self.b36id

        return data

    @property
    def json(self):
        return self.json_core
    
    
    @property
    def jsonlink(self):
        return f"{self.permalink}.json"
    

class country_mixin():

    @property
    def country(self):
        return COUNTRY_CODES.get(self.country_code.upper())

class lazy_mixin():

    def clear_cache(self, *args):

        if not args:
            self._lazy={}
            return

        for arg in args:
            self._lazy.pop(arg, None)