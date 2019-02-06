from app.models import User,Transaction
from flask_login import current_user
from datetime import datetime

def calc_DA(user):
	user = User.query.filter_by(username=current_user.username).first_or_404()
	transactions = Transaction.query.filter_by(payer=current_user).all()
	total_DA = 0.0
	for t in transactions:
		total_DA+=float(t.amount)
	return repr(total_DA)