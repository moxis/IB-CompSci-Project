from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, BooleanField, DateTimeField, DecimalField, IntegerField, SelectField, PasswordField
from wtforms.validators import DataRequired, Email, Length
from .models import *
# FORMS


def get_selection(obj): # querying through tables to make combobox choices
    options = [(None, "")]
    selection = obj.query.all()
    for i in range(0, len(selection)):
        options.append((selection[i].id, selection[i].name))
    return options

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    #recaptcha = RecaptchaField()

class DeleteForm(FlaskForm):
    id = IntegerField('ID')


class AccountForm(FlaskForm):
    id = IntegerField('ID')
    username = StringField('Username', validators=[
        Length(max=12)])
    password = StringField('Password', validators=[
        Length(max=12)])
    is_admin = BooleanField('Admin', default=False)


class SalonForm(FlaskForm):
    id = IntegerField('ID')
    name = StringField('Name', validators=[Length(max=50)])
    address = StringField('Address', validators=[Length(max=100)])
    account_id = SelectField('Link Account')

    @classmethod
    def new(cls):
        form = cls()

        options = [(None, "")]
        selection = Account.query.all()
        for i in range(0, len(selection)):
            options.append((selection[i].id, selection[i].username))
        form.account_id.choices = options
        return form


class EmployeeForm(FlaskForm):
    id = IntegerField('ID')
    name = StringField('Name', validators=[Length(max=50)])
    wage = IntegerField('Wage Rate')
    salon_id = SelectField('Link Salon')

    @classmethod
    def new(cls):
        form = cls()

        options = get_selection(Salon)
        form.salon_id.choices = options
        return form


class ServiceForm(FlaskForm):
    id = IntegerField('ID')
    name = StringField('Name', validators=[Length(max=50)])
    price = DecimalField('Price', number_format='%0.2f')


class CustomerForm(FlaskForm):
    id = IntegerField('ID')
    first_name = StringField('First Name', validators=[Length(max=50)])
    last_name = StringField('Last Name', validators=[Length(max=50)])
    email = StringField('Email', validators=[Email(
        message='Invalid Email!'), Length(max=100)])
    dob = DateTimeField('Date of Birth', format='%d/%m/%Y', validators=[])
    address = StringField('Address', validators=[Length(max=100)])
    address2 = StringField('Secondary Address', validators=[Length(max=100)])
    city = StringField('City', validators=[Length(max=30)])
    postal = IntegerField('Zipcode', validators=[])
    phone = IntegerField('Phone', validators=[])
    card_id = IntegerField('Card ID', validators=[])


class SalesForm(FlaskForm):
    id = IntegerField('ID')
    quantity = IntegerField('Quantity')
    employee_id = SelectField('Employee ID')
    service_id = SelectField('Service ID')
    customer_id = IntegerField('Customer ID')
    discount = IntegerField('Discount')

    @classmethod
    def new(cls):
        form = cls()

        options = get_selection(Employee)
        form.employee_id.choices = options

        options = get_selection(Service)
        form.service_id.choices = options
        return form


class InventoryForm(FlaskForm):
    id = IntegerField('ID')
    name = StringField('Name', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    salon_id = SelectField('Salon', validators=[
                           DataRequired()])

    @classmethod
    def new(cls):
        form = cls()

        options = get_selection(Salon)
        form.salon_id.choices = options
        return form
