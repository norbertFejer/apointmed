# app.py

# Required imports
import os
from flask import Flask, request, jsonify
from firebase_admin import credentials, firestore, initialize_app
from flask_cors import CORS, cross_origin

import uuid
from newsapi import NewsApiClient
import sys
import requests

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
specialization_ref = db.collection('specializations')
users_ref = db.collection('users')

tomTomBaseURL = "https://api.tomtom.com/search/2/geocode/"

@app.route('/')
def hello():
    return "Appointmed app is running..."


###############################################################################################################3
# Medical Cabinet Management


@app.route('/addNewMedicalCabinet', methods=['POST'])
@cross_origin()
def addNewMedicalCabinet():

    try:
        id = str(uuid.uuid1())
        request.json['id'] = id

        final_url = tomTomBaseURL + request.json['address'] + ".json?limit=1&countrySet=RO&lat=46.31226336427369&lon=25.294251672780216&language=hu-HU&key=COkueI6xY8BRyQOjFYdOAB5FqtXXs4Rk"
        data = requests.get(url = final_url).json()

        cab_location = data['results'][0]['position']
        
        request.json['lat'] = cab_location['lat']
        request.json['lon'] = cab_location['lon']

        medical_cabinet_ref.document(id).set(request.json)
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"msg": "An error occured!"}), 500


@app.route('/getAllMedicalCabinet', methods=['GET'])
def getAllMedicalCabinet():

    try:
        lat_me = request.args.get('lat')
        lon_me = request.args.get('lon')

        #default random values
        if not lat_me or float(lat_me) == 0.0:
            lat_me = 46.44355
        else:
            lat_me = float(lat_me)

        if not lon_me or float(lon_me) == 0.0:
            lon_me = 24.54084
        else:
            lon_me = float(lon_me)

        all_cabinets = [doc.to_dict() for doc in medical_cabinet_ref.stream()]

        all_cabinets = calculateRoute(lat_me, lon_me, all_cabinets)
        all_cabinets = sorted(all_cabinets, key=lambda k: k.get('lengthInMeters', 0), reverse=False)

        return jsonify(all_cabinets), 200
    except Exception as e:
        return jsonify({"msg": "An error occured!"}), 500


###############################################################################################################3
# Doctor Management

@app.route('/addNewDoctor', methods=['POST'])
def addNewDoctor():

    try:
        id =  str(uuid.uuid1())
        request.json['id'] = id
        request.json['voteCount'] = 0
        request.json['voteSum'] = 0
        request.json['score'] = 0
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


###############################################################################################################3
# Appointment Management

@app.route('/addNewAppointment', methods=['POST'])
def addNewAppointment():
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


###############################################################################################################3
# Doctor Management


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


@app.route('/getDoctorBusyDays', methods=['GET'])
def getDoctorBusyDays():

    try:
        doctor_id = request.args.get('doctor_id')
        month_id = request.args.get('month')
        if doctor_id and month_id:
            if len(month_id) == 1:
                month_id = "0" + month_id

            appointments = doctors_ref.document(doctor_id).collection('appointments').stream()

            used_days = []
            for appoint in appointments:
                # 8 means all day is full, so we program each patient in every 60 min
                if appoint.to_dict()['date'][5:7] == month_id and len(appoint.to_dict()['hour']) >= 8:
                    print(appoint.to_dict())
                    used_days.append(appoint.to_dict()['date'])

        return jsonify(used_days), 200
    except Exception as e:
        return jsonify({"msg": "An error occured!"}), 500


@app.route('/getDoctorBusyHours', methods=['GET'])
def getDoctorBusyHours():

    try:
        doctor_id = request.args.get('doctor_id')
        date_id = request.args.get('date')
        if doctor_id and date_id:

            busy_hours = doctors_ref.document(doctor_id).collection('appointments').document(date_id).get().to_dict()['hour']
            if busy_hours != None:
                print(busy_hours)
                return jsonify(busy_hours), 200

        return jsonify([]), 200
    except Exception as e:
        return jsonify({"msg": "An error occured!"}), 500

###############################################################################################################3
# Specializations

@app.route('/addNewSpecialization', methods=['POST'])
def addNewSpecialization():

    try:
        id = str(uuid.uuid1())
        request.json['id'] = id
        specialization_ref.document(id).set(request.json)
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"msg": "An error occured!"}), 500


@app.route('/getSpecializations', methods=['GET'])
def getSpecializations():

    try:
        specializations = specialization_ref.stream()

        spec_list = []
        for spec in specializations:
            spec_list.append(spec.to_dict()['name'])

        return jsonify(spec_list), 200
    except Exception as e:
        return jsonify({"msg": "An error occured!"}), 500


###############################################################################################################3
# Symptoms

@app.route('/getSymptoms', methods=['GET'])
def getSymptoms():

    try:
        specializations = specialization_ref.stream()

        symptons_list = []
        for spec in specializations:
            symptons_list =  symptons_list + spec.to_dict()['symptons']

        symptons_list = list(set(symptons_list)) 
        return jsonify(symptons_list), 200

    except Exception as e:
        return jsonify({"msg": "An error occured!"}), 500


@app.route('/getCabinetBySpecifications', methods=['GET', 'POST'])
def getCabinetBySpecifications():

    try:
        print('get specializations....')
        print(request.json)
        cabinets = medical_cabinet_ref.stream()
        cabinet_list = []

        # my current coords
        lat_me = request.args.get('lat')
        lon_me = request.args.get('lon')

        if not lat_me or float(lat_me) == 0.0:
            lat_me = 46.44355
        else:
            lat_me = float(lat_me)

        if not lon_me or float(lon_me) == 0.0:
            lon_me = 24.54084
        else:
            lon_me = float(lon_me)

        searched_specializations = request.json['specializations']
        for cabinet in cabinets:
            cabinet_id = cabinet.to_dict()['id']

            doctor_ids_dict = medical_cabinet_ref.document(cabinet_id).collection("employees").document("doctors").get().to_dict()

            if doctor_ids_dict != None:
                
                for doctor_id in doctor_ids_dict['doctor_id']:
                    doctor = doctors_ref.document(doctor_id).get().to_dict()

                    if doctor['specialization'] in searched_specializations:
                        cabinet_list.append(cabinet.to_dict())
                        break

        cabinet_list = calculateRoute(lat_me, lon_me, cabinet_list)
        cabinet_list = sorted(cabinet_list, key=lambda k: k.get('lengthInMeters', 0), reverse=False)

        return jsonify(cabinet_list), 200
    except Exception as e:
        return jsonify({"msg": e}), 500


@app.route('/getDoctorBySpecifications', methods=['GET'])
def getDoctorBySpecifications():

    try:

        searched_specializations = request.json['specializations']
        doctor_ids_dict = doctors_ref.stream()

        doctor_list = []
        for doctor in doctor_ids_dict:
            if doctor.to_dict()['specialization'] in searched_specializations:
                doctor_list.append(doctor.to_dict())


        return jsonify(doctor_list), 200
    except Exception as e:
        return jsonify({"msg": e}), 500


@app.route('/getDoctorBySymptons', methods=['GET'])
def getDoctorBySymptons():

    try:

        searched_symptons = request.json['symptons']
        specializations = specialization_ref.stream()

        found_specializations = []
        for specialization in specializations:
            for tmp_sym in specialization.to_dict()['symptons']:
                if tmp_sym in searched_symptons:
                    print(tmp_sym)
                    found_specializations.append(specialization.to_dict()['name'])

        found_specializations = list(set(found_specializations))

        doctor_ids_dict = doctors_ref.stream()
        doctor_list = []
        for doctor in doctor_ids_dict:
            if doctor.to_dict()['specialization'] in found_specializations:
                doctor_list.append(doctor.to_dict())

        return jsonify(doctor_list), 200
    except Exception as e:
        return jsonify({"msg": e}), 500


@app.route('/getCabinetBySymptons', methods=['GET', 'POST'])
def getCabinetBySymptons():

    try:

        searched_symptons = request.json['symptons']

        # my current coords
        lat_me = request.args.get('lat')
        lon_me = request.args.get('lon')

        if not lat_me or float(lat_me) == 0.0:
            lat_me = 46.44355
        else:
            lat_me = float(lat_me)

        if not lon_me or float(lon_me) == 0.0:
            lon_me = 24.54084
        else:
            lon_me = float(lon_me)

        specializations = specialization_ref.stream()

        found_specializations = []
        for specialization in specializations:
            for tmp_sym in specialization.to_dict()['symptons']:
                if tmp_sym in searched_symptons:
                    found_specializations.append(specialization.to_dict()['name'])

        found_specializations = list(set(found_specializations))

        cabinets = medical_cabinet_ref.stream()
        cabinet_list = []

        for cabinet in cabinets:
            cabinet_id = cabinet.to_dict()['id']

            doctor_ids_dict = medical_cabinet_ref.document(cabinet_id).collection("employees").document("doctors").get().to_dict()

            if doctor_ids_dict != None:

                for doctor_id in doctor_ids_dict['doctor_id']:
                    doctor = doctors_ref.document(doctor_id).get().to_dict()

                    if doctor['specialization'] in found_specializations:
                        cabinet_list.append(cabinet.to_dict())
                        break

        cabinet_list = calculateRoute(lat_me, lon_me, cabinet_list)
        cabinet_list = sorted(cabinet_list, key=lambda k: k.get('lengthInMeters', 0), reverse=False)

        return jsonify(cabinet_list), 200
    except Exception as e:
        return jsonify({"msg": e}), 500


def calculateRoute(lat_me, lon_me, cabinet_list):
    for cabinet in cabinet_list:

        baseURL = "https://api.tomtom.com/routing/1/calculateRoute/"
        final_url = baseURL + str(cabinet['lat']) + "%2C" + str(cabinet['lon']) + "%3A" + str(lat_me) + "%2C" + str(lon_me) + "/json?maxAlternatives=1&computeTravelTimeFor=all&routeRepresentation=summaryOnly&avoid=unpavedRoads&travelMode=pedestrian&key=COkueI6xY8BRyQOjFYdOAB5FqtXXs4Rk"
        data = requests.get(url = final_url).json()['routes'][0]['summary']

        cabinet['lengthInMeters'] = data['lengthInMeters']
        cabinet['travelTimeInSeconds'] = data['travelTimeInSeconds']

    return cabinet_list


def cabinetCmpByRoute(cabinet_a, cabinet_b):
    return cabinet_a['lengthInMeters'] < cabinet_b['lengthInMeters']


@app.route('/getNewsFeed', methods=['GET'])
def getNewsFeed():

    try:
        newsapi = NewsApiClient(api_key='7560ef5dce1e427897e2163a8bbb1c71')
        page_num = 1
        page_size_num = request.args.get('pageSize')

        if page_num and page_size_num:
            top_headlines = newsapi.get_top_headlines(q='vírus',
                                                        country='hu',
                                                        page=int(page_num),
                                                        page_size=int(page_size_num))

            for headline in top_headlines['articles']:
                del headline['source']

            return jsonify(top_headlines['articles']), 200
        else:
            return jsonify({"success": False}), 405
    except Exception as e:
        return jsonify({"msg": e}), 500


###############################################################################################################3
# Geocoding

@app.route('/getPositionByLocation', methods=['GET'])
def getPositionByLocation():

    try:
        location = request.args.get('location')

        if location:
            final_url = tomTomBaseURL + location + ".json?limit=1&countrySet=RO&lat=46.31226336427369&lon=25.294251672780216&language=hu-HU&key=COkueI6xY8BRyQOjFYdOAB5FqtXXs4Rk"
            data = requests.get(url = final_url).json() 
            
            return jsonify(data['results'][0]['position']), 200
        else:
            return jsonify({"success": False}), 405

    except Exception as e:
        return jsonify({"msg": "An error occured!"}), 500


def getDistanceFromStartPos(location, lat_start, lon_start):
    try:
        final_url = tomTomBaseURL + location + ".json?limit=1&countrySet=RO&lat=" + lat_start + "&lon=" + lon_start + "&language=hu-HU&key=COkueI6xY8BRyQOjFYdOAB5FqtXXs4Rk"
        data = requests.get(url = final_url).json() 
        
        return data['results'][0]['dist']

    except Exception as e:
        return None

###############################################################################################################3
# Voting system

@app.route('/voteDoctor', methods=['POST'])
def voteDoctor():

    try:
        doctor_id = request.json['doctor_id']
        score = request.json['score']

        doctor = doctors_ref.document(doctor_id).get().to_dict()
        doctor['voteCount'] = doctor['voteCount'] + 1
        doctor['voteSum'] = float(doctor['voteSum']) + float(score)
        doctor['score'] = doctor['voteSum'] / doctor['voteCount']

        doctors_ref.document(doctor_id).update({
            "voteCount": doctor['voteCount'],
            "voteSum": doctor['voteSum'],
            "score": doctor['score']
        })

        return jsonify({"success": True}), 200
    except Exception as e:
        print(e)
        print(request.json['doctor_id'], ' doctor_id--')
        print(request.json['score'], ' score--')
        return jsonify({"msg": "An error occured!"}), 500


@app.route('/getDoctorById', methods=['GET'])
def getDoctorById():

    try:
        doctor_id = request.args.get('doctor_id')

        if doctor_id:
            doctor = doctors_ref.document(doctor_id).get().to_dict()
            
            return jsonify(doctor), 200
        else:
            return jsonify({"success": False}), 405

    except Exception as e:
        return jsonify({"msg": "An error occured!"}), 500


##############################################################################
# User management


@app.route('/addNewUser', methods=['POST'])
def addNewUser():

    try:
        user_id = request.json['email']
        users_ref.document(user_id).set(request.json)

        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"msg": "An error occured!"}), 500


@app.route('/getUserById', methods=['GET'])
def getUserById():

    try:
        user_id = request.args.get('user_id')
        print(user_id)

        if user_id:
            user = users_ref.document(user_id).get().to_dict()
            return jsonify(user), 200
        else:
            return jsonify({"msg": "Parameter is missing"}), 400

    except Exception as e:
        return jsonify({"msg": "An error occured!"}), 500




port = int(os.environ.get('PORT', 8080))
if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=port)