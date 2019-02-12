from flask_table import Table, Col

class Results(Table):
	id = Col('Id',show=False)
	note = Col('Note')
	amount = Col('Amount')
	timestamp = Col('Date')
	recurring = Col('Recurring?')
	user_id = Col('User')