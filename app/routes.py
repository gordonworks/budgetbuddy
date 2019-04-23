from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, AddTransactionForm, AddBudgetForm, FilterForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User,Transaction,Budget
from werkzeug.urls import url_parse
from app.maths import calc_DA, category_totals, days_left, gen_calendar
from datetime import date, datetime
from calendar import monthrange
import pygal

@app.route('/')
@app.route('/index')
@login_required
def index():
	user = User.query.filter_by(username=current_user.username).first_or_404()
	#recalculate daily amount if the day is stale
	if user.dA_timestamp.day != datetime.today().day:
		daily_amount = calc_DA(current_user)

	#if there was no timestamp selected, then we will subtract from the daily allowance
	user.daily_allowance = calc_DA(current_user)

	total = 0.0
	dayTrans = Transaction.query.filter_by(recurring=False)
	for t in dayTrans:
		if t.timestamp.date() == datetime.today().date():
			total = total+t.amount
	total = 0-total

	"""
	Gathers all spending by day into a tuple (date,amount)
	"""
	spent_on_day=[]
	temp=0.0
	#trans = Transaction.query.filter_by(payer=current_user).filter(Transaction.amount<=0).filter_by(recurring=True).all()
	trans = Transaction.query.filter_by(payer=current_user).filter(Transaction.amount<=0).all()
	for day in gen_calendar():
		for t in trans:
			if day == t.timestamp.date():
				temp = temp - t.amount
		spent_on_day.append((day,temp))
		temp=0.0

	return render_template('index.html',title='Budget Buddy',user=user,dim=days_left(),
		today=total,dA=float(user.daily_allowance),days=spent_on_day)

@app.route('/login',methods=['GET','POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first()
		if user is None or not user.check_password(form.password.data):
			flash('Invalid username/password')
			return redirect(url_for('login'))
		login_user(user,remember=form.remember_me.data)
		next_page = request.args.get('next')
		if not next_page or url_parse(next_page).netloc != '':
			next_page = url_for('index')
		return redirect(next_page)
	return render_template('login.html',title='Sign In',form=form)

@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('index'))

@app.route('/register',methods=['GET','POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	form = RegistrationForm()
	if form.validate_on_submit():
		user = User(username=form.username.data,email=form.email.data)
		user.set_password(form.password.data)
		db.session.add(user)
		db.session.commit()
		flash('You are now registered.')
		return redirect(url_for('login'))
	return render_template('register.html',title="Registration",form=form)

@app.route('/transactions',methods=['GET','POST'])
@login_required
def transactions():
	user = User.query.filter_by(username=current_user.username).first_or_404()
	form = AddTransactionForm()
	if form.validate_on_submit():
		formatted_amount = f'{float(form.amount.data):.2f}'
		t = Transaction(note=form.note.data,amount='-'+formatted_amount,
			recurring=False,payer=current_user,category=form.category.data,timestamp=form.dt.data)

		db.session.add(t)
		db.session.commit()
		return redirect(url_for('transactions'))

	#pagination logic
	page = request.args.get('page',1,type=int)
	transactions = Transaction.query.filter_by(
		payer = current_user,recurring=False).order_by(Transaction.timestamp.desc()).paginate(
		page,app.config['POSTS_PER_PAGE'],False)
	next_url = url_for('transactions',page=transactions.next_num) \
		if transactions.has_next else None
	prev_url = url_for('transactions',page=transactions.prev_num) \
		if transactions.has_prev else None


	#generating the light blue recurring transactions on the page
	allTrans = Transaction.query.filter_by(payer = current_user,recurring=True).all()

	return render_template('user.html',user=user,transactions=transactions.items,form=form,
		title="Profile",allTrans=allTrans,next_url=next_url,prev_url=prev_url)

@app.route('/delete/<type>/<int:id>/',methods=['GET','POST'])
@login_required
def delete(type,id):
	if type == 'transaction':
		t = Transaction.query.filter_by(id=id).first_or_404()
		user = User.query.filter_by(username=current_user.username).first_or_404()
		db.session.delete(t)
		db.session.commit()
	
		user.daily_allowance = calc_DA(current_user)
		db.session.commit()
	elif type == 'budget':
		b = Budget.query.filter_by(id=id).first_or_404()
		db.session.delete(b)
		db.session.commit()
	#ensures deleting a transaction preserves the current page
	next_page = request.args.get('next')
	if not next_page or url_parse(next_page).netloc != '':
			next_page = url_for('user',username=current_user.username)
	return redirect(next_page)
	#return redirect(url_for('edit',id=id))
	#return redirect(url_for(request.url))

@app.route('/expenses',methods=['GET','POST'])
@login_required
def expenses():
	form = AddTransactionForm()
	user = User.query.filter_by(username=current_user.username).first_or_404()
	daysInMonth = monthrange(datetime.today().year,datetime.today().month)[1] - datetime.today().day
	#transactions = Transaction.query.filter_by(recurring=True).all()
	transactions = Transaction.query.filter(Transaction.recurring==True,Transaction.amount<='0',
		Transaction.payer==current_user).all()
	if form.validate_on_submit():
		formatted_amount = f'{float(form.amount.data):.2f}'
		t = Transaction(note=form.note.data,amount='-'+formatted_amount,
			recurring=True,payer=current_user,category=form.category.data,timestamp=form.dt.data)
		user.daily_allowance = calc_DA(current_user)
		user.dA_timestamp = date.today()
		db.session.add(t)
		db.session.commit()
		return redirect(url_for('expenses'))
	return render_template('user.html',username=user.username,
		user=user,transactions=transactions,form=form,title="Expenses",dim=daysInMonth)

@app.route('/income',methods=['GET','POST'])
@login_required
def income():
	form = AddTransactionForm()
	user = User.query.filter_by(username=current_user.username).first_or_404()
	daysInMonth = monthrange(datetime.today().year,datetime.today().month)[1] - datetime.today().day
	#transactions = Transaction.query.filter_by(recurring=True).all()
	transactions = Transaction.query.filter(Transaction.amount>='0',
		Transaction.payer==current_user).all()
	if form.validate_on_submit():
		formatted_amount = f'{float(form.amount.data):.2f}'
		t = Transaction(note=form.note.data,amount=formatted_amount,
			recurring=True,payer=current_user,category='income',timestamp=form.dt.data)
		user.daily_allowance = calc_DA(current_user)
		user.dA_timestamp = date.today()
		db.session.add(t)
		db.session.commit()
		return redirect(url_for('income'))
	return render_template('user.html',username=user.username,user=user,
		transactions=transactions,form=form,title="Income",dim=daysInMonth)
"""
@app.route('/new_entry',methods=['GET','POST'])
@login_required
def new_entry():
	eForm = AddTransactionForm()
	iForm = AddTransactionForm()
	dForm = AddTransactionForm()
	#can reference in Jinja as form.eForm.amount(), etc
	form = {'eForm':eForm,'iForm':iForm,'dForm':dForm}

	user = User.query.filter_by(username=current_user.username).first_or_404()

	eTrans = Transaction.query.filter(Transaction.recurring==True,Transaction.amount<='0',
		Transaction.payer==current_user).all()
	iTrans = Transaction.query.filter(Transaction.amount>='0',
		Transaction.payer==current_user).all()
	dTrans = transactions = Transaction.query.filter_by(payer = current_user, recurring=False).all()
	#reference as transactions.eTrans.payer.username for the payers username
	transactions = {'eTrans':eTrans,'iTrans':iTrans,'dTrans':dTrans}

	if eForm.validate_on_submit():
		t = Transaction(note=eForm.note.data,amount='-'+eForm.amount.data,
			recurring=True,payer=current_user,timestamp=eForm.dt.data)
		db.session.add(t)
		db.session.commit()
		return redirect(url_for('new_entry'))
	if iForm.validate_on_submit():
		t = Transaction(note=iForm.note.data,amount=iForm.amount.data,
			recurring=True,payer=current_user,timestamp=iForm.dt.data)
		db.session.add(t)
		db.session.commit()
		return redirect(url_for('new_entry'))
	if dForm.validate_on_submit():
		t = Transaction(note=dForm.note.data,amount='-'+dForm.amount.data,
			recurring=False,payer=current_user)
		db.session.add(t)
		db.session.commit()
		return redirect(url_for('new_entry'))

	return render_template('new_entry.html',user=user,transactions=transactions,form=form)
"""

@app.route('/results/<category>/<daterange>')
@login_required
def results(category,daterange):
	total=0.0
	itotal=0.0
	#Logic for all transaction/expenses
	#1 All or 2 using the category
	if category == 'all' or category =='income':
		allTrans = Transaction.query.filter_by(payer=current_user
			).filter(Transaction.amount<=0).order_by(Transaction.timestamp.desc()).all()
	else:
		allTrans = Transaction.query.filter_by(payer=current_user
			).filter(Transaction.category == category).filter(Transaction.amount<=0).order_by(Transaction.timestamp.desc()).all()

	if daterange != 'all':
		print(daterange)
	#Gathering up for total at top of table
	for item in allTrans:
		total-=item.amount

	#Income transactions
	iTrans = Transaction.query.filter_by(payer=current_user
			).filter(Transaction.amount>=0).order_by(Transaction.timestamp.desc()).all()
	for item in iTrans:
		itotal+=item.amount

	#Setting defaults on the forms to coincide with whats being looked at
	form = FilterForm()
	form.category.default = category
	form.process()
	
	return render_template('results.html',allTrans=allTrans,total=total,loc=category,iTrans=iTrans,itotal=itotal,form=form)

@app.route('/edit/<int:id>/',methods=['GET','POST'])
@login_required
def edit(id):
	user =  User.query.filter_by(username=current_user.username).first_or_404()
	transaction = Transaction.query.filter_by(id=id).first_or_404()
	form = AddTransactionForm(category=transaction.category)
	#differentiating income/expenses and preserving negative sign
	neg = ''
	if transaction.amount < 0:
		neg = '-'
		transaction.amount = 0-transaction.amount
	
	#cancel button vs save button
	if form.validate_on_submit():
		if 'cancel_button' in request.form:
			print('edit canceled')
		else:
			transaction.note=form.note.data
			transaction.amount=neg+form.amount.data
			transaction.timestamp=form.dt.data
			transaction.category=form.category.data

			user.daily_allowance = calc_DA(current_user)
			user.dA_timestamp = date.today()

			db.session.commit()

		#ensures editing a transaction preserves the current page
		next_page = request.args.get('next')
		if not next_page or url_parse(next_page).netloc != '':
				next_page = url_for('user',username=current_user.username)
		return redirect(next_page)

	return render_template('edit.html',transaction=transaction,form=form,title="Edit")


@app.route('/charts',methods=['GET','POST'])
@login_required
def charts():
	trans_dict = dict()
	transactions = Transaction.query.filter_by(payer=current_user).all()
	#Gathering all negative transactions for the spending pie chart
	for t in transactions:
		if t.amount > 0:
			pass
		elif t.category in trans_dict:
			trans_dict[t.category] += -t.amount
		else:
			trans_dict[t.category] = -t.amount


	graph = pygal.Pie()
	graph.title = 'Spending by category'
	for k,v in trans_dict.items():
		graph.add(k,v)


	graph_data = graph.render_data_uri()
	return render_template("charts.html", graph_data = graph_data)

@app.route('/budgets',methods=['GET','POST'])
@login_required
def budgets():
	#Gets all budgets to display on screen
	buds = Budget.query.filter_by(budgeter=current_user).all()
	#Aggregates all totals per category for the current user
	bud_dict = category_totals(current_user)
	#Percentages dictionary because jinja cant do math
	percentages = dict()
	#Sets current amount (cur_amount) in the budget data
	for bud in buds:
		bud.cur_amount = bud_dict[bud.category]
		percentages[bud.category] = 100*(bud.cur_amount/float(bud.max_amount))
	

	form = AddBudgetForm()

	default = 'progress-bar bg-warning'

	if form.validate_on_submit():
		b = Budget(cur_amount = bud_dict[form.category.data],max_amount=form.max_amount.data,
			category=form.category.data,budgeter=current_user)
		db.session.add(b)
		db.session.commit()
		return redirect(url_for('budgets'))
	return render_template('budgets.html',buds=buds,form=form,title="Budgets",percentages=percentages,
		default=default)