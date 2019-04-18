from app.models import User,Transaction
from flask_login import current_user
from datetime import datetime
from calendar import monthrange

def calc_DA(user, daily=True):
	user = User.query.filter_by(username=current_user.username).first_or_404()
	transactions = Transaction.query.filter_by(payer=current_user).all()
	total_DA = 0.0
	#Gets the remaining days left of the year
	daysInMonth = days_left()
	for t in transactions:
		total_DA+=float(t.amount)
	if daily:
		total_DA = total_DA/daysInMonth

	total_DA = f'{total_DA:.2f}'
	return total_DA

def category_totals(user):
	user = User.query.filter_by(username=user.username).first_or_404()
	transactions = Transaction.query.filter_by(payer=user).filter(Transaction.amount<=0).all()
	d = dict()
	
	for transaction in transactions:
		d[transaction.category] = d.get(transaction.category,0.0)-transaction.amount

	return d

def days_left():
	return (monthrange(datetime.today().year,datetime.today().month)[1] - datetime.today().day)+1