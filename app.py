# An instance of the Flask class will be our WSGI application
from flask import Flask
from pymongo import MongoClient  # To get a Database instance from MongoClient


import json                      # To decode request data and encode response data as JSON

from flask import Response
from flask import request


import time                      # Used in session generation
import uuid                      # Used in session generation








# Initialize the application as an instance of the Flask class
app = Flask(__name__)








# Get a Database instance of our MongoDB
client = MongoClient('mongodb://localhost:27017/')


db = client['DSPharmacy']  # Access the 'DSPharmacy' database

users    = db['Users']     # Access the 'Users' collection
products = db['Products']  # Access the 'Products' collection








def is_ssn_valid(ssn):

    if not isinstance(ssn, str): ssn = str(ssn)


    # SSN Must be an 11-digit Numeric String
    if len(ssn) != 11 or not ssn.isnumeric(): return False


    # SSN must be in the format: DDMMYYNNNNN

    day   = int(ssn[0:2])  # Digits at indexes 0 and 1 represent the day of birth
    month = int(ssn[2:4])  # Digits at indexes 2 and 3 represent the month of birth

    if not (1 <=  day  <= 31): return False  # Day   must be between 1 and 31
    if not (1 <= month <= 12): return False  # Month must be between 1 and 12


    return True




sessions = {}


def generate_session(handle, category):


    session_id = str(uuid.uuid4())

    handle_type = 'username' if (category == 'administrator') else 'email'

    session_content = {
        handle_type: handle,
        'category':  category,
        'timestamp': time.time()
    }

    sessions[session_id] = session_content


    return session_id




@app.route('/get-sessions')
def get_sessions():
    return Response(json.dumps(sessions), status=200, mimetype='application/json')




# 1. Sign-Up
@app.route('/signup', methods=['POST'])
def signup():


    # Request Body JSON Data Validation ...

    data = None

    try:
        data = json.loads(request.data)
    except Exception:
        return Response('Bad Request', status=400, mimetype='application/json')

    if (data == None or
            'name'     not in data or
            'email'    not in data or
            'password' not in data or
            'ssn'      not in data or not is_ssn_valid(data['ssn'])):

        return Response('Unprocessable Entity', status=422, mimetype='application/json')

    ssn = str(data['ssn'])  # Convert ssn to string (in case it is an integer)


    # Conflict Resolution ...

    conflict = users.find_one({'$or': [
        {'email': data['email']},
        {'ssn': ssn}
    ]})

    if conflict != None:
        return Response('Conflict', status=409, mimetype='application/json')


    # Insert New User ...
    users.insert_one({
        'name':     data['name'],
        'email':    data['email'],
        'password': data['password'],
        'ssn':      ssn,
        'category': 'user'
    })

    return Response('Success', status=200, mimetype='application/json')





# 2. Log-In
@app.route('/login', methods=['POST'])
def login():


    # Request Body JSON Data Validation ...

    data = None

    try:
        data = json.loads(request.data)
    except Exception:
        return Response('Bad Request', status=400, mimetype='application/json')

    if (data == None or
            'password' not in data or
            'username' not in data and 'email' not in data):

        return Response('Unprocessable Entity', status=422, mimetype='application/json')


    # Authentication ...

    handle = 'username' if ('username' in data) else 'email'

    user = users.find_one({handle: data[handle], 'password': data['password']})

    if user == None:
        return Response('Unauthorized', status=401, mimetype='application/json')


    # Authorization ...

    session_id = generate_session(user[handle], user['category'])


    # Response ...

    response = {}

    response['Authorization'] = session_id
    response['Session Items'] = sessions[session_id]

    return Response(json.dumps(response), status=200, mimetype='application/json')




# 3. Create-Product
@app.route('/admin/create-product', methods=['POST'])
def create_product():


    # Header Authorization Key Validation ...

    auth = None

    try:
        auth = request.headers['Authorization']
    except Exception:
        return Response('Unauthorized', status=401, mimetype='application/json')

    if auth == None or auth not in sessions:
        return Response('Unauthorized', status=401, mimetype='application/json')


    # Administrator Authorization Check ...

    if sessions[auth]['category'] != 'administrator':
        return Response('Forbidden', status=403, mimetype='application/json')


    # Request Body JSON Data Validation ...

    data = None

    try:
        data = json.loads(request.data)
    except Exception:
        return Response('Bad Request', status=400, mimetype='application/json')

    if (data == None or
            'name'        not in data or 
            'category'    not in data or
            'description' not in data or
            'stock'       not in data or not isinstance(data['stock'], int)   or data['stock'] < 0 or
            'price'       not in data or not isinstance(data['price'], (int, float)) or data['price'] < 0):

        return Response('Unprocessable Entity', status=422, mimetype='application/json')


    # Insert New Product ...

    products.insert_one({
        'name':        data['name'],
        'category':    data['category'],
        'description': data['description'],
        'price':       data['price'],
        'stock':       data['stock']
    })


    return Response('Success', status=200, mimetype='application/json')




# 4. Product-Search
@app.route('/product-search', methods=['POST'])
def product_search():

    results = products.find()  # Retrieve all products

    response = []              # Initialize the response array

    # Construct the response array
    for result in results:
        # ObjectId would be problematic in JSON encoding,
        # so it is replaced by its string representation
        result['_id'] = str(result['_id'])

        response.append(result)


    return Response(
            json.dumps(response),
            status=200, mimetype='application/json')








if __name__ == '__main__':

    # run the application with a development server
    # in debug mode, on localhost, at port 5000
    
    app.run(debug=True, host='0.0.0.0', port=5000)
