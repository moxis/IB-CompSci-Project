from flask_table import Table, Col, BoolCol, DateCol

class AccountTable(Table):
    id = Col("#")
    username = Col("Username")
    password = Col("Password (hash)")
    is_admin = BoolCol("Admin?")

class SalonTable(Table):
    id = Col("#")
    name = Col("Name")
    address = Col("Address")
    account_id = Col("Account")

class EmployeeTable(Table):
    id = Col("#")
    name = Col("Name")
    wage = Col("Wage (%)")
    salon = Col("Salon")

class ServiceTable(Table):
    id = Col("#")
    name = Col("Name")
    price = Col("Price")

class CustomerTable(Table):
    id = Col("#")
    first_name = Col("First Name")
    last_name = Col("Last Name")
    email = Col("Email")
    dob = Col("Birth")
    address = Col("Address")
    address2 = Col("Address 2")
    city = Col("City")
    postal = Col("Zipcode")
    phone = Col("Phone")
    card_id = Col("Card ID")

class SaleTable(Table):
    id = Col("#")
    date = Col("Date")
    service_id = Col("Service")
    quantity = Col("Quantity")
    total = Col("Total Price")
    employee_id = Col("Employee")
    discount = Col("Discount")
    customer_id = Col("Customer")

class InventoryTable(Table):
    id = Col("#")
    name = Col("Item")
    quantity = Col("Quantity")
    salon = Col("Salon")
