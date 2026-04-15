from app import app, db
import models  

with app.app_context():
    db.drop_all()
    db.create_all()