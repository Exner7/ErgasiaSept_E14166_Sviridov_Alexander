# An instance of the Flask class will be our WSGI application
from flask import Flask
from pymongo import MongoClient  # To get a Database instance from MongoClient

import json                      # To encode response data as JSON
from flask import Response


# Initialize the application as an instance of the Flask class
app = Flask(__name__)


# Get a Database instance of our MongoDB
client = MongoClient('mongodb://localhost:27017/')

db = client['DSPharmacy']  # Access the 'DSPharmacy' database

users = db['Users']        # Access the 'Users' collection


# Test connectivity to MongoDB 'DSPharmacy' database
@app.route('/get-users')
def get_users():
    results = users.find()  # Retrieve all users
    response = []           # Initialize the response array
    # Construct the response array
    for result in results:
        # ObjectId would be problematic in JSON encoding,
        # so it is replaced by a string representation
        result['_id'] = str(result['_id'])
        response.append(result)
        return Response(json.dumps(response), status=200, mimetype='application/json')


if __name__ == '__main__':
    # run the application with a development server
    # in debug mode, on localhost, at port 5000
    app.run(debug=True, host='0.0.0.0', port=5000)
