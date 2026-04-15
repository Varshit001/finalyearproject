from db import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    email = db.Column(db.String(120), primary_key=True)
    password = db.Column(db.String(512), nullable=False)
    username = db.Column(db.String(100), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    is_subscribed = db.Column(db.Boolean, default=False)

    paid_subjects = db.relationship('Payment', backref='user', lazy=True, cascade="all, delete-orphan")
    answers = db.relationship('Answer', backref='user', lazy=True, cascade="all, delete-orphan")
    marks = db.relationship('Mark', backref='user', lazy=True, cascade="all, delete-orphan")
    evaluated = db.relationship('Evaluated', backref='user', lazy=True, cascade="all, delete-orphan")

class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    tests = db.relationship('Test', backref='subject', lazy=True, cascade="all, delete-orphan")
    payments = db.relationship('Payment', backref='subject', lazy=True, cascade="all, delete-orphan")

class Test(db.Model):
    __tablename__ = 'tests'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    question_file = db.Column(db.String(255), nullable=False)
    key_file = db.Column(db.String(255), nullable=True)
    evaluated_file = db.Column(db.String(255), nullable=True)
    total_marks = db.Column(db.Integer, nullable=False)

    answers = db.relationship('Answer', backref='test', lazy=True, cascade="all, delete-orphan")
    marks = db.relationship('Mark', backref='test', lazy=True, cascade="all, delete-orphan")
    evaluated = db.relationship('Evaluated', backref='test', lazy=True, cascade="all, delete-orphan")

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), db.ForeignKey('users.email'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    screenshot_filename = db.Column(db.String(255), nullable=False)
    approved = db.Column(db.Boolean, default=False)

class Answer(db.Model):
    __tablename__ = 'answers'
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), db.ForeignKey('users.email'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

class Mark(db.Model):
    __tablename__ = 'marks'
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), db.ForeignKey('users.email'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)

class Otp(db.Model):
    __tablename__ = 'otps'
    email = db.Column(db.String(120), primary_key=True)
    otp = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Evaluated(db.Model):
    __tablename__ = 'evaluated'
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), db.ForeignKey('users.email'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
