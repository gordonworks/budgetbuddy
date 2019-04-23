from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField,SelectField
from wtforms.fields.html5 import DateField
#from wtforms import DateField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Optional, Regexp
from app.models import User

class LoginForm(FlaskForm):
	username = StringField('Username', validators = [DataRequired()])
	password = PasswordField('Password', validators = [DataRequired()])
	remember_me = BooleanField('Remember Me')
	submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
	username = StringField('Username', validators = [DataRequired()])
	email = StringField('Email Address', validators = [DataRequired(), Email()])
	password = PasswordField('Password', validators = [DataRequired()])
	password2 = PasswordField(
		'Repeat Password', validators = [DataRequired(), EqualTo('password')])
	remember_me = BooleanField('Remember Me')
	submit = SubmitField('Register')

	def validate_username(self,username):
		user = User.query.filter_by(username=username.data).first()
		if user is not None:
			raise ValidationError('Username taken. Use another.')

	def validate_email(self,email):
		user = User.query.filter_by(email=email.data).first()
		if user is not None:
			raise ValidationError('Email taken. Use another.')

class AddTransactionForm(FlaskForm):
	amount = StringField('Amount', validators = [
		DataRequired(), Regexp('\d+(\.\d\d)?', message='Must be in monetary format')])
	note = StringField('Note', validators = [DataRequired()])
	add = SubmitField('Add')
	#dt = DateField('DatePicker', format='%Y-%m-%d',validators = [DataRequired()])
	listochoices = [('groceries','Groceries'),('restaurant','Restaurant'),('income','Income'),
		('entertainment','Entertainment'),('education','Education'),('shopping','Shopping'),
		('rent','Rent/Mortgage'),('taxes','Taxes'),('investments','Investments'),
		('health','Health'),('personal','Personal Care'),('interest','Credit Cards/Loans'),
		('transportation','Transportation')]
	category = SelectField('Category',choices=listochoices)
	dt = DateField('Date', format='%Y-%m-%d', validators = [Optional()])

class AddBudgetForm(FlaskForm):
	max_amount = StringField('Budget Amount', validators = [
		DataRequired(), Regexp('\d+(\.\d\d)?', message='Must be in monetary format')])
	listochoices = AddTransactionForm.listochoices
	category = SelectField('Category',choices=listochoices)
	add = SubmitField('Add')

class FilterForm(FlaskForm):
	listochoices = AddTransactionForm.listochoices
	listochoices.insert(0,('all','All'))
	category = SelectField('Category',choices=listochoices)
	dtstart = DateField('Start Date', format='%Y-%m-%d', validators = [Optional()])
	dtend = DateField('End Date', format='%Y-%m-%d', validators = [Optional()])
	add = SubmitField('Filter')
