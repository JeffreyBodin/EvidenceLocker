import hashlib
import json
from sqlalchemy import *
from sqlalchemy.orm import relationship, lazyload
import re
import werkzeug.security
import rsa

from .mixins import *
from evidencelocker.helpers.aws import s3_download_file

from evidencelocker.decorators.lazy import lazy
from evidencelocker.__main__ import Base


class Exhibit(Base, b36ids, time_mixin, json_mixin, lazy_mixin):

    __tablename__="entries"

    id          =Column(Integer, primary_key=True)
    text_raw    =Column(String(8192))
    text_html   =Column(String(16384))
    title       =Column(String(512))
    created_utc =Column(Integer)
    edited_utc  =Column(Integer, default=None)
    signed_utc  =Column(Integer, default=None)
    author_id   =Column(Integer, ForeignKey("victim_users.id"))
    created_ip  =Column(String(16))
    edited_ip   =Column(String(16))
    signed_ip   =Column(String(16))
    created_country=Column(String(2))
    edited_country=Column(String(2))
    signed_country=Column(String(2))
    signing_sha256 = Column(String(512))
    image_sha256 = Column(String(512), default=None)
    image_type = Column(String(4), default=None)
    rsa_signature = Column(String(256))

    author = relationship("VictimUser", lazy="joined", back_populates="exhibits")

    def __repr__(self):
        return f'<Exhibit(id={self.b36id})>'


    @property
    @lazy
    def permalink(self):

        output = self.title.lower()

        output = re.sub('&\w{2,3};', '', output)

        output = [re.sub('\W', '', word) for word in output.split()]
        output = [x for x in output if x][0:6]

        output = '-'.join(output)

        if not output:
            output = '-'

        return f"/locker/{self.author.username}/exhibit/{self.b36id}/{output}"

    @property
    def pic_permalink(self):
        image_type = self.image_type or "png"
        return f"/exhibit_image/{self.b36id}/{self.image_sha256[-6:]}.{image_type}"

    @property
    @lazy
    def signed_string(self):
        return f'{time.strftime("%d %B %Y at %H:%M:%S", time.gmtime(self.signed_utc))} UTC' if self.signed_utc else None

    @property
    @lazy
    def edited_string(self):
        return f'{time.strftime("%d %B %Y at %H:%M:%S", time.gmtime(self.edited_utc))} UTC' if self.edited_utc else None

    @property
    def json(self):
        data = super().json

        data["author"]=self.author.json_core

        return data

    @property
    def json_for_sig(self):
        data=self.json_core

        data.pop('signing_sha256', None)
        data.pop('rsa_signature', None)

        data["author_username"] = self.author.username
        data["author_id"]=self.author.b36id

        return data

    @property
    @lazy
    def sig_valid(self):

        if not self.rsa_signature:
            return False

        try:
            x=rsa.verify(
                json.dumps(
                    self.json_for_sig,
                    sort_keys=True).encode('utf-8'),
                bytes.fromhex(self.rsa_signature),
                self.author.public_key)
        except rsa.pkcs1.VerificationError:
            return False

        return True

    @property
    @lazy
    def sig_permalink(self):
        return f"{self.permalink}/signature"