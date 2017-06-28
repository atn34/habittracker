import datetime

from flask import Flask, request, abort
from flask_restplus import Resource, Api, fields

from passlib.hash import hex_sha512, bcrypt

from models import db, User, Goal, Token, MakeToken, validate_request_made_on_behalf_of_user

PROD_CONFIG = {
    'SQLALCHEMY_DATABASE_URI': 'sqlite:////tmp/test.db',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
}

api = Api(validate=True)


def set_config(app, config_dict):
    for key, val in config_dict.iteritems():
        app.config[key] = val


def create_app(config):
    app = Flask(__name__)
    set_config(app, config)
    db.init_app(app)
    api.init_app(app)
    return app


def update_obj_with(obj, json, keys):
    for key in keys:
        if key in json:
            setattr(obj, key, json[key])

# Based on https://blogs.dropbox.com/tech/2016/09/how-dropbox-securely-stores-your-passwords/
# TODO(atn34) add pepper
def hash_pw(password):
    return bcrypt.hash(hex_sha512.hash(password))

def verify_hash(password, h):
    return bcrypt.verify(hex_sha512.hash(password), h)

# Endpoints

PostUserRequest = api.model('PostUserRequest', User.write_fields)
PostUserResponse = api.model('PostUserResponse', User.read_fields)
GetUserResponse = api.model('GetUserResponse', User.read_fields)
PutUserRequest = api.model('PutUserRequest', User.write_fields)
PutUserResponse = api.model('PutUserResponse', User.read_fields)
UsernameTokenPostRequest = api.model('UsernameTokenPostRequest', {
    'username': fields.String(),
    'password': fields.String(),
})
UsernameTokenPostResponse = api.model('UsernameTokenPostResponse', {
    'token': fields.String(),
    'userid': fields.Integer(),
})
TokenPostRequest = api.model('TokenPostRequest', {'password': fields.String()})
TokenPostResponse = api.model('TokenPostResponse', {'token': fields.String()})

user_update_fields = User.write_fields.keys()
user_update_fields.remove('password')

@api.route('/api/user')
class CreateUserEndpoint(Resource):

    @api.expect(PostUserRequest)
    @api.doc(model=PostUserResponse)
    @api.marshal_with(PostUserResponse)
    def post(self):
        # TODO do something more graceful when integrity constraints are violated.
        json = request.json
        user = User()
        update_obj_with(user, json, user_update_fields)
        user.pwhash = hash_pw(json['password'])
        db.session.add(user)
        db.session.commit()
        return user

@api.route('/api/maketoken')
class MakeTokenEndpoint(Resource):

    @api.expect(UsernameTokenPostRequest)
    @api.doc(model=UsernameTokenPostResponse)
    @api.marshal_with(UsernameTokenPostResponse)
    def post(self):
        json = request.json
        user = User.query.filter_by(username=json['username']).first()
        if verify_hash(json['password'], user.pwhash):
            token = MakeToken(user)
        else:
            abort(401)
        db.session.add(token)
        db.session.commit()
        return dict(token=token.serialize(), userid=user.userid)


@api.route('/api/user/<int:userid>')
class UserEndpoint(Resource):

    @api.doc(model=GetUserResponse)
    @api.marshal_with(GetUserResponse)
    def get(self, userid):
        validate_request_made_on_behalf_of_user(
            request.headers.get('Authorization'), userid, 'GET')
        user = User.query.filter_by(userid=userid).first_or_404()
        return user

    @api.expect(PutUserRequest)
    @api.doc(model=PutUserResponse)
    @api.marshal_with(PutUserResponse)
    def put(self, userid):
        # TODO do something more graceful when integrity constraints are violated.
        validate_request_made_on_behalf_of_user(
            request.headers.get('Authorization'), userid, 'PUT')
        user = User.query.filter_by(userid=userid).first_or_404()
        update_obj_with(user, request.json, User.write_fields.iterkeys())
        db.session.add(user)
        db.session.commit()
        return user

@api.route('/api/user/<int:userid>/maketoken')
class UserEndpoint(Resource):

    @api.expect(TokenPostRequest)
    @api.doc(model=TokenPostResponse)
    @api.marshal_with(TokenPostResponse)
    def post(self, userid):
        json = response.json
        user = User.query.filter_by(userid=userid).first_or_404()
        if verify_hash(json['password'], user.pwhash):
            token = MakeToken(user)
        else:
            abort(401)
        db.session.add(token)
        db.session.commit()
        return dict(token=token.serialize())

GetGoalResponse = api.model('GetGoalResponse', Goal.read_fields)
PutGoalRequest = api.model('PutGoalRequest', Goal.write_fields)
PutGoalResponse = api.model('PutGoalResponse', Goal.read_fields)
GoalPostRequest = api.model('GoalPostRequest', Goal.write_fields)
GoalPostResponse = api.model('GoalPostResponse', Goal.read_fields)
UserGoalsResponse = api.model('UserGoalsResponse', {
    'goals': fields.List(fields.Nested(GetGoalResponse))
})
MarkDoneResponse = api.model('MarkDoneResponse', {
    'lastDone': fields.DateTime,
    'goalid': fields.Integer})

@api.route('/api/goal/<int:goalid>')
class GoalEndpoint(Resource):

    @api.doc(model=GetGoalResponse)
    @api.marshal_with(GetGoalResponse)
    def get(self, goalid):
        goal = Goal.query.filter_by(goalid=goalid).first_or_404()
        validate_request_made_on_behalf_of_user(
            request.headers.get('Authorization'), goal.userid, 'GET')
        return goal

    @api.expect(PutGoalRequest)
    @api.doc(model=PutGoalResponse)
    @api.marshal_with(PutGoalResponse)
    def put(self, goalid):
        # TODO do something more graceful when integrity constraints are violated.
        goal = Goal.query.filter_by(goalid=goalid).first_or_404()
        validate_request_made_on_behalf_of_user(
            request.headers.get('Authorization'), goal.userid, 'PUT')
        for field in Goal.write_fields:
            setattr(goal, field, request.json[field])
        db.session.add(goal)
        db.session.commit()
        return goal


def get_now():
    return datetime.datetime.now()


@api.route('/api/goal/<int:goalid>/markdone')
class MarkDoneEndpoint(Resource):

    @api.doc(model=MarkDoneResponse)
    @api.marshal_with(MarkDoneResponse) 
    def post(self, goalid):
        goal = Goal.query.filter_by(goalid=goalid).first_or_404()
        validate_request_made_on_behalf_of_user(
            request.headers.get('Authorization'), goal.userid, 'POST')
        now = get_now()
        goal.lastDone = now
        db.session.add(goal)
        db.session.commit()
        return {'lastDone': now, 'goalid': goalid}


@api.route('/api/user/<int:userid>/goals')
class UserGoals(Resource):

    @api.doc(model=UserGoalsResponse)
    @api.marshal_with(UserGoalsResponse)
    def get(self, userid):
        validate_request_made_on_behalf_of_user(
            request.headers.get('Authorization'), userid, 'GET')
        user = User.query.filter_by(userid=userid).first_or_404()
        goals = user.goals.all()
        return {'goals': goals}


@api.route('/api/user/<int:userid>/goal')
class UserGoal(Resource):

    @api.expect(GoalPostRequest)
    @api.doc(model=GoalPostResponse)
    @api.marshal_with(GoalPostResponse)
    def post(self, userid):
        validate_request_made_on_behalf_of_user(
            request.headers.get('Authorization'), userid, 'POST')
        user = User.query.filter_by(userid=userid).first_or_404()
        goal = Goal(user=user)
        update_obj_with(goal, request.json, Goal.write_fields.iterkeys())
        db.session.add(goal)
        db.session.commit()
        return goal


if __name__ == '__main__':
    app = create_app(PROD_CONFIG)
    app.run(debug=True)
