from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())
    video_summary_count = db.Column(db.Integer, default=0)  # New field
    is_premium = db.Column(db.Boolean, default=False)  # New field

    # Add any additional methods or properties as needed
