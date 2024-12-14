import requests, base64, json, sqlite3, string, qrcode
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, render_template, request, session, make_response, redirect, url_for, flash, jsonify, send_file
from flask_paginate import Pagination, get_page_args, get_page_parameter
import secrets, uuid, time, hashlib, os, random, pytz
from datetime import datetime, timedelta
from io import BytesIO
from datetime import datetime
from mimetypes import guess_type
from io import BytesIO
from functools import wraps
import pandas as pd
import plotly.express as px
import plotly.io as pio

app = Flask(__name__, static_folder='assets', template_folder='templates')
app.config['SECRET_KEY'] = "whatsaver2024ojt"

class Database:
    def __init__(self, db_name):
        self.db_name = db_name
        self.con = None
        self.cur = None

    def connect(self):
        self.con = sqlite3.connect(self.db_name)
        self.cur = self.con.cursor()

    def close(self):
        if self.con:
            self.con.close()

    def execute(self, query, params=None):
        self.connect()
        if params:
            self.cur.execute(query, params)
        else:
            self.cur.execute(query)
        self.con.commit()
        last_id = self.cur.lastrowid
        self.close()
        return last_id

    def fetch(self, query, params=None):
        self.connect()
        if params:
            self.cur.execute(query, params)
        else:
            self.cur.execute(query)
        result = self.cur.fetchall()
        self.close()
        return result

db = Database('whatsaver.db')


@app.template_filter('occur_format')
def occur_format(date_occurence):
    date_obj = datetime.strptime(date_occurence, "%m-%d-%Y")
    formatted_date = date_obj.strftime("%d-%b-%y")
    return formatted_date

@app.template_filter('epoch_to_gmt8')
def epoch_to_datetime_gmt8(epoch_time):
    base_datetime = datetime.utcfromtimestamp(epoch_time)
    timezone_gmt8 = pytz.timezone('Etc/GMT-8')
    local_datetime = base_datetime.replace(tzinfo=pytz.utc).astimezone(timezone_gmt8)    
    formatted_datetime = local_datetime.strftime('%B %d, %Y %I:%M %p')
    return formatted_datetime

def calculate_percentage(part, whole):
    return round((part / whole) * 100, 2) if whole != 0 else 0

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged-in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/test-page', methods=['GET'])
def test_page():
    con = sqlite3.connect('whatsaver.db')
    cur = con.cursor()
    res = cur.execute("SELECT * FROM users")
    rows = res.fetchall()
    response = {'accounts': rows}
    return render_template('test-page.html', response=response)


def insert_account(data: str):
    entry = json.loads(data)
    entry.pop('status')
    entry.pop('msg')
    
    con = sqlite3.connect('whatsaver.db')
    cur = con.cursor()
    cur.execute("INSERT INTO users VALUES (Null, :username, :password, :acc_type, :fname, :lname, :cnum, :dept_name)", entry)
    con.commit()
    return


def generate_username():
    prefixes = ['dr', 'nurse', 'med', 'health', 'care', 'clinic', 'admin']
    departments = ['cardio', 'neuro', 'ortho', 'pedia', 'er', 'dental', 'rehab']
    num = str(random.randint(0, 9999)).zfill(4)
    return f"{random.choice(prefixes)}{random.choice(departments)}{num}"

def generate_password(length=10):
    if length < 8:
        raise ValueError("Password length should be at least 8 characters.")
    password_characters = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(random.choice(password_characters) for i in range(length))

@app.route('/dashboard/prcinfo/delete/<int:user_id>', methods=['GET'])
def delete_user(user_id):
    delete_query = 'DELETE FROM users WHERE userID = ?'
    db.execute(delete_query, (user_id,))
    return redirect('/dashboard/prcinfo')

def get_prc_data(offset=0, per_page=10):
    prc_logs = db.fetch("SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?", (per_page, offset))
    return prc_logs

def get_prc_total_count():
    total_count = db.fetch("SELECT COUNT(*) FROM users")[0][0]
    return total_count

@app.route('/dashboard/prcinfo/update', methods=['POST'])
def update_practitioner():
    userID = request.form['user_id']
    sud = db.fetch('SELECT * FROM users WHERE userID=:userID', {'userID': userID})[0]
    print(sud)
    
    fname = request.form['fname']
    mname = request.form['mname']  # might not exist in all cases
    lname = request.form['lname']
    contact_number = request.form['contact-number']
    email = request.form['email']
    account_type = request.form.get('acc-type', default=sud[4])
    role_type = request.form.get('role-type', default=sud[9]) #9
    med_type = request.form.get('med-type', default=sud[10]) #10
    fop = request.form.get('fop', default=sud[11]) #11


    # Complete the SQL query with all necessary fields. Adjust table and column names according to your database schema.
    sql_query = """
        UPDATE users 
        SET
            fname=:fname,
            mname=:mname,  -- Assuming 'mname' exists in the users table
            lname=:lname,
            contact_number=:contact_number,
            email=:email,
            account_type=:account_type,
            role_type=:role_type,
            med_type=:med_type,
            fop=:fop  -- Assuming 'fop' exists in the users table
        WHERE userID = :userID;
    """
    sql_data = {
        "fname": fname,
        "mname": mname,
        "lname": lname,
        "contact_number": contact_number,
        "email": email,
        "account_type": account_type,
        "role_type": role_type,
        "med_type": med_type,
        "fop": fop,
        "userID": userID
    }
    # Use execute method with a named parameter dictionary to pass data safely.
    db.execute(sql_query, sql_data)
    # return jsonify({"message": "Practitioner information updated successfully."})
    return redirect('/dashboard/prcinfo')

@app.route('/dashboard/prcinfo', methods=['GET', 'POST'])
def get_prc_page():
    user = session['user-data']
    if user[4] != 0:
        return redirect('/dashboard')
    
    if request.method == 'GET':
        users = db.fetch("SELECT * FROM users")
        roles = db.fetch("SELECT * FROM professional_roles")
        meds = db.fetch("SELECT * FROM medical_specializations")
        fop = db.fetch("SELECT * FROM field_of_practice")

        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page', per_page=10)
        total_count = get_prc_total_count()
        users = get_prc_data(offset=offset, per_page=per_page)
        pagination = Pagination(page=page, per_page=per_page, total=total_count, css_framework='bootstrap5')

        # return render_template('msi-page.html', med_safety=med_safety, pagination=pagination, page=page, per_page=per_page, total_count=total_count)
    
        return render_template('prc-page.html', users=users, roles=roles, meds=meds, fop=fop, pagination=pagination, page=page, per_page=per_page, total_count=total_count)

    if request.method == 'POST':
        created_by = f'{user[5]} {user[7][:1]}., {user[9]}'
        created_at = int(time.time())
        fname = request.form['fname']
        mname = request.form['mname']
        lname = request.form['lname']
        cnum = request.form['contact-number']
        account_type = request.form['acc-type']
        role_type = request.form['role-type']
        med_type = request.form['med-type']
        fop = request.form['fop']
        email = request.form['email']
        data = {
            'email': email,
            'username': str(generate_username()),
            'password': str(generate_password()),
            'account_type': account_type,
            'fname': fname,
            'mname': mname,
            'lname': lname,
            'contact_number': cnum,
            'role_type': role_type,
            'med_type': med_type,
            'fop': fop,
            'created_by': created_by,
            'created_at': created_at,
            'updated_at': created_at,
        }
        db.execute("INSERT INTO users VALUES (Null, :email, :username, :password, :account_type, :fname, :mname, :lname, :contact_number, :role_type, :med_type, :fop, :created_by, :created_at, :updated_at)", data)
        return redirect('/dashboard/prcinfo')

@app.route('/dashboard/prcinfo/credentials/<int:userID>')
def generate_qrcode_details(userID):
    user_data = db.fetch("SELECT * FROM users WHERE userID=:userID", {'userID': userID})[0]
    password = user_data[2]
    fname = user_data[5]
    mname = user_data[6]
    sname = user_data[7]
    qr_data = {
        "Email": user_data[1],
        "Password": user_data[2],
        "Created by": user_data[12],
        "Created at": user_data[13]
    }
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=1)
    """
    if mname:
        qr.add_data(f"{fname} {mname} {sname} credential:\n{qr_data}")
    else:
        qr.add_data(f"{fname} {sname} credential:\n{qr_data}")
    """
    qr.add_data(f"{password}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    byteIO = BytesIO()
    img.save(byteIO, 'PNG')
    byteIO.seek(0)
    return send_file(byteIO, mimetype='image/png')

@app.route('/register', methods=['GET', 'POST'])
def get_register_page():
    if request.method == 'GET':
        return render_template('reg-form.html')
    
    if request.method == 'POST':
        acc_type = request.form['account_type']
        fname = request.form['fname']
        lname = request.form['lname']
        username = str(request.form['username']).lower()
        contact_number = request.form['contact']
        npwd = request.form['npwd']
        cpwd = request.form['cpwd']
        dept_name = request.form['dept-name']
        if npwd == cpwd:
            response = {
                'username': username,
                'password': npwd,
                'acc_type': acc_type,
                'fname': fname,
                'lname': lname,
                'cnum': contact_number,
                'dept_name': dept_name,
                'status': 'success',
                'msg': 'You have successfully created a new account.'
            }
            # print(response)
            if acc_type == 'None':
                response = {'status': 'failed', 'msg': 'Select one in which type of account.'}
                return render_template('reg-form.html', response=response)
            insert_account(json.dumps(response)) # DB QUERY
            return render_template('reg-form.html', response=response)
        else:
            response = {'status': 'failed', 'msg': 'Please confirm the correct password.'}
            return render_template('reg-form.html', response=response)

    if not request.method == 'POST' or request.method == 'GET':
        return redirect('account_register')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login-form.html')
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db.fetch("SELECT * FROM users where username=:username", {'username': username})
        if user:
            user = user[0]
            db_pwd = user[3]
            session['user-data'] = user
            session['logged-in'] = True
            if password == db_pwd:
                user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
                audit_data = {
                    'fname': user[5],
                    'lname': user[7],
                    'acc_type': user[4],
                    'user_ip': user_ip,
                    'action_type': 'has logged in',
                    'action_icon': 'bi-person-circle',
                    'action_color': 'success',
                    'action_time': int(time.time())
                }
                db.execute("INSERT INTO audit_trail VALUES (Null, :fname, :lname, :acc_type, :user_ip, :action_type, :action_icon, :action_color, :action_time)", audit_data)
                return redirect(url_for('get_dashboard'))
            else:
                response = {'message': 'Incorrect password'}
        else:
            response = {'message': 'Incorrect username'}
        return render_template('login-form.html', response=response)
    else:
        return redirect(url_for('login'))

def get_med_safety_data(offset=0, per_page=10):
    data = db.fetch("SELECT * FROM med_safety ORDER BY updated_at DESC LIMIT ? OFFSET ?", (per_page, offset))
    return data

def get_med_safety_count():
    total_count = db.fetch("SELECT COUNT(*) FROM med_safety")[0][0]
    return total_count

@app.route('/dashboard/mederr', methods=['GET', 'POST'])
def get_mederr():
    c_data = db.fetch("SELECT * FROM clinic_info")
    err_types = db.fetch("SELECT * FROM med_err_types")
    err_cats = db.fetch("SELECT * FROM med_err_cat")
    med_safety = db.fetch("SELECT * FROM med_safety")

    if request.method == 'POST':
        patient_name = request.form['patient-name']
        clinic_name = request.form['clinic-name']
        med_err_type = request.form['mederr_type']
        med_err_subtype = request.form['subError']
        med_err_cat = request.form['medErrorCat']
        progress = request.form['progress']
        in_charge_pharmacist_name = request.form['pharmacist-name']
        month = request.form['month-occurence']
        day = request.form['day-occurence']
        year = request.form['year-occurence']

        data_occur = f"{month}-{day}-{year}"

        remarks = request.form['detailsMedErr']
        recom = request.form['recom']
        
        user = session['user-data']
        created_by = f'{user[5]} {user[7][:1]}., {user[9]}'
        commit_by  = str(user[10])
        created_at = int(time.time())
        updated_at = int(time.time())

        data = {
            'patient_name': patient_name,
            'clinic_name': clinic_name,
            'med_err_type': med_err_type,
            'med_err_subtype': med_err_subtype,
            'med_err_cat': med_err_cat,
            'remarks': remarks,
            'recom': recom,
            'progress': progress,
            'in_charge': in_charge_pharmacist_name,
            'data_occur': data_occur,
            'commit_by': commit_by,
            'created_by': created_by,
            'created_at': created_at,
            'updated_at': updated_at
        }
        db.execute("INSERT INTO med_safety (patient_name, clinic_name, med_err_type, med_err_subtype, med_err_cat, remarks, recom, progress, in_charge, data_occur, commit_by, created_by, created_at, updated_at) VALUES (:patient_name, :clinic_name, :med_err_type, :med_err_subtype, :med_err_cat, :remarks, :recom, :progress, :in_charge, :data_occur, :commit_by, :created_by, :created_at, :updated_at)", data)
        return render_template('mederr.html', c_data=c_data, err_types=err_types, err_cats=err_cats, data=data)

    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page', per_page=5)
    total_count = get_med_safety_count()
    med_safety = get_med_safety_data(offset=offset, per_page=per_page)
    pagination = Pagination(page=page, per_page=per_page, total=total_count, css_framework='bootstrap5')

    return render_template('mederr.html', c_data=c_data, err_types=err_types, err_cats=err_cats, pagination=pagination, page=page, per_page=per_page, total_count=total_count, med_safety=med_safety)

@app.route('/dashboard/mederr/edit', methods=['POST'])
def mederr_patient_edit():
    if request.method == 'POST':
        patient_id = request.form['patient-id']
        patient_name = request.form['patient-name']
        progress = request.form['progress']
        in_charge = request.form['pharmacist-name']
        recom = request.form['recom']
        updated_at = int(time.time())
        data = {
            'patient_name': patient_name,
            'progress': progress,
            'in_charge': in_charge,
            'recom': recom,
            'updated_at': updated_at,
            'patient_id': patient_id,
        }
        db.execute("UPDATE med_safety SET patient_name=:patient_name, progress=:progress, in_charge=:in_charge, recom=:recom, updated_at=:updated_at WHERE id=:patient_id", data)
        return redirect('/dashboard/mederr')
    else:
        return redirect('/dashboard/mederr')

@app.route('/dashboard/clinics', methods=['GET', 'POST'])
def get_clinics():
    if request.method == 'GET':
        data = db.fetch("SELECT ci.c_name AS clinic_name, COUNT(pd.patientID) AS total_patients, COUNT(CASE WHEN pd.status_patient = 'A' THEN 1 ELSE NULL END) AS active_cases, COUNT(CASE WHEN pd.status_patient = 'R' THEN 1 ELSE NULL END) AS resolved_cases, COALESCE(SUM(CAST(pd.count_review AS INTEGER)), 0) AS total_reviews, ci.c_data_src AS clinic_data_source, ci.created_by AS created_by, ci.created_at AS created_at, ci.updated_at AS updated_at FROM clinic_info ci LEFT JOIN patient_demo pd ON ci.c_ID = pd.c_ID GROUP BY ci.c_ID, ci.c_name, ci.c_data_src, ci.created_at;")
        # data = db.fetch("SELECT * FROM clinic_info")

        return render_template('clinics.html', info=data)
    if request.method == 'POST':
        user = session['user-data']
        created_by = f'{user[5]} {user[7][:1]}., {user[9]}'
        created_at = int(time.time())
        cname = request.form['clinicName']
        csrc = request.form['clinicSource']
        data = {
            'cname': cname,
            'total_patients': 0,
            'ongoing_cases': 0,
            'resolved_cases': 0,
            'reviewed_patient': 0,
            'csrc': csrc,
            'created_by': created_by,
            'created_at': created_at,
            'updated_at': created_at
        }
        last_id = db.execute("INSERT INTO clinic_info VALUES (Null, :cname, :total_patients, :ongoing_cases, :resolved_cases, :reviewed_patient, :csrc, :created_by, :created_at, :updated_at)", data)
        return redirect('/dashboard/clinics')# render_template('clinics.html', response=data)

@app.route('/dashboard/active-patients', methods=['GET', 'POST'])
def get_active_patients():
    if request.method == 'GET':
        patient_demos = db.fetch("SELECT pd.*, ci.c_name AS clinic_name FROM patient_demo pd JOIN clinic_info ci ON pd.c_ID = ci.c_ID")
        response = {
            'patient-demo': patient_demos,
        }
        return render_template('active-patients.html', response=response)

    if request.method == 'POST':
        status = request.form['status']
        patient_id = request.form['patient-id']
        patient_infos = db.fetch("SELECT * FROM patient_demo WHERE patientID=:patient_id", {'patient_id': patient_id})[0]
        db.execute("UPDATE patient_demo SET status_patient = :status WHERE patientID = :patient_id", {'status': status, 'patient_id': patient_id})

        review = patient_infos[-1]
        review += 1
        db.execute("UPDATE patient_demo SET count_review = :count_review WHERE patientID = :patient_id",
            {'count_review': review, 'patient_id': patient_id})

        return redirect(url_for('get_active_patients'))

@app.route('/dashboard/add-patient', methods=['GET', 'POST'])
def add_patient_demo():
    if request.method == 'GET':
        c_data = db.fetch("SELECT * FROM clinic_info")
        return render_template('patient-demographics.html', c_data=c_data)

    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        # date_consult = request.form['date-consult']
        month_consult = request.form['month-consult']
        day_consult = request.form['day-consult']
        year_consult = request.form['year-consult']
        date_consult = f"{month_consult}/{day_consult}/{year_consult}"
        weight = request.form['weight']
        allergy = request.form['allergy']
        status_patient = request.form['status-patient']
        clinic_id = request.form['clinic-id']
        temperature = request.form['temperature']
        pulse_rate = request.form['pulse-rate']
        systolic_pr = request.form['systolicPressure']
        diastolic_pr = request.form['diastolicPressure']
        rp_rate = request.form['respiratoryRate']
        complaint = request.form['complaint']
        present_history = request.form['present-history']
        soc_history = request.form['soc-history']
        past_history = request.form['past-history']
        fam_history = request.form['fam-history']
        generic_name = request.form['generic-name']
        brand_name = request.form['brand-name']
        dos_str = request.form['dosageStrength']
        dos_frm = request.form['dosageForm']
        freq = request.form['frequency']
        indication = request.form['indication']
        user = session['user-data']
        created_by = f'{user[5]} {user[7][:1]}., {user[9]}'
        data = {
            'clinic_id': clinic_id,
            'name': name,
            'age': age,
            'gender': gender,
            'date_consult': date_consult,
            'weight': weight,
            'allergy': allergy,
            'status_patient': status_patient,
            'temperature': temperature,
            'pulse_rate': pulse_rate,
            'systolic_pr': systolic_pr,
            'diastolic_pr': diastolic_pr,
            'rp_rate': rp_rate,
            'complaint': complaint,
            'present_history': present_history,
            'soc_history': soc_history,
            'past_history': past_history,
            'fam_history': fam_history,
            'created_by': created_by,
            'count_review': 0
        }
        last_id = db.execute("INSERT INTO patient_demo VALUES (Null, :clinic_id, :name, :age, :gender, :date_consult, :weight, :allergy, :status_patient, :temperature, :pulse_rate, :systolic_pr, :diastolic_pr, :rp_rate, :complaint, :present_history, :soc_history, :past_history, :fam_history, :created_by, :count_review)", data)
        med_data = {
            'patient_id': last_id,
            'generic_name': generic_name,
            'brand_name': brand_name,
            'dos_str': dos_str,
            'dos_frm': dos_frm,
            'freq': freq,
            'indication': indication,
            'created_by': created_by
        }
        db.execute("INSERT INTO patient_med VALUES (Null, :patient_id, :generic_name, :brand_name, :dos_str, :dos_frm, :freq, :indication, :created_by)", med_data)
        # UPDATE CLINIC
        db.execute("UPDATE clinic_info SET updated_at = :updated_at WHERE c_ID = :clinic_id", {'updated_at': int(time.time()), 'clinic_id': clinic_id})
        return redirect('/dashboard/active-patients')

@app.route('/dashboard/pmedhistory/delete', methods=['POST'])
def delete_medication_from_patient():
    if request.method == 'POST':
        patient_id = request.form['patient-id']
        med_id = int(request.form['med-id'])
        db.execute("DELETE FROM patient_med WHERE medID=:med_id", {'med_id': med_id})
        return redirect(request.referrer)
    else:
        return redirect(request.referrer)


@app.route('/dashboard/pmedhistory/<string:patient_id>', methods=['GET', 'POST'])
def get_patient_med_history(patient_id):
    if request.method == 'GET':
        patient_meds = db.fetch("SELECT * FROM patient_med WHERE patientID=:patient_id", {'patient_id': patient_id})
        patient_infos = db.fetch("SELECT * FROM patient_demo WHERE patientID=:patient_id", {'patient_id': patient_id})[0]

        # db.execute("UPDATE patient_demo SET status_patient = :status WHERE patientID = :patient_id", {'status': status, 'patient_id': patient_id})

        review = patient_infos[-1]
        review += 1
        db.execute("UPDATE patient_demo SET count_review = :count_review WHERE patientID = :patient_id",
            {'count_review': review, 'patient_id': patient_id})

        if patient_meds:
            response = {
                'patient-info': patient_infos,
                'patient-med': patient_meds
            }
            return render_template('patient-medication-history.html', patient_infos=patient_infos, patient_meds=patient_meds)
        else:
            if patient_infos:
                response = {'patient-info': patient_infos}
                return render_template('patient-medication-history.html', patient_infos=patient_infos)
            else:
                return render_template('patient-medication-history.html')
    
    if request.method == 'POST':
        patient_id = request.form['patient-id']
        generic_name = request.form['generic-name']
        brand_name = request.form['brand-name']
        dos_str = request.form['dosageStrength']
        dos_frm = request.form['dosageForm']
        freq = request.form['frequency']
        indication = request.form['indication']
        user = session['user-data']
        created_by = f'{user[5]} {user[7][:1]}., {user[9]}'
        med_data = {
            'patient_id': patient_id,
            'generic_name': generic_name,
            'brand_name': brand_name,
            'dos_str': dos_str,
            'dos_frm': dos_frm,
            'freq': freq,
            'indication': indication,
            'created_by': created_by
        }
        db.execute("INSERT INTO patient_med VALUES (Null, :patient_id, :generic_name, :brand_name, :dos_str, :dos_frm, :freq, :indication, :created_by)", med_data)
        return redirect(request.url)

def retrieve_med_err_type_summary():
    query = "SELECT med_err_type, COUNT(*) as count FROM main.med_safety GROUP BY med_err_type;"
    return db.fetch(query)

def retrieve_med_safety_summary():
    query = "SELECT clinic_name, COUNT(*) AS total_entries_per_clinic FROM med_safety GROUP BY clinic_name;"
    return db.fetch(query)

def generate_donut_chart(data, type='None'):
    df = pd.DataFrame(data, columns=['Clinic', 'Errors'])
    fig = px.pie(df, values='Errors', names='Clinic', title=f'Medication Safety Summary by {type}', hole=0.4)
    return fig

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def get_dashboard():
    if request.method == 'GET':
        total_active_patients = db.fetch("SELECT COUNT(*) FROM patient_demo WHERE status_patient = 'A'")[0][0]
        total_inactive_patients = db.fetch("SELECT COUNT(*) FROM patient_demo WHERE status_patient = 'I'")[0][0]
        total_resolved_cases = db.fetch("SELECT COUNT(*) FROM patient_demo WHERE status_patient = 'R'")[0][0]
        total_entry = db.fetch("SELECT COUNT(*) FROM patient_demo")[0][0]
        total_clinics = db.fetch("SELECT COUNT(*) FROM clinic_info")[0][0]
        total_review = db.fetch("SELECT SUM(count_review) AS total_reviews FROM patient_demo WHERE count_review IS NOT NULL;")[0][0]
        total_err_records = db.fetch("SELECT COUNT(*) FROM med_safety")[0][0]
        current_err = db.fetch("SELECT COUNT(*) FROM med_safety WHERE progress NOT IN (1, 3)")[0][0]
        percentage_medication_errors = calculate_percentage(current_err, total_err_records)
        response = {
            'total-active-patients': total_active_patients,
            'total-inactive-patients': total_inactive_patients,
            'total-resolved-cases': total_resolved_cases,
            'total-clinics': total_clinics,
            'total-review': total_review,
            'total-errors': percentage_medication_errors,
            'total-entries': total_entry,
        }
        med_sum = retrieve_med_safety_summary()
        med_fig = generate_donut_chart(med_sum, 'Clinic')
        med_donut = pio.to_html(med_fig, full_html=False)

        err_sum = retrieve_med_err_type_summary()
        err_fig = generate_donut_chart(err_sum, 'Errors Type')
        err_donut = pio.to_html(err_fig, full_html=False)
        
        return render_template('user-dash.html', response=response, med_donut=med_donut, err_donut=err_donut)

def get_audit_logs(offset=0, per_page=10):
    audit_logs = db.fetch("SELECT * FROM audit_trail ORDER BY action_time DESC LIMIT ? OFFSET ?", (per_page, offset))
    # audit_logs = db.fetch("SELECT * FROM audit_trail ORDER BY action_time DESC")
    return audit_logs

def get_audit_count():
    total_count = db.fetch("SELECT COUNT(*) FROM audit_trail")[0][0]
    return total_count

@app.route('/dashboard/audit', methods=['GET'])
def get_audit_page():
    # Default 5 items per page
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page', per_page=5)
    total_count = get_audit_count()
    audit_logs = get_audit_logs(offset=offset, per_page=per_page)
    pagination = Pagination(page=page, per_page=per_page, total=total_count, css_framework='bootstrap5')
    return render_template('audit-page.html', audit=audit_logs, pagination=pagination, page=page, per_page=per_page, total_count=total_count)

@app.route('/dashboard/msinfo', methods=['GET', 'POST'])
def get_msi_page():
    if request.method == 'GET':
        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page', per_page=5)
        total_count = get_med_safety_count()
        med_safety = get_med_safety_data(offset=offset, per_page=per_page)
        pagination = Pagination(page=page, per_page=per_page, total=total_count, css_framework='bootstrap5')

        return render_template('msi-page.html', med_safety=med_safety, pagination=pagination, page=page, per_page=per_page, total_count=total_count)

@app.route('/logout', methods=['GET'])
def make_logout():
    user = session['user-data']
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    audit_data = {
        'fname': user[5],
        'lname': user[7],
        'acc_type': user[4],
        'user_ip': user_ip,
        'action_type': 'has logged out',
        'action_icon': 'bi-wifi-off',
        'action_color': 'danger',
        'action_time': int(time.time())
    }
    db.execute("INSERT INTO audit_trail VALUES (Null, :fname, :lname, :acc_type, :user_ip, :action_type, :action_icon, :action_color, :action_time)", audit_data)
    session.clear()
    return redirect('/')

@app.route('/help', methods=['GET'])
def help_page():
    return render_template('help-page.html')
"""
@app.route('/login', methods=['GET', 'POST'])
def login_form():
    if request.method == 'GET':
        return render_template('login-form.html')
    elif request.method == 'POST':
"""


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8081, threaded=True)