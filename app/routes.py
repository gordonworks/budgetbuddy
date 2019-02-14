from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, AddTransactionForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User,Transaction
from werkzeug.urls import url_parse
from app.maths import calc_DA
from datetime import date, datetime
from app.tables import Results

@app.route('/')
@app.route('/index')
@login_required
def index():
	transactions = Transaction.query.filter_by(payer = current_user).all()
	return render_template('index.html',title='Budget Buddy',transactions=transactions)

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
	if user.dA_timestamp.day != datetime.today().day:
		daily_amount = calc_DA(current_user)
	if form.validate_on_submit():
		t = Transaction(note=form.note.data,amount='-'+form.amount.data,
			recurring=False,payer=current_user,timestamp=form.dt.data)
		#if there was no timestamp selected, then we will subtract from the daily allowance
		if not t.timestamp:
			f = float(user.daily_allowance)
			user.daily_allowance = str(f+float(t.amount))
		else:
			user.daily_allowance = calc_DA(current_user)
		
		db.session.add(t)
		db.session.commit()
		return redirect(url_for('transactions'))

	page = request.args.get('page',1,type=int)
	transactions = Transaction.query.filter_by(
		payer = current_user,recurring=False).order_by(Transaction.timestamp.desc()).paginate(
		page,app.config['POSTS_PER_PAGE'],False)
	next_url = url_for('transactions',page=transactions.next_num) \
		if transactions.has_next else None
	print(next_url)
	prev_url = url_for('transactions',page=transactions.prev_num) \
		if transactions.has_prev else None

	allTrans = Transaction.query.filter_by(payer = current_user,recurring=True).all()

	return render_template('user.html',user=user,transactions=transactions.items,form=form,
		title="Profile",allTrans=allTrans,next_url=next_url,prev_url=prev_url)

"""
@app.route('/user/<username>',methods=['GET','POST'])
@login_required
def user(username):
	user = User.query.filter_by(username=username).first_or_404()
	form = AddTransactionForm()
	if user.dA_timestamp.day != datetime.today().day:
		daily_amount = calc_DA(current_user)
	if form.validate_on_submit():
		t = Transaction(note=form.note.data,amount='-'+form.amount.data,
			recurring=False,payer=current_user,timestamp=form.dt.data)
		#if there was no timestamp selected, then we will subtract from the daily allowance
		if not t.timestamp:
			f = float(user.daily_allowance)
			user.daily_allowance = str(f+float(t.amount))
		else:
			user.daily_allowance = calc_DA(current_user)
		
		db.session.add(t)
		db.session.commit()

		return redirect(url_for('user',username=current_user.username))

	page = request.args.get('page',1,type=int)
	transactions = Transaction.query.filter_by(payer = current_user,recurring=False).paginate(
		page,app.config['POSTS_PER_PAGE'],False)
	next_url = url_for('user',username=username,page=transactions.next_num) \
		if transactions.has_next else None
	prev_url = url_for('user',username=username,page=transactions.prev_num) \
		if transactions.has_prev else None
	allTrans = Transaction.query.filter_by(payer = current_user,recurring=True).all()

	return render_template('user.html',user=user,transactions=transactions.items,form=form,
		title="Profile",allTrans=allTrans,next_url=next_url,prev_url=prev_url)
"""

@app.route('/delete/<int:id>/',methods=['GET','POST'])
@login_required
def delete(id):
	t = Transaction.query.filter_by(id=id).first_or_404()
	user = User.query.filter_by(username=current_user.username).first_or_404()
	db.session.delete(t)
	db.session.commit()
	#deleting will subtract from the DA or recalculate its new value
	
	#THIS CAUSES A 404 on the user page - possibly fixed?
	if t.recurring:
		user.daily_allowance = calc_DA(current_user)
	elif t.timestamp.day != datetime.today().day:
		user.daily_allowance = calc_DA(current_user)
	else:
		f = float(user.daily_allowance)
		user.daily_allowance = str(f-float(t.amount))
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
	#transactions = Transaction.query.filter_by(recurring=True).all()
	transactions = Transaction.query.filter(Transaction.recurring==True,Transaction.amount<='0',
		Transaction.payer==current_user).all()
	if form.validate_on_submit():
		t = Transaction(note=form.note.data,amount='-'+form.amount.data,
			recurring=True,payer=current_user,timestamp=form.dt.data)
		user.daily_allowance = calc_DA(current_user)
		user.dA_timestamp = date.today()
		db.session.add(t)
		db.session.commit()
		return redirect(url_for('expenses'))
	return render_template('user.html',username=user.username,
		user=user,transactions=transactions,form=form,title="Expenses")

@app.route('/income',methods=['GET','POST'])
@login_required
def income():
	form = AddTransactionForm()
	user = User.query.filter_by(username=current_user.username).first_or_404()
	#transactions = Transaction.query.filter_by(recurring=True).all()
	transactions = Transaction.query.filter(Transaction.amount>='0',
		Transaction.payer==current_user).all()
	if form.validate_on_submit():
		t = Transaction(note=form.note.data,amount=form.amount.data,
			recurring=True,payer=current_user,timestamp=form.dt.data)
		user.daily_allowance = calc_DA(current_user)
		user.dA_timestamp = date.today()
		db.session.add(t)
		db.session.commit()
		return redirect(url_for('income'))
	return render_template('user.html',username=user.username,user=user,
		transactions=transactions,form=form,title="Income")

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

@app.route('/results',methods=['GET','POST'])
@login_required
def results():
	user = User.query.filter_by(username=current_user.username).first_or_404()
	transactions = Transaction.query.filter_by(payer=current_user).all()
	table = Results(transactions)

	form = AddTransactionForm()
	if form.validate_on_submit():
		t = Transaction(note=form.note.data,amount='-'+form.amount.data,
			recurring=False,payer=current_user,timestamp=form.dt.data)
		db.session.add(t)
		db.session.commit()
		return redirect(url_for('results'))
	return render_template('results.html',table=table,form=form)
