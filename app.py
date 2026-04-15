from flask import Flask, send_from_directory, redirect, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os
from datetime import timedelta

load_dotenv()

# Initialize app
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# 🔐 Load secret from .env
app.secret_key = os.getenv("SECRET_KEY", "fallback-key")
app.config["JWT_SECRET_KEY"] = app.secret_key
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
app.config["JWT_HEADER_NAME"] = "Authorization"
app.config["JWT_HEADER_TYPE"] = "Bearer"  

# Initialize JWT hello
jwt = JWTManager(app)

# ------------------ DB Config ------------------ #
from urllib.parse import quote_plus

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{quote_plus(os.getenv('DB_PASS'))}"
    f"@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

from db import db
db.init_app(app)
from models import *
# Create tables
def init_db():
    with app.app_context():
        try:
            db.create_all()
            print("✅ Tables checked/created successfully")
        except Exception as e:
            print(f"⚠️ Skipping table creation: {e}")

# ------------------ Register Blueprints ------------------ #
from auth import auth_routes
from otp.email_otp import otp_routes
from payment import payment_routes
from admin import admin_routes
from student.student_routes import student_routes

app.register_blueprint(auth_routes, url_prefix='/auth')
app.register_blueprint(otp_routes, url_prefix='/otp')
app.register_blueprint(payment_routes, url_prefix='/payment')
app.register_blueprint(admin_routes, url_prefix='/admin')
app.register_blueprint(student_routes, url_prefix='/student')

@app.before_request
def log_request_info():
    print(f"🔍 Incoming {request.method} {request.path}")
    print(f"🔐 Authorization: {request.headers.get('Authorization')}")


# ------------------ Serve Uploaded Files ------------------ #
@app.route('/files/<folder>/<filename>')
def serve_file(folder, filename):
    dirs = {
        'questions': os.path.join('uploads', 'questions'),
        'answers': os.path.join('uploads', 'answers'),
        'keys': os.path.join('uploads', 'keys'),
        'tests': os.path.join('uploads', 'tests')  # ✅ NEW for individual tests
    }
    if folder in dirs:
        return send_from_directory(dirs[folder], filename)
    return 'Invalid folder', 404

@app.route('/uploads/<filename>')
def serve_uploads(filename):
    return send_from_directory('uploads', filename)

@app.route('/uploads/answers/<path:filename>')
def serve_answer_pdf(filename):
    return send_from_directory('uploads/answers', filename)

@app.route('/files/evaluated/<path:filename>')
def get_evaluated_file(filename):
    return send_from_directory('uploads/evaluated', filename)
# ------------------ Ensure Folder Structure ------------------ #
for subfolder in [
    'uploads',
    'uploads/questions',
    'uploads/answers',
    'uploads/keys',
    'uploads/tests',
    'uploads/evaluated'  
]:
    os.makedirs(subfolder, exist_ok=True)

# ------------------ Default Route ------------------ #
@app.route('/')
def home():
    return redirect('/admin')

# ------------------ Run App ------------------ #
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)