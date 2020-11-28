# app.py

# Required imports
import os
from flask import Flask, request, jsonify
from firebase_admin import credentials, firestore, initialize_app
from flask_cors import CORS, cross_origin

import uuid

import sys

# Initialize Flask app
app = Flask(__name__)

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# Initialize Firestore DB
cred = credentials.Certificate('key.json')
default_app = initialize_app(cred)
db = firestore.client()

medical_cabinet_ref = db.collection('medical_cabinets')
doctors_ref = db.collection('doctors')

@app.route('/')
def hello():
    return "Appointmed app is running..."


@app.route('/addNewMedicalCabinet', methods=['POST'])
@cross_origin()
def addNewMedicalCabinet():

    try:
        id = str(uuid.uuid1())
        request.json['id'] = id
        medical_cabinet_ref.document(id).set(request.json)
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"msg": "An error occured!"}), 500


@app.route('/getAllMedicalCabinet', methods=['GET'])
def getAllMedicalCabinet():

    try:
        all_cabinets = [doc.to_dict() for doc in medical_cabinet_ref.stream()]
        return jsonify(all_cabinets), 200
    except Exception as e:
        return jsonify({"msg": "An error occured!"}), 500


@app.route('/addNewDoctor', methods=['POST'])
def addNewDoctor():

    try:
        id =  str(uuid.uuid1())
        request.json['id'] = id
        doctors_ref.document(id).set(request.json)
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"msg": "An error occured!"}), 500


@app.route('/getAllDoctors', methods=['GET'])
def getAllDoctors():

    try:
        all_doctors = [doc.to_dict() for doc in doctors_ref.stream()]
        return jsonify(all_doctors), 200
    except Exception as e:
        return jsonify({"msg": "An error occured!"}), 500


@app.route('/addNewAppointment', methods=['POST'])
def addNewAppointment():
    print("addNewAppointment called...")
    sys.stdout.flush()
    try:
        doctor_id = request.args.get('doctor_id')
        if doctor_id:
            appointment = doctors_ref.document(doctor_id).collection("appointments").document(request.json['date'])
            app_dict = appointment.get().to_dict()

            if app_dict == None:
                request.json['hour'] = [request.json['hour']]
                appointment.set(request.json)
            else:
                app_dict['hour'].append(request.json['hour'])
                appointment.update(app_dict)

            return jsonify({"success": True}), 200
    except Exception as e:
        print(e)
        sys.stdout.flush()
        return jsonify({"msg": "An error occured!"}), 500


@app.route('/deleteAppointment', methods=['DELETE'])
def deleteAppointment():

    try:
        doctor_id = request.args.get('doctor_id')
        if doctor_id:
            appointment = doctors_ref.document(doctor_id).collection("appointments").document(request.json['date'])
            app_dict = appointment.get().to_dict()

            if app_dict == None:
                return jsonify({"no content": True}), 204
            else:
                app_dict['hour'].remove(request.json['hour'])
                appointment.update(app_dict)
                
            return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"msg": "An error occured!"}), 500


@app.route('/addNewCabinetDoctor', methods=['POST'])
def addNewCabinetDoctor():
    try:
        cabinet_id = request.args.get('cabinet_id')
        if cabinet_id:
            cab_doctors = medical_cabinet_ref.document(cabinet_id).collection("employees").document("doctors")
            cab_doctors_dict = cab_doctors.get().to_dict()

            if cab_doctors_dict == None:
                request.json['doctor_id'] = [request.json['doctor_id']]
                cab_doctors.set(request.json)
            else:
                cab_doctors_dict['doctor_id'].append(request.json['doctor_id'])
                cab_doctors.update(cab_doctors_dict)

            return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"msg": "An error occured!"}), 500


@app.route('/getCabinetDoctors', methods=['GET'])
def getCabinetDoctors():

    try:
        cabinet_id = request.args.get('cabinet_id')

        if cabinet_id:
            doctors = []
            doctor_ids_dict = medical_cabinet_ref.document(cabinet_id).collection("employees").document("doctors").get().to_dict()
            for doctor_id in doctor_ids_dict['doctor_id']:
                doctor = doctors_ref.document(doctor_id).get().to_dict()
                doctors.append(doctor)

        return jsonify(doctors), 200
    except Exception as e:
        return jsonify({"msg": "An error occured!"}), 500




port = int(os.environ.get('PORT', 8080))
if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=port)