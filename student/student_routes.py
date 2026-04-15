# ✅ student_routes.py

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime
import os, smtplib
from dotenv import load_dotenv

from db import db
from models import User, Subject, Test, Payment, Answer, Mark, Evaluated
from flask_jwt_extended import jwt_required, get_jwt_identity

student_routes = Blueprint('student_routes', __name__)
load_dotenv()

# ------------------ ✅ Get Subjects ------------------ #
@student_routes.route('/subjects', methods=['GET'])
@jwt_required()
def get_subjects():
    email = get_jwt_identity()
    user = User.query.get(email)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    subjects = Subject.query.all()
    result = []

    for subject in subjects:
        payment = Payment.query.filter_by(user_email=email, subject_id=subject.id, approved=True).first()
        subject_data = {
            'id': subject.id,
            'name': subject.name,
            'paid': bool(payment),
            'tests': []
        }

        for test in subject.tests:
            answer = Answer.query.filter_by(user_email=email, test_id=test.id).first()
            mark = Mark.query.filter_by(user_email=email, test_id=test.id).first()
            evaluated = Evaluated.query.filter_by(user_email=email, test_id=test.id).first()
            subject_data['tests'].append({
                'test_id': test.id,
                'test_name': test.name,
                'total_marks': test.total_marks,
                'question_file': f"/files/questions/{test.question_file}" if test.question_file else None,
                'key_file': f"/files/keys/{test.key_file}" if test.key_file else None,
                'evaluated_file': f"/files/evaluated/{evaluated.file_name}" if evaluated else None,
                'key_ready': bool(test.key_file),
                'evaluated_ready': bool(test.evaluated_file),
                'answer_uploaded': bool(answer),
                'marks': mark.score if mark else None
            })

        result.append(subject_data)

    return jsonify(result), 200

# ------------------ ✅ Upload Payment ------------------ #
@student_routes.route('/pay_subject', methods=['POST'])
@jwt_required()
def pay_subject():
    email = get_jwt_identity()
    subject_id = request.form.get('subject_id')
    screenshot = request.files.get('screenshot')

    if not subject_id or not screenshot:
        return jsonify({"error": "Missing subject_id or screenshot"}), 400

    filename = f"{email}_{subject_id}_payment.jpg"
    os.makedirs("uploads", exist_ok=True)
    screenshot.save(os.path.join("uploads", filename))

    payment = Payment.query.filter_by(user_email=email, subject_id=subject_id).first()
    if payment:
        payment.screenshot_filename = filename
        payment.approved = False
    else:
        payment = Payment(user_email=email, subject_id=subject_id, screenshot_filename=filename, approved=False)
        db.session.add(payment)

    db.session.commit()
    return jsonify({"message": "Payment screenshot uploaded"}), 200

# ------------------ ✅ Upload Answer ------------------ #
@student_routes.route('/upload_answer', methods=['POST'])
@jwt_required()
def upload_answer():
    email = get_jwt_identity()
    test_id = request.form.get('test_id')
    pdf = request.files.get('answer_pdf')

    if not test_id or not pdf:
        return jsonify({"error": "Missing test_id or file"}), 400

    test = Test.query.filter_by(id=test_id).first()
    if not test:
        return jsonify({"error": "Invalid test"}), 400

    subject_id = test.subject_id
    payment = Payment.query.filter_by(user_email=email, subject_id=subject_id, approved=True).first()
    if not payment:
        return jsonify({"error": "Payment not approved for this subject"}), 403

    os.makedirs('uploads/answers', exist_ok=True)
    filename = secure_filename(f"{test_id}_{email}.pdf")
    filepath = os.path.join('uploads/answers', filename)
    pdf.save(filepath)

    answer = Answer.query.filter_by(user_email=email, test_id=test_id).first()
    if answer:
        answer.file_name = filename
        answer.submitted_at = datetime.utcnow()
    else:
        answer = Answer(user_email=email, test_id=test_id, file_name=filename)
        db.session.add(answer)

    db.session.commit()
    notify_admin_upload(email, test.name)
    return jsonify({"message": "Answer uploaded successfully"}), 200

# ------------------ ✅ Notify Admin ------------------ #
def notify_admin_upload(email, test_name):
    try:
        sender = os.getenv("EMAIL")
        password = os.getenv("PASSWORD")
        admin = os.getenv("ADMIN_EMAIL")
        msg = f"Subject: New Answer Uploaded\n\nStudent {email} uploaded an answer for test '{test_name}'."

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, admin, msg)
    except Exception as e:
        print(f"Failed to notify admin: {e}")

# ------------------ ✅ Get Tests per Subject ------------------ #
@student_routes.route('/tests/<int:subject_id>', methods=['GET'])
@jwt_required()
def get_tests_for_subject(subject_id):
    subject = Subject.query.get(subject_id)
    if not subject:
        return jsonify({'error': 'Subject not found'}), 404

    tests = Test.query.filter_by(subject_id=subject_id).all()
    test_list = []
    for test in tests:
        test_list.append({
            'id': test.id,
            'name': test.name,
            'question_pdf': test.question_file,
            'total_marks': test.total_marks
        })

    return jsonify(test_list), 200

# ------------------ ✅ Report Card ------------------ #
@student_routes.route('/report_card', methods=['GET'])
@jwt_required(locations=["headers"])
def get_report_card():
    print("✅ Reached report_card route")
    email = get_jwt_identity()
    user = User.query.get(email)
    if not user:
        return jsonify({"error": "User not found"}), 404

    report = []
    total_scored = 0
    total_possible = 0

    subjects = Subject.query.all()
    for subject in subjects:
        subject_score = 0
        subject_total = 0
        test_details = []

        for test in subject.tests:
            mark = Mark.query.filter_by(user_email=email, test_id=test.id).first()
            if mark and mark.score is not None:
                test_score = float(mark.score)
                test_total = test.total_marks or 0
                subject_score += test_score
                subject_total += test_total
                total_scored += test_score
                total_possible += test_total

                test_details.append({
                    "test_name": test.name,
                    "score": test_score,
                    "total": test_total,
                    "percentage": round((test_score / test_total) * 100, 2) if test_total else None
                })

        report.append({
            "subject_id": subject.id,
            "subject_name": subject.name,
            "subject_percentage": round((subject_score / subject_total) * 100, 2) if subject_total else None,
            "tests": test_details
        })

    overall_percentage = round((total_scored / total_possible) * 100, 2) if total_possible else None

    return jsonify({
        "overall_percentage": overall_percentage,
        "subjects": report
    }), 200
