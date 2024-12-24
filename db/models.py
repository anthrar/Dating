from . import db
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash


class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(180),  nullable=False)  
    name = db.Column(db.String(80), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.Integer, nullable=False)
    search = db.Column(db.Integer, nullable=False)
    aboutme = db.Column(db.String(2000), nullable=True)
    photo = db.Column(db.String(180), nullable=True)
    hidden = db.Column(db.Integer, nullable=True)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def isFillProfile(self):
        return self.name.strip() != ''
        
    def __init__(self, login, password):
            self.login = login
            self.password = generate_password_hash(password)
            self.name = ''
            self.age = 20
            self.gender = 0   
            self.search = 1   
            self.aboutme = ''
            self.photo = None
    def __repr__(self):
            return f'User {self.name} {self.id}: {self.login}'
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}