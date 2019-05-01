from datetime import datetime,date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
from app import db
from hashlib import md5

@login.user_loader
def load_user(id):
	return User.query.get(int(id))

class User(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), index=True, unique=True)
	email = db.Column(db.String(120), index=True, unique=True)
	password_hash = db.Column(db.String(128))
	daily_allowance = db.Column(db.String(16))
	dA_timestamp = db.Column(db.Date,index=True,default=date.today)
	#adds transaction.payer as a reference back to the user
	#User u -> u.transactions will give the list of transactions
	transactions = db.relationship('Transaction',backref='payer',lazy='dynamic')
	arc_transactions = db.relationship('Arc_Transaction',backref='payer',lazy='dynamic')
	budgets = db.relationship('Budget',backref='budgeter',lazy='dynamic')

	def __repr__(self):
		return '<User {}>'.format(self.username)

	def set_password(self,password):
		self.password_hash=generate_password_hash(password)

	def check_password(self,password):
		return check_password_hash(self.password_hash,password)

	def avatar(self,size):
		digest = md5(self.email.lower().encode('utf-8')).hexdigest()
		return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
			digest,size)

class Transaction(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	note = db.Column(db.String(16))
	amount = db.Column(db.String(16))
	category = db.Column(db.String(32))
	timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
	recurring = db.Column(db.Boolean)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


	def __repr__(self):
		return '<{}:{}>'.format(self.note,self.amount)

class Arc_Transaction(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	note = db.Column(db.String(16))
	amount = db.Column(db.String(16))
	category = db.Column(db.String(32))
	timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
	recurring = db.Column(db.Boolean)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


	def __repr__(self):
		return '<arc {}:{}>'.format(self.note,self.amount)

class Budget(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	cur_amount = db.Column(db.String(16))
	max_amount = db.Column(db.String(16))
	category = db.Column(db.String(32),unique=True)
	timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

	def __repr__(self):
		return '<{}:{}>'.format(self.category,self.max_amount)