from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer as Serializer
from config import Config
from datetime import datetime

# Initialize the database instance
db = SQLAlchemy()


# User model to represent users of the application
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    tasks = db.relationship('Task', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_token(self, expires_sec=1800):
        """Generate a secure reset token that expires in 30 minutes."""
        s = Serializer(Config.SECRET_KEY)
        return s.dumps({'user_id': self.id})

    # Static method to verify the reset token
    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        """Verify a reset token and return the associated user if valid."""
        s = Serializer(Config.SECRET_KEY)
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
        except:
            return None
        return User.query.get(user_id)


# Task model to represent tasks created by users
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=True)
    priority = db.Column(db.String(50), nullable=True)
    due_date = db.Column(db.String(50), nullable=True)
    completed = db.Column(db.Boolean, default=False)
    comments = db.relationship('Comment', backref='task', lazy=True)


# Comment model to represent comments associated with tasks
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
