#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        image_url = data.get('image_url')
        bio = data.get('bio')

        if not (username and password):
            return {'error': 'Username and password are required'}, 422

        user = User.query.filter_by(username=username).first()
        if user:
            return {'error': 'Username already exists'}, 409
        
        user = User(
            username=username,
            image_url=image_url,
            bio=bio
        )
        user.password_hash = password
        
        try:
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            return user.to_dict(), 201
        except IntegrityError:
            db.session.rollback()
            return {'error': 'Username already exists'}, 409


class CheckSession(Resource):
    def get(self):
        user_id = session['user_id']
        if user_id:
            user = User.query.filter(User.id == user_id).first()
            return user.to_dict(), 200
        else:
            return {'message': 'Please log in'}, 401
class Login(Resource):
    def post(self):
        request_data = request.json
        username = request_data.get('username')
        password = request_data.get('password')
        user = User.query.filter(User.username == username).first()
        if user:
            if user.authenticate(password):
                session['user_id'] = user.id
                return user.to_dict(), 200
            else:
                return {'message': 'Incorrect password'}, 401
        else:
            return {'message': "User not found"}, 401

class Logout(Resource):
    def delete(self):
        session['user_id'] = None
        return {}, 401

class RecipeIndex(Resource):
    def get(self):
        if 'user_id' not in session:
            return {'message': 'Unauthorized'}, 401
        user = User.query.get(session['user_id'])
        if not user:
            return {'message': 'User not found'}, 401

        recipe = [recipe.to_dict() for recipe in user.recipes]
        return recipe, 200
        
    def post(self):
        if 'user_id' not in session:
            return {'message': 'Unauthorized'}, 401
        
        request_data = request.json
        title = request_data.get('title')
        instructions = request_data.get('instructions')
        minutes_to_complete = request_data.get('minutes_to_complete')

        if not all([title, instructions, minutes_to_complete]):
            return {'message': 'Incomplete data provided'}, 400

        try:
            recipe = Recipe(
                title=title,
                instructions=instructions,
                minutes_to_complete=minutes_to_complete,
                user_id=session['user_id']
            )
            db.session.add(recipe)
            db.session.commit()
            return recipe.to_dict(), 201
        except IntegrityError:
            return {'message': '422 Unprocessable Entity'}, 422
        

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)