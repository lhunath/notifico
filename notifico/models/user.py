# -*- coding: utf8 -*-
__all__ = ('User',)
import os
import base64
import hashlib
import datetime

from sqlalchemy.ext.hybrid import hybrid_property

from notifico import db
from notifico.models import CaseInsensitiveComparator


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # ---
    # Required Fields
    # ---
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    salt = db.Column(db.String(8), nullable=False)
    joined = db.Column(db.TIMESTAMP(), default=datetime.datetime.utcnow())

    # ---
    # Public Profile Fields
    # ---
    company = db.Column(db.String(255))
    website = db.Column(db.String(255))
    location = db.Column(db.String(255))

    @classmethod
    def new(cls, username, email, password):
        u = cls()
        u.email = email.lower().strip()
        u.salt = cls._create_salt()
        u.password = cls._hash_password(password, u.salt)
        u.username = username.strip()
        return u

    @staticmethod
    def _create_salt():
        """
        Returns a new base64 salt.
        """
        return base64.b64encode(os.urandom(8))[:8]

    @staticmethod
    def _hash_password(password, salt):
        """
        Returns a hashed password from `password` and `salt`.
        """
        return hashlib.sha256(salt + password.strip()).hexdigest()

    def set_password(self, new_password):
        self.salt = self._create_salt()
        self.password = self._hash_password(new_password, self.salt)

    @classmethod
    def by_email(cls, email):
        return cls.query.filter_by(email=email.lower().strip()).first()

    @classmethod
    def by_username(cls, username):
        return cls.query.filter_by(username_i=username).first()

    @classmethod
    def email_exists(cls, email):
        return cls.query.filter_by(email=email.lower().strip()).count() >= 1

    @classmethod
    def username_exists(cls, username):
        return cls.query.filter_by(username_i=username).count() >= 1

    @classmethod
    def login(cls, username, password):
        u = cls.by_username(username)
        if u and u.password == cls._hash_password(password, u.salt):
            return u
        return None

    @property
    def public_projects(self):
        return self.projects.filter_by(public=True)

    @property
    def private_projects(self):
        return self.projects.filter_by(public=False)

    @hybrid_property
    def username_i(self):
        return self.username.lower()

    @username_i.comparator
    def username_i(cls):
        return CaseInsensitiveComparator(cls.username)