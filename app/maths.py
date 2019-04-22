from app.models import User,Transaction
from flask_login import current_user
from datetime import datetime,date
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

def gen_calendar():
	now = date.today()
	prevmonth=now.replace(month=(now.month-1),day=1)
	nextmonth=now.replace(month=(now.month+1),day=1)

	#Day ranges of months (1,30)
	nowdr=(1,monthrange(now.year,now.month)[1])
	prevdr = (1,monthrange(prevmonth.year,prevmonth.month)[1])
	nextdr = (1,monthrange(nextmonth.year,nextmonth.month)[1])

	month_days=[]
	days_of_last_month = now.replace(day=1).isoweekday()
	if days_of_last_month == 7:
		days_of_last_month = 0

	"""
	- enumerate over days in reverse dolm times
	- enumerate over days in current month
	- enumerate over days (42-30)-dolm for next month
	"""
	#28+1-5,28+1 - range(24,29)
	for d in range(prevdr[1]+1-days_of_last_month,prevdr[1]+1):
		month_days.append(prevmonth.replace(day=d))
		#month_days.append((d,prevmonth.replace(day=d).strftime("%A")))
	for d in range(nowdr[0],nowdr[1]+1):
		month_days.append(now.replace(day=d))
	for d in range(1,42-nowdr[1]-days_of_last_month+1):
		month_days.append(nextmonth.replace(day=d))
	return month_days