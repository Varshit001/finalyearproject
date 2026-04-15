from flask import Blueprint, request, jsonify
import os

payment_routes = Blueprint('payment', __name__)

UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@payment_routes.route('/upload', methods=['POST'])
def upload_payment():
    file = request.files.get('screenshot')
    email = request.form.get('email')

    if not file or not email:
        return jsonify({'msg': 'Missing file or email'}), 400

    filename = email + "_payment.jpg"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    return jsonify({'msg': 'Screenshot uploaded. Await admin approval.'}), 200
