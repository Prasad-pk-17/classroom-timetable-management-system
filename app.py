from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysql_connector import MySQL
from datetime import datetime, timedelta

def format_time(t):
    # If MySQL returns timedelta
    if isinstance(t, timedelta):
        t = (datetime.min + t).time()
    return t.strftime("%I:%M %p").lstrip("0")


app = Flask(__name__)
app.secret_key = "classroom_timetable_secret_key"



app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Prasad'
app.config['MYSQL_DATABASE'] = 'classroom_db'

mysql = MySQL(app)

def admin_login_required():
    return session.get("admin_logged_in")



# LOGIN SYSTEM

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        cur = mysql.connection.cursor()

        # check user in database
        cur.execute("SELECT * FROM admin WHERE username=%s AND password=%s",(username, password))
        admin = cur.fetchone()
        cur.close()

        if admin:
            session["admin_logged_in"] = True
            session["admin_id"] = admin[0]
            session["admin_username"] = admin[1]
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid Username or Password", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")


# register route

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()

        cursor.execute("SELECT * FROM admin WHERE email=%s OR username=%s", (email, username))
        existing = cursor.fetchone()

        if existing:
            return render_template("register.html", message="User already exists!")

        cursor.execute("INSERT INTO admin(username, email, password) VALUES (%s, %s, %s)",(username, email, password))
        mysql.connection.commit()
        cursor.close()

        return render_template("register.html", message="Registration successful! You can login now.")

    return render_template("register.html")

# forget password route



@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM admin WHERE email=%s", (email,))
        user = cur.fetchone()

        if not user:
            flash("Email not found!", "danger")
            return redirect(url_for('forgot_password'))

        reset_token = email[::-1]    

        return redirect(url_for('reset_password', token=reset_token))

    return render_template("forgot_password.html")


# reset password route

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = token[::-1]

    if request.method == 'POST':
        new_password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("UPDATE admin SET password=%s WHERE email=%s",(new_password, email))
        mysql.connection.commit()

        flash("Password updated successfully!", "success")
        return redirect(url_for('login'))

    return render_template("reset_password.html", email=email)


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("login"))




# DASHBOARD 

@app.route("/dashboard")
def dashboard():
    if not admin_login_required():
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()

    cur.execute("SELECT COUNT(*) FROM classrooms")
    total_classrooms = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM subjects")
    total_subjects = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM timeslots")
    total_timeslots = cur.fetchone()[0]

    cur.close()

    return render_template("dashboard.html",total_classrooms=total_classrooms,total_subjects=total_subjects,total_timeslots=total_timeslots)




# ADD CLASSROOM

@app.route('/add_classroom', methods=['GET', 'POST'])
def add_classroom():
    if request.method == 'POST':
        name = request.form['name']
        capacity = request.form['capacity']
        department = request.form['department']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO classrooms (name, capacity, department) VALUES (%s, %s, %s)",(name, capacity, department))
        mysql.connection.commit()

        cur.close()

        flash("Classroom added successfully!", "success")
        return redirect(url_for("add_classroom"))

    return render_template("add_classroom.html")


# VIEW CLASSROOMS

@app.route('/view_classrooms')
def view_classrooms():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM classrooms")
    classrooms = cur.fetchall()
    cur.close()

    return render_template("view_classrooms.html", classrooms=classrooms)


# EDIT CLASSROOM


@app.route("/edit_classroom", methods=["GET", "POST"])
def edit_classroom():
    cur = mysql.connection.cursor()

    if request.method == "POST":
       
        total = int(request.form["total_rows"])

        for i in range(total):
            cid = request.form.get(f"id_{i}")
            name = request.form.get(f"name_{i}")
            capacity = request.form.get(f"capacity_{i}")
            department = request.form.get(f"department_{i}")

            cur.execute("""UPDATE classrooms SET name=%s, capacity=%s, department=%s WHERE id=%s """, (name, capacity, department, cid))

        mysql.connection.commit()
        cur.close()

        flash("All classrooms updated!", "success")
        return redirect(url_for("edit_classroom"))

    
    cur.execute("SELECT * FROM classrooms")
    classrooms = cur.fetchall()
    cur.close()

    return render_template("edit_classroom.html", classrooms=classrooms)

# DELETE CLASSROOM
@app.route('/delete_classrooms', methods=['GET', 'POST'])
def delete_classrooms():
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        ids_to_delete = request.form.getlist('delete_ids')

        if ids_to_delete:
            for cid in ids_to_delete:
                cur.execute("DELETE FROM classrooms WHERE id=%s", (cid,))
            mysql.connection.commit()

        cur.close()
        flash("Selected classrooms deleted successfully!", "danger")
        return redirect(url_for('delete_classrooms'))

    cur.execute("SELECT * FROM classrooms")
    classrooms = cur.fetchall()
    cur.close()

    return render_template("delete_classrooms.html", classrooms=classrooms)





# ADD SUBJECT
@app.route("/add_subject", methods=["GET", "POST"])
def add_subject():

    if request.method == "POST":

        # Get form data
        department = request.form["department"]
        year = request.form["year"]
        semester = request.form["semester"]
        name = request.form["name"]
        subject_code = request.form["subject_code"]
        teacher = request.form["teacher"]
        num_students = int(request.form["num_students"])
        subject_type = request.form["type"]

        # DB connection
        cur = mysql.connection.cursor()

        # Insert query
        cur.execute("""
        INSERT INTO subjects
        (department, year, semester, name, subject_code, teacher, num_students, type)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (department, year, semester, name, subject_code, teacher, num_students, subject_type))

        mysql.connection.commit()
        cur.close()

        flash("Subject added successfully!", "success")

        return redirect(url_for("add_subject"))

    return render_template("add_subject.html")


# VIEW SUBJECTS
@app.route('/view_subjects')
def view_subjects():

    cur = mysql.connection.cursor()

    # Fetch semester also (VERY IMPORTANT)
    cur.execute("""SELECT id,department,name,subject_code,teacher,num_students,semester FROM subjects """)

    subjects = cur.fetchall()
    cur.close()

    return render_template("view_subjects.html", subjects=subjects)


#edit subjects
@app.route('/edit_all_subjects', methods=['GET', 'POST'])
def edit_all_subjects():

    cur = mysql.connection.cursor()

    if request.method == 'POST':

        total = int(request.form['total_rows'])

        for i in range(total):

            sid = request.form.get(f"id_{i}")

            department = request.form.get(f"department_{i}")
            name = request.form.get(f"name_{i}")
            code = request.form.get(f"code_{i}")
            teacher = request.form.get(f"teacher_{i}")
            num_students = int(request.form.get(f"num_students_{i}"))
            semester = request.form.get(f"semester_{i}")

            cur.execute("""
                UPDATE subjects 
                SET department=%s,
                    name=%s,
                    subject_code=%s,
                    teacher=%s,
                    num_students=%s,
                    semester=%s
                WHERE id=%s
            """, (department, name, code, teacher, num_students, semester, sid))

        mysql.connection.commit()
        flash("All subjects updated successfully!", "success")
        return redirect(url_for('edit_all_subjects'))

    cur.execute("""
        SELECT id, department, name, subject_code,
               teacher, num_students, semester
        FROM subjects
    """)

    subjects = cur.fetchall()
    cur.close()

    return render_template("edit_all_subjects.html", subjects=subjects)


    # ================== FETCH ==================

    # IMPORTANT: NO SELECT *
    cur.execute("""SELECT id, department, name, subject_code, teacher, num_students, semester FROM subjects """)

    subjects = cur.fetchall()
    cur.close()

    return render_template("edit_all_subjects.html", subjects=subjects)


    # ================== GET DATA ==================

    # IMPORTANT: Explicit order (no SELECT *)
    cur.execute("""SELECTid, name, teacher, subject_code, department, num_students, semester FROM subjects """)

    subjects = cur.fetchall()
    cur.close()

    return render_template("edit_all_subjects.html", subjects=subjects)



# delete subjects
@app.route('/delete_subjects', methods=['GET', 'POST'])
def delete_subjects():

    cur = mysql.connection.cursor()

    if request.method == 'POST':

        ids = request.form.getlist('delete_ids')

        for sid in ids:
            # delete from timetable first (foreign key issue fix)
            cur.execute("DELETE FROM timetable WHERE subject_id=%s", (sid,))
            cur.execute("DELETE FROM subjects WHERE id=%s", (sid,))

        mysql.connection.commit()
        flash("Selected subjects deleted successfully!", "danger")
        return redirect(url_for('delete_subjects'))

    # FETCH SUBJECTS
    cur.execute("""
        SELECT id, department, name, subject_code,
               teacher, num_students, semester
        FROM subjects
    """)

    subjects = cur.fetchall()
    cur.close()

    return render_template("delete_subjects.html", subjects=subjects)



# ADD TIMESLOT

@app.route("/add_timeslot" , methods=["GET" , "POST"])
def add_timeslot():
    if request.method == "POST":
        start_time = request.form["start_time"]
        end_time = request.form["end_time"]
        day = request.form["day"]

        cur = mysql.connection.cursor()
        cur.execute( "INSERT INTO timeslots (start_time, end_time, day) VALUES (%s, %s, %s)",(start_time, end_time, day))
        mysql.connection.commit()
        cur.close()

        flash("Timeslot added successfully!", "success")
        return redirect(url_for("add_timeslot"))

    return render_template("add_timeslot.html")


# VIEW TIMESLOTS

@app.route('/view_timeslots')
def view_timeslots():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, start_time, end_time, day FROM timeslots")
    timeslots = cur.fetchall()
    cur.close()

    return render_template("view_timeslots.html", timeslots=timeslots)

#edit timeslots

@app.route('/edit_all_timeslots', methods=['GET', 'POST'])
def edit_all_timeslots():

    if request.method == 'POST':
        cur = mysql.connection.cursor()
        total = int(request.form['total_rows'])

        for i in range(total):
            tid = request.form.get(f"id_{i}")
            day = request.form.get(f"day_{i}")
            start = request.form.get(f"start_{i}")
            end = request.form.get(f"end_{i}")

            cur.execute("SELECT day, start_time, end_time FROM timeslots WHERE id=%s", (tid,))
            old_day, old_start, old_end = cur.fetchone()

            if not day: day = old_day
            if not start: start = old_start
            if not end: end = old_end

            cur.execute(""" UPDATE timeslots SET day=%s, start_time=%s, end_time=%s WHERE id=%s""", (day, start, end, tid))

        mysql.connection.commit()
        cur.close()

        flash("Timeslots updated!", "success")
        return redirect(url_for('edit_all_timeslots'))

    # GET method
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM timeslots")
    slots = cur.fetchall()
    cur.close()

    return render_template("edit_all_timeslots.html", slots=slots)

# delete timeslots
@app.route('/delete_timeslots', methods=['GET', 'POST'])
def delete_timeslots():

    cur = mysql.connection.cursor()

    if request.method == 'POST':

        ids = request.form.getlist('delete_ids')

        for tid in ids:
            # delete timetable records first
            cur.execute("DELETE FROM timetable WHERE timeslot_id=%s", (tid,))
            
            # then delete timeslot
            cur.execute("DELETE FROM timeslots WHERE id=%s", (tid,))

        mysql.connection.commit()
        flash("Selected timeslots deleted successfully!", "danger")
        return redirect(url_for('delete_timeslots'))

    cur.execute("SELECT * FROM timeslots")
    slots = cur.fetchall()
    cur.close()

    return render_template("delete_timeslots.html", slots=slots)

import random
from datetime import datetime, timedelta

import random

@app.route('/generate_timetable', methods=['POST'])
def generate_timetable():

    semester = request.form.get('semester')

    cursor = mysql.connection.cursor(dictionary=True)

    # SUBJECTS
    cursor.execute("SELECT * FROM subjects WHERE semester=%s", (semester,))
    subjects = cursor.fetchall()

    theory = [s for s in subjects if s['type']=="theory"]
    practical = [s for s in subjects if s['type']=="practical"]

    # TIMESLOTS
    cursor.execute("""
    SELECT * FROM timeslots
    ORDER BY FIELD(day,'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'),
    start_time
    """)
    timeslots = cursor.fetchall()

    # CLASSROOMS
    cursor.execute("SELECT * FROM classrooms")
    classrooms = cursor.fetchall()

    theory_rooms=[c for c in classrooms if "LAB" not in c['name']]

    # LAB ROOM RULE
    if semester in ["Sem III","Sem IV"]:
        lab_rooms=[c for c in classrooms if "LAB2" in c['name']]
    else:
        lab_rooms=[c for c in classrooms if "LAB1" in c['name']]

    # DELETE OLD TIMETABLE
    cursor.execute("""
    DELETE t FROM timetable t
    JOIN subjects s ON t.subject_id=s.id
    WHERE s.semester=%s
    """,(semester,))

    days=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]

    theory_index=0
    practical_index=0

    for day in days:

        day_slots=[s for s in timeslots if s['day']==day]

        # PRACTICAL SLOT RULE
        if semester in ["Sem I","Sem II"]:
            lab_slot1=day_slots[0]
            lab_slot2=day_slots[1]
            theory_slots=[2,3]
        else:
            lab_slot1=day_slots[2]
            lab_slot2=day_slots[3]
            theory_slots=[0,1]

        # ---------- THEORY ----------
        for i in theory_slots:

            slot=day_slots[i]

            subject=theory[theory_index % len(theory)]

            room=random.choice(theory_rooms)

            cursor.execute("""
            INSERT INTO timetable(day,classroom_id,subject_id,timeslot_id)
            VALUES(%s,%s,%s,%s)
            """,(day,room['id'],subject['id'],slot['id']))

            theory_index+=1


        # ---------- PRACTICAL ----------
        subject=practical[practical_index % len(practical)]

        lab=random.choice(lab_rooms)

        cursor.execute("""
        INSERT INTO timetable(day,classroom_id,subject_id,timeslot_id)
        VALUES(%s,%s,%s,%s)
        """,(day,lab['id'],subject['id'],lab_slot1['id']))

        cursor.execute("""
        INSERT INTO timetable(day,classroom_id,subject_id,timeslot_id)
        VALUES(%s,%s,%s,%s)
        """,(day,lab['id'],subject['id'],lab_slot2['id']))

        practical_index+=1


    mysql.connection.commit()
    cursor.close()

    flash("Timetable generated successfully!", "success")

    return redirect(url_for('view_timetable', semester=semester))

from datetime import datetime, timedelta

@app.route('/timetable/<semester>')
def view_timetable(semester):

    cursor = mysql.connection.cursor(dictionary=True, buffered=True)

    query = """
        SELECT t.day,
               ts.start_time,
               ts.end_time,
               s.name AS subject_name,
               s.teacher,
               c.name AS classroom
        FROM timetable t
        JOIN subjects s ON t.subject_id = s.id
        JOIN timeslots ts ON t.timeslot_id = ts.id
        JOIN classrooms c ON t.classroom_id = c.id
        WHERE s.semester = %s
    """

    cursor.execute(query, (semester,))
    rows = cursor.fetchall()   
    cursor.close()

    days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday"
    ]

    headers = [
        "11:30 AM - 12:30 PM",
        "12:30 PM - 1:30 PM",
        "2:30 PM - 3:30 PM",
        "3:30 PM - 4:30 PM"
    ]

    timetable = {d: {h: "" for h in headers} for d in days}

    for row in rows:

        start = row['start_time']
        end = row['end_time']

        if isinstance(start, timedelta):
            start = (datetime.min + start).time()

        if isinstance(end, timedelta):
            end = (datetime.min + end).time()

        start = start.strftime("%I:%M %p").lstrip("0")
        end = end.strftime("%I:%M %p").lstrip("0")

        header = f"{start} - {end}"

        content = f"""
        <b>{row['subject_name']}</b><br>
        {row['teacher']}<br>
        Room: {row['classroom']}
        """

        if row['day'] in timetable and header in timetable[row['day']]:
            timetable[row['day']][header] += content

    return render_template(
        "timetable.html",
        semester=semester,
        timetable=timetable,
        days=days
    )

from datetime import datetime, timedelta

@app.route('/combined_timetable')
def combined_timetable():

    cursor = mysql.connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT t.day, ts.start_time, ts.end_time,
               s.name subject_name,
               s.semester,
               s.teacher,
               c.name classroom
        FROM timetable t
        JOIN subjects s ON t.subject_id = s.id
        JOIN timeslots ts ON t.timeslot_id = ts.id
        JOIN classrooms c ON t.classroom_id = c.id
    """)

    rows = cursor.fetchall()
    cursor.close()

    days=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]

    headers=[
        "11:30 AM - 12:30 PM",
        "12:30 PM - 1:30 PM",
        "2:30 PM - 3:30 PM",
        "3:30 PM - 4:30 PM"
    ]

    timetable={d:{h:"" for h in headers} for d in days}

    for row in rows:

        start=row['start_time']
        end=row['end_time']

        if isinstance(start,timedelta):
            start=(datetime.min+start).time()

        if isinstance(end,timedelta):
            end=(datetime.min+end).time()

        start=start.strftime("%I:%M %p").lstrip("0")
        end=end.strftime("%I:%M %p").lstrip("0")

        header=f"{start} - {end}"

        content=f"""
        <b>{row['semester']} - {row['subject_name']}</b><br>
        {row['teacher']}<br>
        Room: {row['classroom']}<br><br>
        """

        if row['day'] in timetable and header in timetable[row['day']]:
            timetable[row['day']][header]+=content

    return render_template(
        "combined_timetable.html",
        timetable=timetable,
        days=days
    )

if __name__ == "__main__":
    app.run()


