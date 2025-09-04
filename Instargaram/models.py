from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    page_name = db.Column(db.String(255), nullable=False)
    text = db.Column(db.Text, nullable=True)
    post_url = db.Column(db.String(500), nullable=False, unique=True)
    post_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Post {self.page_name} - {self.post_url}>"
