from app import db
from .tables import *
import datetime
from werkzeug.security import generate_password_hash

# Define models


class Account(db.Model):
    __title__ = "Account"
    __htmlfunc__ = AccountTable
    __choice__ = ['ID', 'Username', 'Password', 'is_admin']
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(12), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean)
    salon = db.relationship('Salon', backref='user', lazy='dynamic')

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def get_item(self):
        item = dict(id=self.id, username=self.username,
                    password=self.password, is_admin=self.is_admin)
        return item

    def __init__(self, username, password, is_admin):
        self.username = username
        self.password = generate_password_hash(password)
        self.is_admin = is_admin

    def __repr__(self):
        return '<Account %r>' % self.username


class Salon(db.Model):
    __title__ = "Salon"
    __htmlfunc__ = SalonTable
    __choice__ = ['ID', 'Name', 'Address']
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    address = db.Column(db.String(128), nullable=False, unique=True)
    account_id = db.Column(db.Integer, db.ForeignKey(
        'account.id'), nullable=False)
    employees = db.relationship('Employee', backref='salon', lazy='dynamic')
    inventory = db.relationship('Inventory', backref='salon', lazy='dynamic')

    def get_item(self):
        item = dict(id=self.id, name=self.name,
                    address=self.address, account_id=self.user.username)
        return item

    def __init__(self, name, address, user):
        self.name = name
        self.address = address
        self.user = user

    def __repr__(self):
        return '<Salon %r>' % self.name


class Employee(db.Model):
    __title__ = "Employee"
    __htmlfunc__ = EmployeeTable
    __choice__ = ['ID', 'Name', 'Wage Rate']
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    wage_rate = db.Column(db.Integer, nullable=False)
    salon_id = db.Column(db.Integer, db.ForeignKey('salon.id'))
    sales = db.relationship('Sale', backref='employee', lazy='dynamic')

    def get_item(self):
        item = dict(id=self.id, name=self.name,
                    wage=self.wage_rate, salon=self.salon.name)
        return item

    def __init__(self, name, wage_rate, salon):
        self.name = name
        self.wage_rate = wage_rate
        self.salon = salon

    def __repr__(self):
        return '<Employee %r>' % self.name


class Service(db.Model):
    __title__ = "Service"
    __htmlfunc__ = ServiceTable
    __choice__ = ['ID', 'Name', 'Price']
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    sales = db.relationship('Sale', backref='service', lazy='dynamic')

    def get_item(self):
        item = dict(id=self.id, name=self.name, price=str(self.price) + " czk")
        return item

    def __init__(self, name, price):
        self.name = name
        self.price = price

    def __repr__(self):
        return '<Service %r>' % self.name


class Customer(db.Model):
    __title__ = "Customer"
    __htmlfunc__ = CustomerTable
    __choice__ = ['ID', 'First Name', 'Last Name', 'Email',
                  'DOB', 'Address', 'City', 'Postal', 'Phone', 'Card ID']
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    dob = db.Column(db.DateTime)
    address = db.Column(db.String(128), nullable=False)
    address2 = db.Column(db.String(128))
    city = db.Column(db.String(50), nullable=False)
    postal = db.Column(db.Integer, nullable=False)
    phone = db.Column(db.Integer, nullable=False)
    card_id = db.Column(db.Integer, nullable=False)
    sales = db.relationship('Sale', backref='customer', lazy='dynamic')

    def get_item(self):
        item = dict(id=self.id, first_name=self.first_name, last_name=self.last_name, email=self.email, dob=self.dob.date().strftime("%d/%m/%Y"), address=self.address,
                    address2=self.address2, city=self.city, postal=self.postal, phone=self.phone, card_id=self.card_id)
        return item

    def __init__(self, first_name, last_name, email, dob, address, address2, city, postal, phone, card_id):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.dob = dob
        self.address = address
        self.address2 = address2
        self.city = city
        self.postal = postal
        self.phone = phone
        self.card_id = card_id

    def __repr__(self):
        return '<Customer %r>' % self.last_name


class Sale(db.Model):
    __title__ = "Sales"
    __htmlfunc__ = SaleTable
    __choice__ = ['ID', 'Date', 'Quantity', 'Employee', 'Service', 'Customer ID']
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime)
    quantity = db.Column(db.Integer, nullable=False)
    discount = db.Column(db.Integer)
    employee_id = db.Column(db.Integer, db.ForeignKey(
        'employee.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey(
        'service.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))

    def get_item(self):
        item = dict(id=self.id, date=self.date.date().strftime("%d/%m/%Y"), service_id=self.service.name, quantity=self.quantity, total=(self.quantity * self.service.price) * (100 - (self.discount if self.discount is not None else 0)) / 100,
                    employee_id=self.employee.name, customer_id=self.customer.card_id if self.customer is not None else None, discount=self.discount)
        return item

    def __init__(self, quantity, employee, service, discount, customer):
        self.date = datetime.datetime.now().date()
        self.quantity = quantity
        self.employee = employee
        self.service = service
        self.customer = customer
        self.discount = (discount + 50) if customer is not None and customer.dob.month == datetime.datetime.now(
        ).date().month and customer.dob.day == datetime.datetime.now().date().day else 0

    def __repr__(self):
        return '<Sale %r>' % self.id


class Inventory(db.Model):
    __title__ = "Inventory"
    __htmlfunc__ = InventoryTable
    __choice__ = ['ID', 'Name', 'Quantity', 'Salon']
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    salon_id = db.Column(db.Integer, db.ForeignKey('salon.id'), nullable=False)

    def get_item(self):
        item = dict(id=self.id, name=self.name,
                    quantity=self.quantity, salon=self.salon.name)
        return item

    def __init__(self, name, quantity, salon):
        self.name = name
        self.quantity = quantity
        self.salon = salon

    def __repr__(self):
        return '<Item %r>' % self.name
