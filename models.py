from extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)
    jobs = db.relationship("Job", backref="owner", lazy=True, cascade="all, delete-orphan")
    
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # owner of the job entry
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # core fields for a job application
    company = db.Column(db.String(120), nullable=False, index=True)
    role = db.Column(db.String(120), nullable=False, index=True)
    status = db.Column(db.String(32), nullable=False, default="Applied")  # Applied / Interview / Offer / Rejected

    location = db.Column(db.String(120))
    link = db.Column(db.String(512))
    applied_on = db.Column(db.Date)  # store date only
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)