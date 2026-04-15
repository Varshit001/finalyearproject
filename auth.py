from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from dotenv import load_dotenv
import os

load_dotenv()

from models import User
from db import db

auth_routes = Blueprint('auth', __name__)
SECRET_KEY = os.getenv("SECRET_KEY")


@auth_routes.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'User already exists'}), 400

    new_user = User(
        email=email,
        password=generate_password_hash(password),
        is_verified=False,
        is_subscribed=False
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Signup successful'}), 201


@auth_routes.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({'message': 'Invalid credentials'}), 401

    token = jwt.encode(
        {
            'sub': email,
            'email': email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=365)  # 🔁 1 year token
        },
        SECRET_KEY, algorithm="HS256"
    )
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'is_verified': user.is_verified,
        'is_subscribed': user.is_subscribed
    }), 200 if user.is_verified else 202


@auth_routes.route('/status/<email>', methods=['GET'])
def check_user_status(email):
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({
        'is_verified': user.is_verified,
        'is_subscribed': user.is_subscribed
    }), 200


@auth_routes.route('/username', methods=['POST'])
def update_username():
    data = request.get_json()
    email = data.get('email')
    username = data.get('username')

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'msg': 'User not found'}), 404

    user.username = username
    db.session.commit()
    return jsonify({'msg': 'Username saved'}), 200