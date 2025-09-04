from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_name = db.Column(db.String(255))
    text = db.Column(db.Text)
    post_url = db.Column(db.String(500))
    post_date = db.Column(db.String(50))
