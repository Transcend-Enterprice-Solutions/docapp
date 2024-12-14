import sqlite3, time

con = sqlite3.connect('whatsaver.db')
cur = con.cursor()

user_id = int(time.time())


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
"""
def calculate_percentage(part, whole):
    return round((part / whole) * 100, 2) if whole != 0 else 0

total_records = db.fetch("SELECT COUNT(*) FROM med_safety")[0][0]
med_errors = db.fetch("SELECT COUNT(*) FROM med_safety WHERE progress NOT IN (1, 3)")[0][0]
percentage_medication_errors = calculate_percentage(med_errors, total_records)

print(f'Percentage of medication safety errors: {percentage_medication_errors}%')
"""


# CLINIC IDS #
# 1 = hypertension clinic

# clinic_demo
# cur.execute('''CREATE TABLE IF NOT EXISTS clinic_demo (clinic_id integer PRIMARY KEY AUTOINCREMENT, clinic_name text not NULL)''')
# con.commit()

## USERS TABLE ##
# cur.execute('''CREATE TABLE IF NOT EXISTS users (userID integer PRIMARY KEY AUTOINCREMENT, username text not NULL, password text not NULL, account_type integer not NULL, fname text not NULL, lname text not NULL, contact_number text not NULL, clinic_id text not NULL)''')
# cur.execute('''ALTER TABLE users ADD COLUMN dept_name text''')
# cur.execute('''ALTER TABLE users DROP COLUMN acc_type''')
# con.commit()

# cur.execute("INSERT INTO users VALUES (Null, ?, ?, ?, ?, ?, ?)", ('andy', '24875', 0, 'andy', 'cruz', '0960745321'))
# con.commit()



## PATIENT DEMOGRAPHICS TABLE ##
# cur.execute('''CREATE TABLE IF NOT EXISTS patient_demo (patientID integer PRIMARY KEY AUTOINCREMENT, name text not NULL, age text not NULL, gender text not NULL, date_consult text not NULL, weight text not NULL, allergy text not NULL, status_patient text not NULL, temperature text not NULL, pulse_rate text not NULL, bl_pressure text not NULL, rp_rate text not NULL, complaint text not NULL, present_history text not NULL, soc_history text not NULL, past_history text not NULL, fam_history text not NULL, created_by text not NULL)''')

# cur.execute('''ALTER TABLE patient_demo ADD COLUMN created_by text''')
# con.commit()

## PATIENT MEDICATION HISTORY TABLE ##
## cur.execute('''CREATE TABLE IF NOT EXISTS patient_med (medID integer PRIMARY KEY AUTOINCREMENT, patientID text not NULL, generic_name text not NULL, brand_name text not NULL, dos_str text not NULL, dos_frm text not NULL, freq text not NULL, indication text not NULL, created_by text not NULL)''')
# cur.execute('''DROP TABLE patient_med''')
## con.commit()


# cur.execute('''UPDATE patient_demo SET created_by = 'John R., IT' WHERE patientID = 2 ''')  
# con.commit()
# exit()

## PATIENT DEMO DELETION ##
# cur.execute('''DELETE FROM patient_demo WHERE patientID = 1''')
# con.commit()

# practitioner type => admin (0)
# student type => guest (1)

# account type: {'0': 'admin', '1': 'student'}]
# cur.execute('''UPDATE users SET acc_type = '1' WHERE userID = '1709098454' ''')
# con.commit()

## PATIENT DEMO TOTAL DATE ENTRIES ##
# res = cur.execute('''SELECT COUNT(*) FROM patient_demo WHERE status_patient = 'A' ''')
# total_entry = res.fetchone()[0]
# print(total_entry)
# exit()


# cur.execute("DELETE FROM users WHERE userID = 4")
# con.commit()
# res = cur.execute("SELECT * FROM patient_demo")
# res = cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
# res = cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='patient_demo'")
# res = cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='patient_med'")

# res = cur.execute("SELECT * FROM users where userID = (?)", [user_id])
# res = cur.execute("SELECT * FROM patient_demo")
# res = cur.execute("SELECT * FROM patient_med")
# res = cur.execute("SELECT * FROM msafety_info")

# active_patient_count = cur.execute("SELECT COUNT(*) FROM patient_demo").fetchall()[0][0]
# print(active_patient_count)


# res = cur.execute("SELECT * FROM users WHERE username = :username", {'username': 'ras1234'})
# row = res.fetchone()

# [(1709098429, 'dale', '141414', 9606869418), (1709098446, 'andy', '141414', 9606869411)
# res = cur.execute("SELECT * FROM sqlite_master where type='table'")

"""
rows = res.fetchone()
print(rows[2])
"""
# rows = res.fetchall()
# print(rows)

"""
for row in rows:
    if row[0] == '1709096824':
        print(row)
"""

# res = cur.execute("SELECT ci.c_name AS clinic_name, COUNT(pd.patientID) AS total_patients, COUNT(CASE WHEN pd.status_patient = 'R' THEN 1 ELSE NULL END) AS resolved_cases, ci.c_data_src AS clinic_data_source, ci.created_at AS created_at FROM clinic_info ci JOIN patient_demo pd ON ci.c_ID = pd.c_ID GROUP BY ci.c_ID, ci.c_name, ci.c_data_src, ci.created_at;")
# print(res.fetchall())

users = db.fetch("SELECT * FROM users")
print(users)