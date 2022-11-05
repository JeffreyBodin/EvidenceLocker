from sqlalchemy import *
from sqlalchemy.orm import relationship, lazyload, deferred
from sqlalchemy.ext.associationproxy import association_proxy
import rsa

from .mixins import *

from evidencelocker.helpers.countries import COUNTRY_CODES, RESTRICTED_COUNTRIES
from evidencelocker.helpers.hashes import validate_hash
from evidencelocker.__main__ import Base

class VictimUser(Base, b36ids, time_mixin, user_mixin, json_mixin, country_mixin):

    __tablename__="victim_users"
    
    id          =Column(Integer, primary_key=True)
    username    =Column(String(64), unique=True)
    created_utc =Column(Integer)
    name        =Column(String(128))
    country_code=Column(String(2))
    created_country=Column(String(2))
    pw_hash     =deferred(Column(String(256)))
    otp_secret  =deferred(Column(String(32)))
    email       =Column(String(256), unique=True)
    banned_utc  =Column(Integer, default=0)
    ban_reason  =Column(String(128))
    login_nonce =Column(Integer, default=0)
    allow_leo_sharing = Column(Boolean, default=False)
    last_otp_code = deferred(Column(String(6)))
    public_link_nonce=Column(Integer, default=0)
    _rsa_e      =Column(String(32))
    _rsa_d      =deferred(Column(String(256)))
    _rsa_n      =Column(String(256))
    _rsa_p      =deferred(Column(String(256)))
    _rsa_q      =deferred(Column(String(256)))

    exhibits = relationship("Exhibit", order_by="Exhibit.id.desc()", back_populates="author")

    def __repr__(self):
        return f'<VictimUser(id={self.b36id}, username={self.username})>'
    
    @property
    def type_id(self):
        return f"v{self.id}"

    @property
    def permalink(self):
        return f"/locker/{self.username}"
    
    def can_be_viewed_by_user(self, other):

        if (self.is_banned or (other and other.is_banned)) and not (other and other.type_id.startswith('a')):
            return False

        elif request.args.get("token") and validate_hash(f"{self.id}+{self.public_link_nonce}+{request.path}", request.args.get("token","")):
            return True

        elif not other:
            return False

        elif other is self:
            return True

        elif other.type_id.startswith("v"):
            return False

        elif other.type_id.startswith("a"):
            return True

        elif other.type_id.startswith("p"):

            if not other.is_recently_verified:
                return False
                
            if self.allow_leo_sharing and other.agency.country_code==self.country_code and self.country_code not in RESTRICTED_COUNTRIES:
                return True

            elif other.agency_id in [x.agency_id for x in self.share_records]:
                return True

            return False

        return False

    @property
    def signed_exhibit_count(self):
        return len([x for x in self.exhibits if x.signed_utc])

    @property
    def draft_exhibit_count(self):
        return len([x for x in self.exhibits if not x.signed_utc])
    
    @property
    def json(self):
        data = super().json

        data["exhibits"]=[x.json_core for x in self.exhibits]

        return data

    @property
    def public_key(self):

        if not self._rsa_n:
            self.create_keys()

        return rsa.PublicKey(
            int(self._rsa_n, 16),
            int(self._rsa_e, 16)
            )

    @property
    def private_key(self):

        #This property cannot be accessed unless authenticated as the user
        if g.user != self:
            abort(403)

        if not self._rsa_n:
            self.create_keys()

        return rsa.PrivateKey(
            int(self._rsa_n, 16),
            int(self._rsa_e, 16),
            int(self._rsa_d, 16),
            int(self._rsa_p, 16),
            int(self._rsa_q, 16)
            )
    
    def create_keys(self):
        if self._rsa_n:
            raise RuntimeError(f"User {self} already has keys")

        pub, priv = rsa.newkeys(512)

        self._rsa_n = hex(priv.n)
        self._rsa_e = hex(priv.e)
        self._rsa_d = hex(priv.d)
        self._rsa_p = hex(priv.p)
        self._rsa_q = hex(priv.q)

        g.db.add(self)
        g.db.commit()

    @property
    @lazy
    def pem_cert_permalink(self):
        return f"{self.permalink}/certificate.pem"

    @property
    @lazy
    def py_cert_permalink(self):
        return f"{self.permalink}/certificate.py"