# app.py

# Required imports
import os
from flask import Flask, request, jsonify
from firebase_admin import credentials, firestore, initialize_app

import uuid

# Initialize Flask app
app = Flask(__name__)

# Initialize Firestore DB
cred = credentials.Certificate('key.json')
default_app = initialize_app(cred)
db = firestore.client()

medical_cabinet_ref = db.collection('medical_cabinets')
doctors_ref = db.collection('doctors')

@app.route('/addNewMedicalCabinet', methods=['POST'])
def create():
    """
        create() : Add document to Firestore collection with request body.
        Ensure you pass a custom ID as part of json body in post request,
        e.g. json={'id': '1', 'title': 'Write a blog post'}
    """
    try:
        id =  str(uuid.uuid1())
        medical_cabinet_ref.document(id).set(request.json)
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"msg": "An error occured!"}), 500


@app.route('/getAllMedicalCabinet', methods=['GET'])
def getAllMedicalCabinet():
    """
        read() : Fetches documents from Firestore collection as JSON.
        todo : Return document that matches query ID.
        all_todos : Return all documents.
    """
    try:
        all_cabinets = [doc.to_dict() for doc in medical_cabinet_ref.stream()]
        return jsonify(all_cabinets), 200
    except Exception as e:
        return jsonify({"msg": "An error occured!"}), 500


@app.route('/addNewDoctor', methods=['POST'])
def addNewDoctor():
    """
        create() : Add document to Firestore collection with request body.
        Ensure you pass a custom ID as part of json body in post request,
        e.g. json={'id': '1', 'title': 'Write a blog post'}
    """
    try:
        id =  str(uuid.uuid1())
        doctors_ref.document(id).set(request.json)
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"msg": "An error occured!"}), 500


@app.route('/getAllDoctors', methods=['GET'])
def getAllDoctors():
    """
        read() : Fetches documents from Firestore collection as JSON.
        todo : Return document that matches query ID.
        all_todos : Return all documents.
    """
    try:
        all_doctors = [doc.to_dict() for doc in doctors_ref.stream()]
        return jsonify(all_doctors), 200
    except Exception as e:
        return jsonify({"msg": "An error occured!"}), 500




#############################################################################################################
@app.route('/update', methods=['POST', 'PUT'])
def update():
    """
        update() : Update document in Firestore collection with request body.
        Ensure you pass a custom ID as part of json body in post request,
        e.g. json={'id': '1', 'title': 'Write a blog post today'}
    """
    try:
        id = request.json['id']
        todo_ref.document(id).update(request.json)
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"


@app.route('/delete', methods=['GET', 'DELETE'])
def delete():
    """
        delete() : Delete a document from Firestore collection.
    """
    try:
        # Check for ID in URL query
        todo_id = request.args.get('id')
        todo_ref.document(todo_id).delete()
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"


port = int(os.environ.get('PORT', 8080))
if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=port)