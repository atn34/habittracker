import base64
import binascii
import json
import os

from flask_restplus import fields, abort
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    userid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(80))

    write_fields = {'username': fields.String,
                    'password': fields.String,
                    }
    read_fields = {'userid': fields.Integer,
                   'username': fields.String,
                   }

    def __repr__(self):
        return '<User %r>' % self.userid


class Goal(db.Model):
    goalid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    lastDone = db.Column(db.DateTime)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'))
    user = db.relationship('User', backref=db.backref('goals', lazy='dynamic'))

    write_fields = {'name': fields.String}
    read_fields = {'name': fields.String,
                   'goalid': fields.Integer,
                   'lastDone': fields.DateTime,
                   'userid': fields.Integer,
                   }

    def __init__(self, user):
        self.user = user

    def __repr__(self):
        return '<Goal %r>' % self.goalid

def new_secret():
    return binascii.b2a_base64(os.urandom(64))

class Token(db.Model):
    tokenid = db.Column(db.Integer, primary_key=True)
    secret = db.Column(db.String(128), default=new_secret)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'))
    user = db.relationship('User', backref=db.backref('tokens', lazy='dynamic'))

    write_fields = {}
    read_fields = {'tokenid': fields.Integer,
                   'secret': fields.String,
                   'userid': fields.String,
                   }

    def __init__(self, user):
        self.user = user

    def __repr__(self):
        return '<Token %r>' % self.tokenid

    def serialize(self):
        return base64.b64encode(json.dumps(dict(
            tokenid=self.tokenid,
            secret=self.secret,
        )))

def MakeToken(user):
    token = Token(user)
    token.secret = new_secret()
    return token

def _validate_request_made_on_behalf_of_user(auth_header, userid, http_method):
    try:
        data = json.loads(base64.b64decode(auth_header.split(" ")[1]))
    except (ValueError, TypeError):
        return False
    if not 'tokenid' in data:
        return False
    if not 'secret' in data:
        return False
    tokenid = data['tokenid']
    secret = data['secret']
    token = Token.query.filter_by(tokenid=tokenid).first()
    if token is None:
        return False
    return userid == token.userid and secret == token.secret

def validate_request_made_on_behalf_of_user(auth_header, userid, http_method):
    if not _validate_request_made_on_behalf_of_user(auth_header, userid, http_method):
        abort(401)
