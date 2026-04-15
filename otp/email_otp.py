from flask import Blueprint, request, jsonify
import smtplib
import random
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

from db import db
from models import User, Otp

load_dotenv()

otp_routes = Blueprint('otp', __name__)


@otp_routes.route('/send', methods=['POST'])
def send_otp():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'msg': 'Email is required'}), 400

    otp = str(random.randint(100000, 999999))

    record = Otp.query.filter_by(email=email).first()
    if record:
        record.otp = otp
        record.created_at = datetime.utcnow()
    else:
        new_record = Otp(email=email, otp=otp)
        db.session.add(new_record)

    db.session.commit()

    sender = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")
    message = f"Subject: Your OTP\n\nYour OTP is {otp}. It is valid for 5 minutes."

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, email, message)
        return jsonify({'msg': 'OTP sent'}), 200
    except Exception as e:
        return jsonify({'msg': f'Failed to send OTP: {str(e)}'}), 500


@otp_routes.route('/verify', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    otp_input = data.get('otp')

    record = Otp.query.filter_by(email=email).first()
    if not record:
        return jsonify({'msg': 'OTP not found'}), 400

    if datetime.utcnow() - record.created_at > timedelta(minutes=5):
        return jsonify({'msg': 'OTP expired'}), 400

    if record.otp != otp_input:
        return jsonify({'msg': 'Invalid OTP'}), 400

    user = User.query.filter_by(email=email).first()
    if user:
        user.is_verified = True
        db.session.commit()

    # ✅ Remove OTP after successful verification
    db.session.delete(record)
    db.session.commit()

    return jsonify({'msg': 'OTP verified'}), 200
