import binascii
import fnmatch
import json
import os

from flask_restplus import fields, abort
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    userid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)

    write_fields = {'username': fields.String,
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
    http_method_glob = db.Column(db.String(16), default="*")
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

def _validate_request_made_on_behalf_of_user(auth_header, userid, http_method):
    try:
        data = json.loads(binascii.a2b_base64(auth_header.split(" ")[1]))
    except Exception:
        return False
    if not 'tokenid' in data:
        return False
    if not 'secret' in data:
        return False
    tokenid = data['tokenid']
    secret = data['secret']
    token = Token.query.filterby(tokenid=tokenid).first()
    if token is None:
        return False
    return userid == token.userid and secret == token.secret and fnmatch.fnmatch(http_method, token.http_method_glob) 

def validate_request_made_on_behalf_of_user(auth_header, userid, http_method):
    if not _validate_request_made_on_behalf_of_user(auth_header, userid, http_method):
        abort(401)