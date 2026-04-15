from flask import Blueprint, request, jsonify
import jwt
import os
from dotenv import load_dotenv

load_dotenv()

question_routes = Blueprint('questions', __name__)
SECRET_KEY = os.getenv("SECRET_KEY")

from global_state import users, subjects

@question_routes.route('/subjects', methods=['GET'])
def get_subjects():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'msg': 'Missing token'}), 401

    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = decoded['email']
        if not users.get(email, {}).get('is_subscribed'):
            return jsonify({'msg': 'Not subscribed'}), 403
        return jsonify(subjects)
    except jwt.ExpiredSignatureError:
        return jsonify({'msg': 'Token expired'}), 403
    except Exception:
        return jsonify({'msg': 'Invalid token'}), 403
