from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, AddTransactionForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User,Transaction
from werkzeug.urls import url_parse
from app.maths import calc_DA
from datetime import date

@app.route('/')
@app.route('/index')
@login_required
def index():
	transactions = [
		{
			'user':{'username':'gordon'},
			'amount' : 500.00,
			'note': 'rent',
			'recurring' : True
		},
		{
			'user':{'username':'gordon'},
			'amount' : 200.65,
			'note': 'xbox',
			'recurring' : False
		}
	]
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

@app.route('/user/<username>',methods=['GET','POST'])
@login_required
def user(username):
	user = User.query.filter_by(username=username).first_or_404()
	form = AddTransactionForm()
	#daily_amount = calc_DA(current_user)
	if form.validate_on_submit():
		t = Transaction(note=form.note.data,amount='-'+form.amount.data,
			recurring=False,payer=current_user)
		
		f = float(user.daily_allowance)
		user.daily_allowance = str(f+float(t.amount))
		
		db.session.add(t)
		db.session.commit()
		return redirect(url_for('user',username=current_user.username))
	transactions = Transaction.query.filter_by(payer = current_user).all()
	return render_template('user.html',user=user,transactions=transactions,form=form)
	#return render_template('user.html',user=user,transactions=transactions,form=form)

@app.route('/edit/<int:id>/',methods=['GET','POST'])
@login_required
def edit(id):
	t = Transaction.query.filter_by(id=id).first_or_404()
	user = User.query.filter_by(username=current_user.username).first_or_404()
	db.session.delete(t)
	db.session.commit()
	#deleting will subtract from the DA or recalculate its new value
	
	#THIS CAUSES A 404 on the user page - possibly fixed?
	if t.recurring:
		user.daily_allowance = calc_DA(current_user)
	else:
		f = float(user.daily_allowance)
		user.daily_allowance = str(f-float(t.amount))
	db.session.commit()
	
	return redirect(url_for('user',username=current_user.username))
	#return redirect(request.url)

@app.route('/expenses',methods=['GET','POST'])
@login_required
def expenses():
	form = AddTransactionForm()
	user = User.query.filter_by(username=current_user.username).first_or_404()
	#transactions = Transaction.query.filter_by(recurring=True).all()
	transactions = Transaction.query.filter(Transaction.recurring==True,Transaction.amount<='0',
		Transaction.payer==current_user).all()
	print(form.validate_on_submit())
	if form.validate_on_submit():
		t = Transaction(note=form.note.data,amount='-'+form.amount.data,
			recurring=True,payer=current_user,timestamp=form.dt.data)
		user.daily_allowance = calc_DA(current_user)
		user.dA_timestamp = date.today()
		db.session.add(t)
		db.session.commit()
		return redirect(url_for('expenses'))
	return render_template('expenses.html',user=user,transactions=transactions,form=form)

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
	return render_template('expenses.html',user=user,transactions=transactions,form=form)