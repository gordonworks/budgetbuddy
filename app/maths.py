from app.models import User,Transaction
from flask_login import current_user
from datetime import datetime
from calendar import monthrange

def calc_DA(user):
	user = User.query.filter_by(username=current_user.username).first_or_404()
	transactions = Transaction.query.filter_by(payer=current_user).all()
	total_DA = 0.0
	daysInMonth = monthrange(datetime.today().year,datetime.today().month)[1]
	for t in transactions:
		total_DA+=float(t.amount)
	
	total_DA = total_DA/daysInMonth
	return repr(total_DA)