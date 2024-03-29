# An instance of the Flask class will be our WSGI application
from flask import Flask, request, Response

from pymongo import MongoClient  # To get a Database instance from MongoClient

import json  # To decode request data and encode response data as JSON
import time  # Used in session generation
import uuid  # Used in session generation

from bson.objectid import ObjectId

from datetime import date  # To get current year in 'age' function

import os


mongodb_hostname = os.environ.get('MONGO_HOSTNAME','localhost')


# Get a Database instance of our MongoDB
client = MongoClient('mongodb://' + mongodb_hostname + ':27017/')


# Access the 'DSPharmacy' database
db = client['DSPharmacy']

users = db['Users']        # Access the 'Users' collection
products = db['Products']  # Access the 'Products' collection


# Initialize the application as an instance of the Flask class
app = Flask(__name__)


sessions = {}


# Helper Functions ...

def is_ssn_valid(ssn):

    # SSN should be an integer
    if not isinstance(ssn, int):
        return False

    ssn = str(ssn)

    # SSN should be 11-digits long
    if len(ssn) != 11:
        return False

    #                            01234567890 (indexes)
    # SSN must be in the format: DDMMYYNNNNN

    # Digits at indexes 0 and 1 represent the day of birth
    day = int(ssn[0:2])

    # Digits at indexes 2 and 3 represent the month of birth
    month = int(ssn[2:4])

    if not (1 <= day <= 31):
        return False
    if not (1 <= month <= 12):
        return False

    return True


def generate_session(handle, category):

    # Generate the session's uuid
    session_id = str(uuid.uuid4())

    # Generate the session's content

    if (category == 'administrator'):
        handle_type = 'username'
    else:
        handle_type = 'email'

    session_content = {
        handle_type: handle,
        'category':  category,
        'timestamp': time.time()
    }

    if category == 'user':
        session_content['cart'] = {
            'products': {},
            'total': 0.0
        }

    # Add session into sessions-dictionary
    sessions[session_id] = session_content

    return session_id


def is_authorized(category='any'):

    # Request-Header-Authorization-Key Validation ...

    auth = None

    try:
        auth = request.headers['Authorization']
    except Exception:
        return 401

    if auth == None or auth not in sessions:
        return 401

    if category == 'any':
        return auth

    # Administrator Authorization Check ...
    if category == 'administrator':
        if sessions[auth]['category'] != 'administrator':
            return 403

    # User Authorization Check ...
    if category == 'user':
        if sessions[auth]['category'] != 'user':
            return 403

    return auth


def age(ssn):
    birth_year = int(str(ssn)[4:6])
    current_year = int(str(date.today().year)[2:4])

    if current_year < birth_year:
        current_year += 100

    return current_year - birth_year


def is_credit_valid(credit):

    # Credit should be an integer
    if not isinstance(credit, int):
        return False

    credit = str(credit)

    # Credit should be 16-digits long
    if len(credit) != 16:
        return False

    return True


# Endpoints (Routes and Functions) ...


# Guest Endpoints ...


# 01. Sign-Up
@app.route('/signup', methods=['POST'])
def signup():

    # Request-Body-JSON-Data Validation ...

    data = None

    try:
        data = json.loads(request.data)
    except Exception:
        return Response('Bad Request',
                        status=400,
                        mimetype='application/json')

    if (data == None or
            'name' not in data or
            'email' not in data or
            'password' not in data or
            'ssn' not in data or
            not is_ssn_valid(data['ssn'])):
        return Response('Unprocessable Entity',
                        status=422,
                        mimetype='application/json')

    # Conflict Detection ...

    # A conflict may occur,
    # if a user with the provided email or ssn
    # is already present in the database

    result = users.find_one({'$or': [
        {'email': data['email']},
        {'ssn': data['ssn']}
    ]})

    if result != None:
        return Response('Conflict',
                        status=409,
                        mimetype='application/json')

    # Insert New User ...

    users.insert_one({
        'ssn': data['ssn'],
        'name': data['name'],
        'email': data['email'],
        'password': data['password'],
        'category': 'user',
        'orderHistory': []
    })

    return Response('OK',
                    status=200,
                    mimetype='application/json')


# 02. Log-In
@app.route('/login', methods=['POST'])
def login():

    # Request-Body-JSON-Data Validation ...

    data = None

    try:
        data = json.loads(request.data)
    except Exception:
        return Response('Bad Request',
                        status=400,
                        mimetype='application/json')

    if (data == None or
            'password' not in data or
            'username' not in data and 'email' not in data):
        return Response('Unprocessable Entity',
                        status=422,
                        mimetype='application/json')

    # Authentication Check ...

    if 'username' in data:
        handle = 'username'
    else:
        handle = 'email'

    result = users.find_one(
        {handle: data[handle], 'password': data['password']})

    if result == None:
        return Response('Unauthorized',
                        status=401,
                        mimetype='application/json')

    # Authorization Check ...
    session_id = generate_session(result[handle], result['category'])

    # Response ...

    response = {}
    response['Authorization'] = session_id
    response['Session Items'] = sessions[session_id]

    return Response(json.dumps(response),
                    status=200,
                    mimetype='application/json')


# Endpoints Available to Administrator and User ...


# 03. Product-Search
@app.route('/product-search', methods=['POST'])
def product_search():

    # Check Authorization ...

    auth = is_authorized()

    if auth == 401:
        return Response('Unauthorized',
                        status=401,
                        mimetype='application/json')
    if auth == 403:
        return Response('Forbidden',
                        status=403,
                        mimetype='application/json')

    # Request-Body-JSON-Data Validation ...

    data = None

    try:
        data = json.loads(request.data)
    except Exception:
        return Response('Bad Request',
                        status=400,
                        mimetype='application/json')

    if data == None:
        return Response('Unprocessable Entity',
                        status=422,
                        mimetype='application/json')

    # Find Products ...

    if '_id' in data:  # Find Product By _id ...
        results = products.find({'_id': ObjectId(data['_id'])})

    elif 'name' in data:  # Find Products By name ...
        results = products.find(
            {'name': {'$regex': data['name'].lower()}}).sort('price')

    elif 'category' in data:  # Find Products By category ...
        results = products.find(
            {'category': {'$regex': data['category'].lower()}}).sort('price')

    else:
        return Response('Unprocessable Entity',
                        status=422,
                        mimetype='application/json')

    # Response ...

    response = []  # Initialize the response array
    # Construct the response array
    for result in results:
        product = {
            # ObjectId would be problematic in JSON encoding,
            # so it is replaced by its string representation
            'Product ID': str(result['_id']),
            'Product Information': {
                'name': result['name'],
                'price': result['price'],
                'category': result['category'],
                'description': result['description']
            }
        }

        response.append(product)

    if len(response) == 0:
        return Response('Not Found',
                        status=404,
                        mimetype='application/json')

    return Response(json.dumps(response),
                    status=200,
                    mimetype='application/json')


# Administrator Endpoints ...


# 04. Create-Product
@app.route('/admin/create-product', methods=['POST'])
def create_product():

    # Check Authorization ...

    auth = is_authorized('administrator')

    if auth == 401:
        return Response('Unauthorized',
                        status=401,
                        mimetype='application/json')
    if auth == 403:
        return Response('Forbidden',
                        status=403,
                        mimetype='application/json')

    # Request-Body-JSON-Data Validation ...

    data = None

    try:
        data = json.loads(request.data)
    except Exception:
        return Response('Bad Request',
                        status=400,
                        mimetype='application/json')

    if (data == None or
            'name' not in data or
            'category' not in data or
            'description' not in data or
            'stock' not in data or
            not isinstance(data['stock'], int) or
            data['stock'] < 0 or
            'price' not in data or
            not isinstance(data['price'], (int, float)) or
            data['price'] < 0.0):
        return Response('Unprocessable Entity',
                        status=422,
                        mimetype='application/json')

    # Insert New Product ...

    products.insert_one({
        'name': data['name'].lower(),
        'category': data['category'].lower(),
        'price': data['price'],
        'stock': data['stock'],
        'description': data['description']
    })

    return Response('OK',
                    status=200,
                    mimetype='application/json')


# 05. Update-Product
@app.route('/admin/update-product', methods=['PUT'])
def update_product():

    # Check Authorization ...

    auth = is_authorized('administrator')

    if auth == 401:
        return Response('Unauthorized',
                        status=401,
                        mimetype='application/json')
    if auth == 403:
        return Response('Forbidden',
                        status=403,
                        mimetype='application/json')

    # Request-Body-JSON-Data Validation ...

    data = None

    try:
        data = json.loads(request.data)
    except Exception:
        return Response('Bad Request',
                        status=400,
                        mimetype='application/json')

    if (data == None or
            '_id' not in data or
            'stock' in data and
            (not isinstance(data['stock'], int) or data['stock'] < 0) or
            'price' in data and
            (not isinstance(data['price'], (int, float)) or data['price'] < 0)):
        return Response('Unprocessable Entity',
                        status=422,
                        mimetype='application/json')

    # Update Product ...

    update_set = {}

    for key in ['name', 'category', 'description', 'price', 'stock']:
        if key == '_id':
            continue
        if key in data:
            update_set[key] = data[key]

    if len(update_set.keys()) == 0:
        return Response('Unprocessable Entity',
                        status=422,
                        mimetype='application/json')

    try:
        if products.update_one({'_id': ObjectId(data['_id'])},
                               {'$set': update_set}).modified_count == 0:
            return Response('Not Found',
                            status=404,
                            mimetype='application/json')
    except Exception:
        return Response('Internal Server Error',
                        status=500,
                        mimetype='application/json')

    return Response('OK',
                    status=200,
                    mimetype='application/json')


# 06. Delete-Product
@app.route('/admin/delete-product', methods=['DELETE'])
def delete_product():

    # Check Authorization ...

    auth = is_authorized('administrator')

    if auth == 401:
        return Response('Unauthorized',
                        status=401,
                        mimetype='application/json')
    if auth == 403:
        return Response('Forbidden',
                        status=403,
                        mimetype='application/json')

    # Request-Body-JSON-Data Validation ...

    data = None

    try:
        data = json.loads(request.data)
    except Exception:
        return Response('Bad Request',
                        status=400,
                        mimetype='application/json')

    if data == None or '_id' not in data:
        return Response('Unprocessable Entity',
                        status=422,
                        mimetype='application/json')

    # Delete Product ...

    try:
        if products.delete_one(
                {'_id': ObjectId(data['_id'])}).deleted_count == 0:
            return Response('Not Found',
                            status=404,
                            mimetype='application/json')
    except Exception:
        return Response('Internal Server Error',
                        status=500,
                        mimetype='application/json')

    return Response('OK',
                    status=200,
                    mimetype='application/json')


# User Endpoints ...


# 07. Add-To-Cart
@app.route('/user/add-to-cart', methods=['POST'])
def add_to_cart():

    # Check Authorization ...

    auth = is_authorized('user')

    if auth == 401:
        return Response('Unauthorized',
                        status=401,
                        mimetype='application/json')
    if auth == 403:
        return Response('Forbidden',
                        status=403,
                        mimetype='application/json')

    # Request-Body-JSON-Data Validation ...

    data = None

    try:
        data = json.loads(request.data)
    except Exception:
        return Response('Bad Request',
                        status=400,
                        mimetype='application/json')

    if (data == None or
            '_id' not in data or
            'quantity' not in data or
            (not isinstance(data['quantity'], int) or data['quantity'] < 1)):
        return Response('Unprocessable Entity',
                        status=422,
                        mimetype='application/json')

    # Retrieve Product ...

    result = products.find_one({'_id': ObjectId(data['_id'])})

    if result == None:
        return Response('Not Found',
                        status=404,
                        mimetype='application/json')

    # Underage users should not be able to purchase products from the categories:
    #   - analgesic
    #   - antibiotic
    #   - antiseptic

    # Retrieve user's SSN using email to calculate user's age
    user = users.find_one({'email': sessions[auth]['email']})

    if (result['category'] in ['analgesic', 'antibiotic', 'antiseptic'] and
            age(user['ssn']) < 18):
        return Response('Forbidden',
                        status=403,
                        mimetype='application/json')

    # Add Product To Cart ...

    cart = sessions[auth]['cart']

    product_id = str(result['_id'])

    if product_id not in cart['products']:

        cart['products'][product_id] = {
            'name': result['name'],
            'price': result['price'],
            'quantity': data['quantity'],
            'category': result['category'],
            'description': result['description']
        }

    else:
        quantity = cart['products'][product_id]['quantity']

        if result['stock'] < quantity + data['quantity']:
            return Response('Conflict',
                            status=409,
                            mimetype='application/json')

        cart['products'][product_id]['quantity'] += data['quantity']

    cart['total'] += data['quantity'] * result['price']

    # Response ...

    return Response(json.dumps(cart),
                    status=200,
                    mimetype='application/json')


# 08. View-Cart
@app.route('/user/view-cart', methods=['POST'])
def view_cart():

    # Check Authorization ...

    auth = is_authorized('user')

    if auth == 401:
        return Response('Unauthorized',
                        status=401,
                        mimetype='application/json')
    if auth == 403:
        return Response('Forbidden',
                        status=403,
                        mimetype='application/json')

    cart = sessions[auth]['cart']

    return Response(json.dumps(cart),
                    status=200,
                    mimetype='application/json')


# 09. Remove-From-Cart
@app.route('/user/remove-from-cart', methods=['DELETE'])
def remove_from_cart():

    # Check Authorization ...

    auth = is_authorized('user')

    if auth == 401:
        return Response('Unauthorized',
                        status=401,
                        mimetype='application/json')
    if auth == 403:
        return Response('Forbidden',
                        status=403,
                        mimetype='application/json')

    # Request Body JSON Data Validation ...

    data = None

    try:
        data = json.loads(request.data)
    except Exception:
        return Response('Bad Request',
                        status=400,
                        mimetype='application/json')

    if data == None or '_id' not in data:
        return Response('Unprocessable Entity',
                        status=422,
                        mimetype='application/json')

    # Remove Product From Cart ...

    cart = sessions[auth]['cart']

    product_id = data['_id']

    if product_id not in cart['products']:
        return Response('Not Found',
                        status=404,
                        mimetype='application/json')

    quantity = cart['products'][product_id]['quantity']
    price = cart['products'][product_id]['price']

    cart['total'] -= quantity * price

    del cart['products'][product_id]

    # Correct for Float arithmetic error:
    # some times total should reach zero
    # but was slightly negative instead.
    if cart['total'] < 0.0:
        cart['total'] = 0.0

    # Response ...

    return Response(json.dumps(cart),
                    status=200,
                    mimetype='application/json')


# 10. Checkout
@app.route('/user/checkout', methods=['POST'])
def checkout():

    # Check Authorization ...

    auth = is_authorized('user')

    if auth == 401:
        return Response('Unauthorized',
                        status=401,
                        mimetype='application/json')
    if auth == 403:
        return Response('Forbidden',
                        status=403,
                        mimetype='application/json')

    # Request Body JSON Data Validation ...

    data = None

    try:
        data = json.loads(request.data)
    except Exception:
        return Response('Bad Request',
                        status=400,
                        mimetype='application/json')

    if (data == None or
            'credit' not in data or (not is_credit_valid(data['credit']))):
        return Response('Unprocessable Entity',
                        status=422,
                        mimetype='application/json')

    cart = sessions[auth]['cart']
    receipt = {
        'products': {},
        'total': 0.0
    }

    has_skipped = False  # flags if a product was skipped due to insufficient stock

    # For each product in the cart
    # retreive the product's stock
    # if the stock is sufficient,
    # update the product' stock by subtracting the quantity
    # then remove the product from the cart, and update total
    # add the product to the receipt, and update receipt total

    for product_id in list(cart['products']):

        product = products.find_one({'_id': ObjectId(product_id)})

        price = cart['products'][product_id]['price']
        quantity = cart['products'][product_id]['quantity']

        if product['stock'] < quantity:
            has_skipped = True
            continue

        products.update_one({'_id': ObjectId(product_id)}, {
                            '$inc': {'stock': - quantity}})

        cart['total'] -= quantity * price
        receipt['total'] += quantity * price

        receipt['products'][product_id] = cart['products'][product_id]

        del cart['products'][product_id]

    # Correct for Float arithmetic error:
    # some times total should reach zero
    # but was slightly negative instead.
    if cart['total'] < 0.0:
        cart['total'] = 0.0

    # If any products in the cart couldn't be purchased,
    # add a message to the receipt informing the client.
    if has_skipped:
        receipt['message'] = "Order Incomplete Due To Insufficient Stock - Check Cart"

    receipt['timestamp'] = time.time()

    # Add receipt to orderHistory
    email = sessions[auth]['email']
    users.update_one({'email': email}, {'$push': {'orderHistory': receipt}})

    return Response(json.dumps(receipt),
                    status=200,
                    mimetype='application/json')


# 11. View-Order-History
@app.route('/user/view-order-history', methods=['POST'])
def view_order_history():

    # Check Authorization ...

    auth = is_authorized('user')

    if auth == 401:
        return Response('Unauthorized',
                        status=401,
                        mimetype='application/json')
    if auth == 403:
        return Response('Forbidden',
                        status=403,
                        mimetype='application/json')

    # Retrieve user's orderHistory using email

    user_email = sessions[auth]['email']

    user = users.find_one({'email': user_email})

    order_history = user['orderHistory']

    # Response ...

    return Response(json.dumps(order_history),
                    status=200,
                    mimetype='application/json')


# 12. Delete-Account
@app.route('/user/delete-account', methods=['DELETE'])
def delete_account():

    # Check Authorization ...

    auth = is_authorized('user')

    if auth == 401:
        return Response('Unauthorized',
                        status=401,
                        mimetype='application/json')
    if auth == 403:
        return Response('Forbidden',
                        status=403,
                        mimetype='application/json')

    user_email = sessions[auth]['email']

    del sessions[auth]
    users.delete_one({'email': user_email})

    return Response('OK',
                    status=200,
                    mimetype='application/json')


if __name__ == '__main__':
    # run the application with a development server
    # in debug mode, on localhost, at port 5000
    app.run(debug=True, host='0.0.0.0', port=5000)
