from flask import Blueprint, request, render_template, redirect, jsonify
from werkzeug.utils import secure_filename
import os
from models import User, Subject, Test, Payment, Answer, Mark, Evaluated
from db import db
from datetime import datetime

admin_routes = Blueprint('admin_routes', __name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ──────────────────────────────────────────
#  Dashboard
# ──────────────────────────────────────────
@admin_routes.route('/')
def admin_dashboard():
    pending = []
    payments = Payment.query.filter_by(approved=False).all()
    for p in payments:
        subject = Subject.query.get(p.subject_id)
        user = User.query.get(p.user_email)
        username = user.username if user else "Unknown"
        pending.append({
            "email": p.user_email,
            "username": username,
            "subject_id": p.subject_id,
            "subject_name": subject.name if subject else "Unknown",
            "screenshot": f"/uploads/{p.screenshot_filename}"
        })

    subjects = Subject.query.all()

    chart_labels = []
    chart_taken = []
    chart_passed = []
    chart_failed = []
    chart_pending = []

    for subject in subjects:
        total_taken = 0
        total_passed = 0
        total_failed = 0
        total_pending = 0

        for test in subject.tests:
            answers = test.answers
            total_taken += len(answers)
            for answer in answers:
                mark = Mark.query.filter_by(test_id=test.id, user_email=answer.user_email).first()
                if mark:
                    if test.total_marks and mark.score >= (test.total_marks / 2):
                        total_passed += 1
                    else:
                        total_failed += 1
                else:
                    total_pending += 1

        chart_labels.append(subject.name)
        chart_taken.append(total_taken)
        chart_passed.append(total_passed)
        chart_failed.append(total_failed)
        chart_pending.append(total_pending)

    return render_template(
        "admin_dashboard.html",
        pending=pending,
        subjects=subjects,
        chart_labels=chart_labels,
        chart_taken=chart_taken,
        chart_passed=chart_passed,
        chart_failed=chart_failed,
        chart_pending=chart_pending
    )


# ──────────────────────────────────────────
#  Subjects list page  →  /admin/subjects
# ──────────────────────────────────────────
@admin_routes.route('/subjects')
def subjects_page():
    subjects = Subject.query.all()
    return render_template("admin_subjects.html", subjects=subjects)


# ──────────────────────────────────────────
#  Add Subject  →  POST /admin/add_subject
# ──────────────────────────────────────────
@admin_routes.route('/add_subject', methods=['POST'])
def add_subject():
    subject_name = request.form.get('subject_name', '').strip()
    if not subject_name:
        return jsonify({'error': 'Missing subject name'}), 400

    new_subject = Subject(name=subject_name)
    db.session.add(new_subject)
    db.session.commit()
    return redirect('/admin/subjects')


# ──────────────────────────────────────────
#  Delete Subject  →  POST /admin/delete_subject
# ──────────────────────────────────────────
@admin_routes.route('/delete_subject', methods=['POST'])
def delete_subject():
    subject_id = request.form.get('subject_id')
    subject = Subject.query.get(subject_id)
    if not subject:
        return "Subject not found", 404

    for test in subject.tests:
        Answer.query.filter_by(test_id=test.id).delete()
        Mark.query.filter_by(test_id=test.id).delete()
        db.session.delete(test)

    db.session.delete(subject)
    db.session.commit()
    return redirect('/admin/subjects')


# ──────────────────────────────────────────
#  Manage Subject (Tests)  →  /admin/subject/<id>
# ──────────────────────────────────────────
@admin_routes.route('/subject/<int:subject_id>')
def manage_subject(subject_id):
    subject = Subject.query.get(subject_id)
    if not subject:
        return "Subject not found", 404

    total_score = 0
    total_possible = 0

    for test in subject.tests:
        test_total = test.total_marks or 0
        test_marks = Mark.query.filter_by(test_id=test.id).all()
        for mark in test_marks:
            if mark.score is not None:
                total_score += float(mark.score)
                total_possible += test_total

    average_percentage = (
        round((total_score / total_possible) * 100, 2)
        if total_possible > 0 else None
    )

    return render_template(
        "subject_tests.html",
        subject=subject,
        average=average_percentage
    )


# ──────────────────────────────────────────
#  Add Test  →  POST /admin/add_test
# ──────────────────────────────────────────
@admin_routes.route('/add_test', methods=['POST'])
def add_test():
    subject_id    = request.form.get('subject_id')
    test_name     = request.form.get('test_name', '').strip()
    total_marks   = request.form.get('total_marks')
    question_file = request.files.get('question_file')

    if not all([subject_id, test_name, total_marks, question_file]):
        return 'Missing data', 400

    try:
        total_marks = int(total_marks)
    except (ValueError, TypeError):
        return 'Invalid marks value', 400

    QUESTIONS_FOLDER = os.path.join("uploads", "questions")
    os.makedirs(QUESTIONS_FOLDER, exist_ok=True)

    filename       = secure_filename(question_file.filename)
    saved_filename = f"{subject_id}_{filename}"
    question_file.save(os.path.join(QUESTIONS_FOLDER, saved_filename))

    new_test = Test(
        subject_id=subject_id,
        name=test_name,
        total_marks=total_marks,
        question_file=saved_filename
    )
    db.session.add(new_test)
    db.session.commit()
    return redirect(f"/admin/subject/{subject_id}")


# ──────────────────────────────────────────
#  Delete Test  →  POST /admin/delete_test
# ──────────────────────────────────────────
@admin_routes.route('/delete_test', methods=['POST'])
def delete_test():
    test_id = request.form.get('test_id')
    test    = Test.query.filter_by(id=test_id).first()
    if not test:
        return 'Invalid test', 400

    subject_id = test.subject_id  # capture before deletion

    if test.question_file:
        qpath = os.path.join('uploads', 'questions', test.question_file)
        if os.path.exists(qpath):
            os.remove(qpath)

    if test.key_file:
        kpath = os.path.join('uploads', 'keys', test.key_file)
        if os.path.exists(kpath):
            os.remove(kpath)

    Answer.query.filter_by(test_id=test_id).delete()
    Mark.query.filter_by(test_id=test_id).delete()
    db.session.delete(test)
    db.session.commit()
    return redirect(f"/admin/subject/{subject_id}")


# ──────────────────────────────────────────
#  Upload Answer Key  →  POST /admin/upload_key
# ──────────────────────────────────────────
@admin_routes.route('/upload_key', methods=['POST'])
def upload_answer_key():
    test_id = request.form.get('test_id')
    pdf     = request.files.get('key_pdf')

    if not test_id or not pdf:
        return 'Missing data', 400

    KEYS_FOLDER = os.path.join("uploads", "keys")
    os.makedirs(KEYS_FOLDER, exist_ok=True)

    filename = f"key_{test_id}.pdf"
    pdf.save(os.path.join(KEYS_FOLDER, filename))

    test = Test.query.filter_by(id=test_id).first()
    if test:
        test.key_file = filename
        db.session.commit()
        return redirect(f"/admin/subject/{test.subject_id}")

    return 'Invalid test', 400


# ──────────────────────────────────────────
#  Update Marks  →  POST /admin/update_marks
# ──────────────────────────────────────────
@admin_routes.route('/update_marks', methods=['POST'])
def update_marks():
    email   = request.form.get('email')
    test_id = request.form.get('test_id')
    marks   = request.form.get('marks')

    if not email or not test_id:
        return "Missing data", 400

    try:
        marks = float(marks)
    except (ValueError, TypeError):
        return "Invalid marks format", 400

    mark = Mark.query.filter_by(user_email=email, test_id=test_id).first()
    if mark:
        mark.score = marks
    else:
        mark = Mark(user_email=email, test_id=test_id, score=marks)
        db.session.add(mark)

    db.session.commit()
    test = Test.query.get(test_id)
    return redirect(f"/admin/subject/{test.subject_id}")


# ──────────────────────────────────────────
#  Upload Evaluated PDF  →  POST /admin/upload_evaluated
# ──────────────────────────────────────────
@admin_routes.route('/upload_evaluated', methods=['POST'])
def upload_evaluated_individual():
    test_id = request.form.get('test_id')
    email   = request.form.get('user_email')
    pdf     = request.files.get('evaluated_pdf')

    if not email or not test_id or not pdf:
        return 'Missing data', 400

    os.makedirs('uploads/evaluated', exist_ok=True)
    filename = secure_filename(f"{test_id}_{email}_evaluated.pdf")
    filepath = os.path.join('uploads/evaluated', filename)
    pdf.save(filepath)

    record = Evaluated.query.filter_by(user_email=email, test_id=test_id).first()
    if record:
        record.file_name    = filename
        record.submitted_at = datetime.utcnow()
    else:
        record = Evaluated(user_email=email, test_id=test_id, file_name=filename)
        db.session.add(record)

    db.session.commit()
    test = Test.query.filter_by(id=test_id).first()
    return redirect(f"/admin/subject/{test.subject_id}")


# ──────────────────────────────────────────
#  Approve Payment  →  POST /admin/approve_subject_payment
# ──────────────────────────────────────────
@admin_routes.route('/approve_subject_payment', methods=['POST'])
def approve_subject_payment():
    email      = request.form.get('email')
    subject_id = request.form.get('subject_id')

    payment = Payment.query.filter_by(user_email=email, subject_id=subject_id).first()
    if payment:
        if payment.screenshot_filename:
            path = os.path.join('uploads', payment.screenshot_filename)
            if os.path.exists(path):
                os.remove(path)
        payment.approved = True
        db.session.commit()
        return redirect('/admin')

    return "Invalid data", 400


# ──────────────────────────────────────────
#  Payments page  →  /admin/payments
# ──────────────────────────────────────────
@admin_routes.route('/payments')
def payments_page():
    def build_list(payments):
        result = []
        for p in payments:
            subject  = Subject.query.get(p.subject_id)
            user     = User.query.get(p.user_email)
            username = user.username if user else "Unknown"
            result.append({
                "email":        p.user_email,
                "username":     username,
                "subject_id":   p.subject_id,
                "subject_name": subject.name if subject else "Unknown",
                "screenshot":   f"/uploads/{p.screenshot_filename}" if p.screenshot_filename else None,
            })
        return result

    pending  = build_list(Payment.query.filter_by(approved=False).all())
    approved = build_list(Payment.query.filter_by(approved=True).all())

    return render_template("admin_payments.html", pending=pending, approved=approved)