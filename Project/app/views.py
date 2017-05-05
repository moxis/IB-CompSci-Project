from werkzeug.security import check_password_hash, generate_password_hash
from flask import render_template, flash, redirect, url_for, request, g, make_response, abort
from flask_login import login_user, logout_user, current_user, login_required
from functools import wraps
from app import app, db, lm
import configparser
import pdfkit
import json
from .forms import *
from .models import *


@lm.user_loader
def load_user(id):
    return Account.query.get(int(id))


@app.before_request
def before_request():
    config = configparser.ConfigParser()
    config.read('config.ini')
    whitelist = config.getboolean('WHITELIST', 'enabled') # boolean of whether whitelisting is enabled
    whitelisted_ip = config.get('WHITELIST', 'IPs').split(',') # array of IPs that are in whitelist
    if whitelist and request.remote_addr not in whitelisted_ip: # if whitelist enabled and ip not in whitelist
        abort(403) # deny access
    else:
        g.user = current_user # initialize user session


def admin_required(f): # wrapper for admin required pages only
    @wraps(f)
    def wrap(*args, **kwargs):
        if g.user.is_admin: # check whether user has admin rights
            return f(*args, **kwargs)
        else:
            return redirect(url_for('data')) # else redirect to data page which is accessible by all users
    return wrap

@app.route('/settings/', methods=['GET', 'POST'])
@login_required
@admin_required
def setting():
    config = configparser.ConfigParser() # initialize new configuration template
    config.read('config.ini') # read the configuration file

    if request.method == 'POST': # if POST request is submitted
        try:
            ticked = str(request.form['check']) # attempt to get the value of checkbox
        except:
            ticked = 'off' # if attempt failed it means that the checkbox is unticked

        config.set('WHITELIST', 'enabled', ticked) # set config enabled as ticked value
        data = str(request.form['ip'].split('\n')) # split textarea input for every newline and turn the list into a string
        for letter in {"[", "]", r'\r', "'", " "}: # for loop of characters that need to be removed
            data = data.replace(letter, '') # replace the charactes by blank string
        config.set('WHITELIST', 'IPs', data) # set config whitelisted ips as the filtered textarea

        with open('config.ini', 'w') as configfile: # open configuration in write mode
            config.write(configfile) # rewrite the configuration file

    whitelist = config.getboolean('WHITELIST', 'enabled') # get whether whitelist is enabled from config file
    whitelisted_ip = config.get('WHITELIST', 'IPs').split(',') # get whitelisted ips from config file

    return render_template('setting.html', title="Settings", whitelist=whitelist, whitelisted_ip=whitelisted_ip)

@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm() # initialize a new login form object
    if g.user.is_authenticated: # if user already logged in
        return redirect(url_for('dashboard'))  # redirect user to dashboard
    else:
        if form.validate_on_submit(): # if form is valid so captcha solved and no empty fields
            user = Account.query.filter_by(
                username=form.username.data).first() # query accounts table for inputted username and return the first entry
            if user is not None: # if user exists
                if check_password_hash(user.password, form.password.data): # check whether input password hash matches the hash on database
                    login_user(user) # set logged in session to user
                    return redirect(url_for('index')) # redirect client to index
            flash("Invalid username or password!") # if not redirected display error message
        else:
            flash("Error in validating your request!") # form not valid display error message

    return render_template('login.html', form=form)


@app.route('/')
def index():
    if g.user.is_authenticated: # if user logged in
        if g.user.is_admin: # if user is admin
            return redirect(url_for('dashboard')) # if true redirect to dashboard
        else:
            return redirect(url_for('data')) # else false redirect to data page
    else:
        return redirect(url_for('login')) # else user not logged in so redirect client to login page


@app.route('/dashboard/', methods=['POST', 'GET'])
@login_required
@admin_required
def dashboard():
    salons = Salon.query.all() # get all entries from salon table
    sales = Sale.query.all() # get all entries from sales tables
    services = Service.query.all() # get all entries from services table
    piedata = []
    bardata = []
    linedata = [[0, (datetime.datetime.now() - datetime.timedelta(days=y)
                     ).strftime("%Y-%m-%d")] for y in range(30)] # initialize x-axis for line graph for 30 days

    output = ""

    if request.method == 'POST': # if POST request is submitted
        if request.form['submit'] == 'calc_revenue': # to check whether submitted request is asking to calculate revenue
            i = 0
            employee = request.form['employee_choice'] # get selected employee
            for sale in sales: # loop every entry in sales array
                if sale.employee.name == employee and (datetime.datetime.now() - sale.date).days <= int(request.form['duration_choice']): # if employee of entry equals employee selected AND date is less than selected time range
                    i += (sale.service.price * sale.quantity * (100 -
                                                                sale.discount) / 100) * sale.employee.wage_rate / 100 # calculate profit for employee and add it to the sum i
            output = "%s - %s czk" % (employee, str(round(i, 2))) # format float value into a string of ____ czk

    for service in services: # loop for every entry in services
        i = 0
        for sale in sales: # loop for every sale in sales
            if sale.service.name == service.name: # check whether service of sale equals service from loop
                i += sale.quantity # if true increment the counter by quantity of the sale
        piedata.append([service.name, i]) # at the end of the service loop append data into pie data array

    for salon in salons: # loop for every entry in salons
        i = 0
        for sale in sales: # loop for every sale in sales
            if sale.employee.salon.name == salon.name: # check whether name of salon of employer of sale equals name of salon
                i += sale.service.price * sale.quantity * \
                    (100 - sale.discount) / 100 # calculate revenue of the sale and add it to counter
        bardata.append([salon.name, i]) # at the end of the sales loop append data into bar data array that shows best selling services

    now = datetime.datetime.now()
    for sale in sales: # looping through the sales
        i = (now - sale.date).days # calculate the difference in days between now and then
        if i in range(30): # if difference in days is within the 30 day range then
            linedata[i][0] += sale.service.price * \
                sale.quantity * (100 - sale.discount) / 100 # modify the price value on the line graph data array

    return render_template('dashboard.html', title="Dashboard", piedata=piedata, bardata=bardata, linedata=linedata[::-1], employee=Employee.query.all(), output=output)


@app.route('/data/', methods=['GET', 'POST'])
@login_required
def data():
    active_id = 0 # the active tab determinant
    errormessage = 'Please fill in all the fields!' # default error message
    integererror = '%s should be a number!' # default error message for non integer inputs

    def get_userOBJ(item, mode): # function to get related user depending on how they are connected
        if mode is None: # if none then there are no or no need to check what user it is related to
            return g.user
        elif mode == "emp": # if object is related to an employee from which you can relate to a salon then to a user
            return item.employee.salon.user
        elif mode == "sal":
            return item.salon.user # if object is related to a salon from which you can relate to a user

    def loop_through_data(data, query=None, active_id=None, mode=None): # function to populate the table
        r = []
        for table in data: # loop through all the accessible tables
            items = []
            database = table[0]
            if data.index(table) == active_id and query is not None: # if a query has been requested and check which field it is requesting
                mode = mode.lower()
                if mode == 'id':
                    nest = database.query.filter_by(id=query)
                elif mode == 'username':
                    nest = database.query.filter_by(username=query)
                elif mode == 'password':
                    nest = database.query.filter_by(password=query)
                elif mode == 'is_admin':
                    nest = database.query.filter_by(is_admin=query)
                elif mode == 'name':
                    nest = database.query.filter_by(name=query)
                elif mode == 'address':
                    nest = database.query.filter_by(address=query)
                elif mode == 'wage rate':
                    nest = database.query.filter_by(
                        wage_rate=query)
                elif mode == 'price':
                    nest = database.query.filter_by(price=query)
                elif mode == 'first name':
                    nest = database.query.filter_by(
                        first_name=query)
                elif mode == 'last name':
                    nest = database.query.filter_by(
                        last_name=query)
                elif mode == 'email':
                    nest = database.query.filter_by(email=query)
                elif mode == 'dob':
                    nest = database.query.filter_by(dob=query)
                elif mode == 'city':
                    nest = database.query.filter_by(city=query)
                elif mode == 'postal':
                    nest = database.query.filter_by(postal=query)
                elif mode == 'phone':
                    nest = database.query.filter_by(phone=query)
                elif mode == 'card id':
                    nest = database.query.filter_by(card_id=query)
                elif mode == 'date':
                    nest = database.query.filter_by(date=query)
                elif mode == 'quantity':
                    nest = database.query.filter_by(quantity=query)
                elif mode == 'employee':
                    nest = database.query.filter_by(
                        employee_id=Employee.query.filter_by(name=query).first().id)
                elif mode == 'service':
                    nest = database.query.filter_by(
                        service_id=Service.query.filter_by(name=query).first().id)
                elif mode == 'customer id':
                    nest = database.query.filter_by(
                        customer_id=Customer.query.filter_by(card_id=query).first().id)
                elif mode == 'salon':
                    nest = database.query.filter_by(
                        salon_id=Salon.query.filter_by(name=query).first().id)
            else:
                nest = database.query # if not populate the table with all entries

            for item in nest.all()[::-1]: # loop every entry in the table which is reversed so the newer entries appear first
                if get_userOBJ(item, table[1]) != g.user: # check whether user of item matches the current user
                    continue # if not continue the loop without doing anything
                else: # otherwise the entry belongs to that user so add it to the array that will be used to populate the html table
                    items.append(item.get_item())
            r.append([database, database.__htmlfunc__(items)]) # append table and the data for that table
        return r

    if g.user.is_admin: # checking whether user has admin rights
        data = [[Account, None], [Salon, None], [Employee, None], [
            Service, None], [Customer, None], [Sale, None], [Inventory, None]] # determining what tables are available for that type of user
    else:
        data = [[Sale, "emp"], [Inventory, "sal"]] # determining what tables are available for that type of user

    forms = { # dictionary of forms for new and update entries
        'Delete': DeleteForm(),
        'Account': AccountForm(),
        'Salon': SalonForm().new(), # .new() is to repopulate the foreign key choices after a new entry has been added
        'Employee': EmployeeForm().new(),
        'Service': ServiceForm(),
        'Customer': CustomerForm(),
        'Sales': SalesForm().new(),
        'Inventory': InventoryForm().new(),
    }

    # the handling of request for specific tables
    def employee_request(r):
        form = forms['Employee']
        if "new" in r:
            if all(x not in {form.name.data, form.salon_id.data} for x in ["None", ""]): # data required validation
                if str(form.wage.data).isdigit() and form.wage.data in list(range(1, 101)): # digit validation
                    entry = Employee(form.name.data, form.wage.data,
                                     Salon.query.filter_by(id=form.salon_id.data).first())
                    db.session.add(entry)
                else:
                    flash(integererror % "Wage")
            else:
                flash(errormessage)
        elif "edit" in r:
            entry = Employee.query.filter_by(id=form.id.data).first()
            if form.name.data != "":
                entry.name = form.name.data
            if str(form.wage.data) is not None:
                if str(form.wage.data).isdigit() and form.wage.data in list(range(1, 101)):
                    entry.wage_rate = form.wage.data
                else:
                    flash(integererror % "Wage")
            if form.salon_id.data != "None":
                entry.salon = Salon.query.filter_by(
                    id=form.salon_id.data).first()

    def salon_request(r):
        form = forms['Salon']
        if "new" in r:
            if all(x not in {form.name.data, form.address.data, form.account_id.data} for x in ["", "None"]):
                entry = Salon(form.name.data, form.address.data, Account.query.filter_by(
                    id=form.account_id.data).first())
                db.session.add(entry)
            else:
                flash(errormessage)
        elif "edit" in r:
            entry = Salon.query.filter_by(id=form.id.data).first()
            if form.name.data != "":
                entry.name = form.name.data
            if form.address.data != "":
                entry.address = form.address.data
            if form.account_id.data != "None":
                entry.user = Account.query.filter_by(
                    id=form.account_id.data).first()

    def account_request(r):
        form = forms['Account']
        if "new" in r:
            if all(x not in {form.username.data, form.password.data} for x in ["None", ""]):
                entry = Account(form.username.data,
                                form.password.data, form.is_admin.data)
                db.session.add(entry)
            else:
                flash(errormessage)
        elif "edit" in r:
            entry = Account.query.filter_by(id=form.id.data).first()
            if form.username.data != "":
                entry.username = form.username.data
            if form.password.data != "":
                entry.password = generate_password_hash(form.password.data)
            entry.is_admin = form.is_admin.data

    def service_request(r):
        form = forms['Service']
        if "new" in r:
            if all(x not in {form.name.data, form.price.data} for x in ["None", ""]):
                if str(form.price.data).isdigit():
                    entry = Service(form.name.data, form.price.data)
                    db.session.add(entry)
                else:
                    flash(integererror % "Price")
            else:
                flash(errormessage)
        elif "edit" in r:
            entry = Service.query.filter_by(id=form.id.data).first()
            if form.name.data != "":
                entry.name = form.name.data
            if str(form.price.data) is not None:
                if str(form.price.data).isdigit():
                    entry.price = form.price.data
                else:
                    flash(integererror % "Price")

    def customer_request(r):
        form = forms['Customer']
        if "new" in r:
            if all(x not in {form.first_name.data, form.last_name.data, form.email.data, str(form.dob.data), form.address.data, form.city.data, form.postal.data, form.phone.data} for x in ["None", ""]):
                entry = Customer(form.first_name.data, form.last_name.data, form.email.data, form.dob.data, form.address.data,
                                 form.address2.data, form.city.data, form.postal.data, form.phone.data, form.card_id.data)
                db.session.add(entry)
            else:
                flash(errormessage)
        elif "edit" in r:
            entry = Customer.query.filter_by(id=form.id.data).first()
            if form.first_name.data != "":
                entry.first_name = form.first_name.data
            if form.last_name.data != "":
                entry.last_name = form.last_name.data
            if form.email.data != "":
                entry.email = form.email.data
            if form.dob.data is not None:
                entry.dob = form.dob.data
            if form.address.data != "":
                entry.address = form.address.data
            if form.address2.data != "":
                entry.address2 = form.address.data
            if form.city.data != "":
                entry.city = form.city.data
            if str(form.postal.data) is not None:
                if str(form.postal.data).isdigit():
                    entry.postal = form.postal.data
                else:
                    flash(integererror % "Postal")
            if str(form.phone.data) is not None:
                if str(form.phone.data).isdigit():
                    entry.phone = form.phone.data
                else:
                    flash(integererror % "Phone number")
            if str(form.card_id.data) is not None:
                if str(form.card_id.data).isdigit():
                    entry.card_id = form.card_id.data
                else:
                    flash(integererror % "Card ID")

    def sales_request(r):
        form = forms['Sales']
        if "new" in r:
            if all(x not in {form.quantity.data, form.service_id.data, form.employee_id.data} for x in ["None", ""]):
                if (get_userOBJ(Employee.query.filter_by(id=form.employee_id.data).first(), 'sal') == g.user) or g.user.is_admin:
                    entry = Sale(form.quantity.data, Employee.query.filter_by(id=form.employee_id.data).first(), Service.query.filter_by(id=form.service_id.data).first(
                    ), form.discount.data, Customer.query.filter_by(card_id=form.customer_id.data).first() if form.customer_id.data != "" else None)
                    db.session.add(entry)
                else:
                    flash("Access Denied!")
        elif "edit" in r and g.user.is_admin:
            entry = Sale.query.filter_by(id=form.id.data).first()
            if str(form.quantity.data) is not None:
                if str(form.quantity.data).isdigit():
                    entry.quantity = form.quantity.data
                else:
                    flash(integererror % "Quantity")
            if str(form.discount.data) is not None:
                if str(form.discount.data).isdigit() and form.discount.data in list(range(0,101)):
                    entry.discount = form.discount.data
                else:
                    flash(integererror % "Discount")
            if form.service_id.data != "None":
                entry.service_id = Service.query.filter_by(
                    id=form.service_id.data).first()
            if form.employee_id.data != "None":
                entry.employee_id = Employee.query.filter_by(
                    id=form.employee_id.data).first()
            if form.customer_id.data != "":
                entry.customer_id = Customer.query.filter_by(
                    card_id=form.customer_id.data).first()

    def inventory_request(r):
        form = forms['Inventory']
        if "new" in r:
            if all(x not in {form.name.data, form.quantity.data} for x in ["None", ""]):
                if str(form.quantity.data).isdigit():
                    entry = Inventory(form.name.data, form.quantity.data, Salon.query.filter_by(
                        id=form.salon_id.data).first() if g.user.is_admin else g.user.salon.first())
                    db.session.add(entry)
                else:
                    flash(integererror % "Quantity")
            else:
                flash(errormessage)
        elif "edit" in r:
            entry = Inventory.query.filter_by(id=form.id.data).first()
            if form.name.data != "":
                entry.name = form.name.data
            if str(form.quantity.data) is not None:
                if str(form.quantity.data).isdigit():
                    entry.quantity = form.quantity.data
                else:
                    flash(integererror % "Quantity")

    def delete_request(table):
        form = forms['Delete']
        if form.validate() and g.user.is_admin: # if form is valid with csrf token because we don't want unprivileged accounts to be deleting
            entry = table.query.filter_by(id=form.id.data).first() # query by ID to find the entry
            if g.user.is_admin: # admin accounts can delete anything
                db.session.delete(entry)
            else:
                for item in data:
                    if table == item[0]:
                        mode = item[1]
                        if get_userOBJ(entry, mode) == g.user: # checking whether user has the privilege to delete a specific entry
                            db.session.delete(entry)

    if request.method == 'POST': # checking if a POST request was submitted
        r = request.form['submit'] # get the data from the submit button
        if g.user.is_admin and forms['Account'].validate(): # checking whether user is admin because this is admin only
            if "Employee" in r: # checking for which table is in request data
                active_id = 2 # changing active tab so it doesn't go back to tab 1 after submitting
                employee_request(r)
            elif "Salon" in r:
                active_id = 1
                salon_request(r)
            elif "Account" in r:
                active_id = 0
                account_request(r)
            elif "Service" in r:
                active_id = 3
                service_request(r)
            elif "Customer" in r:
                active_id = 4
                customer_request(r)

        if forms['Delete'].validate(): # checking against crsf attacks
            if "Sales" in r:
                if g.user.is_admin:
                    active_id = 5
                else:
                    active_id = 0
                sales_request(r)
            elif "Inventory" in r:
                if g.user.is_admin:
                    active_id = 6
                else:
                    active_id = 1
                inventory_request(r)

        db.session.commit() # commit changes to the database

        if "del" in r:
            delete_request(data[active_id][0])
            db.session.commit()
            tables = loop_through_data(data) # repopulate the table after deleting an entry
        elif "export" in r:
            tables = loop_through_data(data)
            rendered = render_template('export.html', table=tables[active_id]).replace(
                "<table>", "<table class='table table-striped'>")
            pdf = pdfkit.from_string(rendered, False)
            response = make_response(pdf)
            response.headers['Content-Type'] = 'application/pdf' # setting headers for the browser
            response.headers[
                'Content-Disposition'] = 'inline; filename=output.pdf'
            return response
        elif 'filter' in r:
            tables = loop_through_data(
                data, request.form['query'], active_id, request.form['choice'])
        else:
            tables = loop_through_data(data)
    else:
        tables = loop_through_data(data)

    forms = {
        'Delete': DeleteForm(),
        'Account': AccountForm(),
        'Salon': SalonForm().new(),
        'Employee': EmployeeForm().new(),
        'Service': ServiceForm(),
        'Customer': CustomerForm(),
        'Sales': SalesForm().new(),
        'Inventory': InventoryForm().new(),
    }

    html = render_template('data.html', tables=tables, title="Data", forms=forms, active_id=active_id).replace(
        "<table>", "<table name='table' class='table table-hover table-striped'>")

    return html


@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html', title="404")
