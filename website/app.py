from flask import Flask, json, render_template, request, redirect, url_for, g
import sqlite3 as sql 
import os
import random
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "crackvision"

UPLOAD_FOLDER = 'static/uploads'
# Ensure uploads folder exists in working directory
os.makedirs(os.path.join('d:/internship netsoft/python/website', UPLOAD_FOLDER), exist_ok=True)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sql.connect("crackvision.db", timeout=30.0)
        db.execute("PRAGMA journal_mode=WAL;")
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    conn = sql.connect('crackvision.db', timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    cursor = conn.cursor()
    
    # Check if old table structure exists
    cursor.execute("PRAGMA table_info(users)")
    cols = [c[1] for c in cursor.fetchall()]
    
    # If the users table is of old style, drop it to migrate safely
    if cols and 'username' not in cols:
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS projects")
        cursor.execute("DROP TABLE IF EXISTS prediction")
        cursor.execute("DROP TABLE IF EXISTS reviews")

    # Create tables exactly matching the DB Schema.pdf specifications
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role INTEGER,
        name TEXT,
        dob TEXT,
        email TEXT,
        contact TEXT,
        address TEXT,
        gender TEXT,
        img TEXT
    )
    """)

    # Force drop existing projects table to replace it with the new schema as requested by the user
    cursor.execute("DROP TABLE IF EXISTS projects")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pcat TEXT,
        pname TEXT,
        ptype TEXT,
        duration TEXT,
        area TEXT,
        client TEXT,
        location TEXT,
        bheight TEXT,
        ftype TEXT,
        fmaterial TEXT,
        pspace TEXT,
        erate TEXT,
        sdesc TEXT,
        poverview TEXT,
        plog TEXT,
        status TEXT,
        img TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prediction (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        userid INTEGER,
        pred_result TEXT,
        pred_image TEXT,
        orginal_image TEXT,
        avg_depths TEXT,
        confidence REAL,
        date_time TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        user_id INTEGER,
        review_text TEXT,
        date_time TEXT
    )
    """)

    # Seed default users matching integer roles: 1 = admin, 2 = user, 3 = engineer
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO users (username, password, role, name, dob, email, contact, address, gender, img)
            VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, 'static/default_profile.png')
        """, ('admin', 'admin123', 'System Admin', '1985-01-01', 'admin@company.com', '0000000000', 'Admin Office', 'Male'))

    cursor.execute("SELECT * FROM users WHERE username = 'user'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO users (username, password, role, name, dob, email, contact, address, gender, img)
            VALUES (?, ?, 2, ?, ?, ?, ?, ?, ?, 'static/default_profile.png')
        """, ('user', 'user123', 'Demo User', '1998-05-15', 'user@company.com', '9876500000', 'User Street', 'Male'))

    cursor.execute("SELECT * FROM users WHERE username = 'engineer'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO users (username, password, role, name, dob, email, contact, address, gender, img)
            VALUES (?, ?, 3, ?, ?, ?, ?, ?, ?, 'static/default_profile.png')
        """, ('engineer', 'engineer123', 'Demo Engineer', '1992-10-20', 'engineer@company.com', '9876543210', 'Engineer Lab', 'Male'))

    # Seed default construction projects
    cursor.execute("SELECT COUNT(*) FROM projects")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO projects (pcat, pname, ptype, duration, area, client, location, bheight, ftype, fmaterial, pspace, erate, sdesc, poverview, plog, status, img)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'Commercial Complex',
            'NetSoft Business Tower',
            'Commercial Construction',
            '24 Months',
            '45,000 sq ft',
            'NetSoft Group',
            'Kochi, Kerala',
            '85 meters (20 Floors)',
            'Pile Foundation',
            'Reinforced Concrete (M40 grade)',
            '6.0 meters',
            'N/A',
            'Multi-floor commercial building with office spaces, parking facilities, and modern structural safety systems.',
            'The NetSoft Business Tower is a flagship corporate commercial development designed to meet the highest safety, efficiency, and engineering standards. Featuring state-of-the-art facilities, seismic protection systems, and automated surface scanning sensor slots, it is engineered for extreme durability.',
            'Initial corporate complex site log detailing pile foundation safety and concrete grade scanning details.',
            'Ongoing',
            'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=600&q=70'
        ))

        cursor.execute("""
            INSERT INTO projects (pcat, pname, ptype, duration, area, client, location, bheight, ftype, fmaterial, pspace, erate, sdesc, poverview, plog, status, img)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'Residential Building',
            'Green Valley Apartments',
            'Residential Construction',
            '18 Months',
            '65,000 sq ft',
            'Green Valley Developers',
            'Chennai, Tamil Nadu',
            '40 meters (12 Floors)',
            'Raft Foundation',
            'Concrete and High-Strength Steel Barrels',
            '4.5 meters',
            'N/A',
            'Residential apartment project focused on durable construction, practical layouts, and reliable long-term maintenance.',
            'Green Valley Apartments is a high-density, eco-friendly luxury residential housing complex. Built with structural safety as the highest priority, the buildings are monitored with real-time inspection cameras and utilize highly durable low-shrinkage self-consolidating concrete.',
            'Residential building logs indicating complete raft foundation settlement checks and concrete casing scans.',
            'Completed',
            'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=600&q=70'
        ))

        cursor.execute("""
            INSERT INTO projects (pcat, pname, ptype, duration, area, client, location, bheight, ftype, fmaterial, pspace, erate, sdesc, poverview, plog, status, img)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'Structural Repair',
            'Concrete Surface Restoration',
            'Infrastructure Rehabilitation',
            '6 Months',
            '12,000 sq ft',
            'National Highway Authority',
            'Bengaluru, Karnataka',
            'N/A',
            'N/A',
            'Fiber-Reinforced Cement and Epoxies',
            'N/A',
            'N/A',
            'Planned concrete restoration work including surface repair, crack sealing, slab review, and inspection-ready documentation.',
            'This project targets critical rehabilitation of a heavy-traffic highway bridge surface and under-girders. The execution details involve removing degraded concrete layers, injecting epoxy micro-fillers into detected crack paths, and applying a robust protective fiber polymer overlay.',
            'Infrastructure restoration log tracking slab crack epoxies injections and overlay curing monitoring.',
            'Upcoming',
            'https://images.unsplash.com/photo-1590069261209-f8e9b8642343?auto=format&fit=crop&w=600&q=70'
        ))

    # Migration: Force-upgrade pre-existing database project images to optimized Unsplash URLs
    cursor.execute("SELECT id, pname FROM projects")
    for row in cursor.fetchall():
        pid, pname = row[0], row[1]
        if pname == 'NetSoft Business Tower':
            cursor.execute("UPDATE projects SET img = ? WHERE id = ?", ('https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=600&q=70', pid))
        elif pname == 'Green Valley Apartments':
            cursor.execute("UPDATE projects SET img = ? WHERE id = ?", ('https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=600&q=70', pid))
        elif pname == 'Concrete Surface Restoration':
            cursor.execute("UPDATE projects SET img = ? WHERE id = ?", ('https://images.unsplash.com/photo-1590069261209-f8e9b8642343?auto=format&fit=crop&w=600&q=70', pid))

    # Seed sample reviews
    cursor.execute("SELECT COUNT(*) FROM reviews")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO reviews (project_id, user_id, review_text, date_time)
            VALUES (?, ?, ?, ?)
        """, (1, 2, 'The structural slab looks extremely solid and execution seems highly professional. Excellent work!', '2026-05-24 14:32:00'))

        cursor.execute("""
            INSERT INTO reviews (project_id, user_id, review_text, date_time)
            VALUES (?, ?, ?, ?)
        """, (2, 2, 'The foundation work was completed precisely on schedule. The finishes are very durable and look clean.', '2025-04-10 11:15:00'))

    conn.commit()
    conn.close()

init_db()

@app.route("/")
@app.route("/index.html")
def index():
    return render_template("index.html")

@app.route("/register.html")
def register_page():
    return render_template("register.html")

@app.route("/register_db", methods=['POST'])
def register_db():
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone') # Maps to contact in database
        dob = request.form.get('dob')
        gender = request.form.get('gender')
        address = request.form.get('address')
        password = request.form.get('password')
        
        con = get_db()
        cur = con.cursor()
        try:
            cur.execute("""
                INSERT INTO users (username, password, role, name, dob, email, contact, address, gender, img)
                VALUES (?, ?, 2, ?, ?, ?, ?, ?, ?, 'static/default_profile.png')
            """, (username, password, name, dob, email, phone, address, gender))
            con.commit()
            return redirect("/login.html")
        except Exception as e:
            return f"Registration failed: {str(e)}", 400

@app.route("/login.html")
def login():
    return render_template("login.html")

@app.route("/user.html")
def user_dashboard():
    return render_template("user.html")

@app.route("/admin.html")
def admin():
    return render_template("admin.html")

@app.route("/engineer.html")
def engineer():
    return render_template("engineer.html")

@app.route("/login_db", methods=['POST'])
def login_db():
    try:
        data = request.get_json()
        if not data:
            return json.dumps({"status": "error", "message": "Missing JSON data."}), 400, {'Content-Type': 'application/json'}
            
        login_input = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        con = get_db()
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("""
            SELECT * FROM users 
            WHERE (LOWER(email) = ? OR LOWER(username) = ?) AND password = ?
        """, (login_input, login_input, password))
        user = cur.fetchone()
            
        if not user:
            return json.dumps({"status": "error", "message": "Invalid username/email or password."}), 401, {'Content-Type': 'application/json'}
            
        # Map integer role to string role for client-side compatibility
        legacy_role = 'user'
        if user['role'] == 1:
            legacy_role = 'admin'
        elif user['role'] == 3:
            legacy_role = 'engineer'
            
        user_data = {
            "id": user['id'],
            "username": user['username'],
            "name": user['name'],
            "email": user['email'],
            "phone": user['contact'],
            "age": 25,
            "dob": user['dob'],
            "gender": user['gender'],
            "address": user['address'],
            "role": legacy_role,
            "role_id": user['role'],
            "status": "approved",
            "employeeId": f"ENG-00{user['id']}" if user['role'] == 3 else None,
            "department": "Structural Inspection" if user['role'] == 3 else None,
            "designation": "Site Engineer" if user['role'] == 3 else None
        }
        return json.dumps({"status": "success", "user": user_data}), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}), 500, {'Content-Type': 'application/json'}

@app.route("/admin/get_engineers", methods=['GET'])
def get_engineers():
    try:
        con = get_db()
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("SELECT id, name, username, email, contact, dob, address, gender, password FROM users WHERE role = 3")
        rows = cur.fetchall()
            
        engineers = []
        for row in rows:
            engineers.append({
                "name": row["name"],
                "username": row["username"],
                "email": row["email"],
                "phone": row["contact"],
                "dob": row["dob"],
                "address": row["address"],
                "gender": row["gender"],
                "employeeId": f"ENG-00{row['id']}",
                "department": "Structural Inspection",
                "designation": "Site Engineer",
                "status": "approved",
                "password": row["password"]
            })
        return json.dumps(engineers), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}), 500, {'Content-Type': 'application/json'}

@app.route("/admin/add_engineer", methods=['POST'])
def add_engineer():
    try:
        data = request.get_json()
        if not data:
            return json.dumps({"status": "error", "message": "Missing JSON data."}), 400, {'Content-Type': 'application/json'}
            
        name = data.get('name')
        username = data.get('username')
        if not username:
            username = data.get('email', '').split('@')[0]
        email = data.get('email', '').strip().lower()
        phone = data.get('phone') # contact
        dob = data.get('dob', '1995-01-01')
        address = data.get('address', 'Engineer Lab')
        gender = data.get('gender', 'Male')
        password = data.get('password')
        
        con = get_db()
        cur = con.cursor()
        
        cur.execute("SELECT * FROM users WHERE LOWER(email) = ? OR LOWER(username) = ?", (email, username.lower()))
        if cur.fetchone():
            return json.dumps({"status": "error", "message": "Username or Email already exists."}), 400, {'Content-Type': 'application/json'}
            
        cur.execute("""
            INSERT INTO users (username, password, role, name, dob, email, contact, address, gender, img)
            VALUES (?, ?, 3, ?, ?, ?, ?, ?, ?, 'static/default_profile.png')
        """, (username, password, name, dob, email, phone, address, gender))
        con.commit()
            
        return json.dumps({"status": "success", "message": "Engineer added successfully."}), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}), 500, {'Content-Type': 'application/json'}

@app.route("/admin/update_status", methods=['POST'])
def update_status():
    return json.dumps({"status": "success", "message": "Status updated successfully."}), 200, {'Content-Type': 'application/json'}

@app.route("/admin/delete_engineer", methods=['POST'])
def delete_engineer():
    try:
        data = request.get_json()
        if not data:
            return json.dumps({"status": "error", "message": "Missing JSON data."}), 400, {'Content-Type': 'application/json'}
            
        email = data.get('email', '').strip().lower()
        
        con = get_db()
        cur = con.cursor()
        cur.execute("DELETE FROM users WHERE LOWER(email) = ? AND role = 3", (email,))
        con.commit()
            
        return json.dumps({"status": "success", "message": "Engineer deleted successfully."}), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}), 500, {'Content-Type': 'application/json'}

@app.route("/admin/add_project", methods=['POST'])
def add_project():
    try:
        pcat = request.form.get('pcat', '').strip()
        pname = request.form.get('pname', '').strip()
        ptype = request.form.get('ptype', '').strip()
        duration = request.form.get('duration', '').strip()
        area = request.form.get('area', '').strip()
        client = request.form.get('client', '').strip()
        location = request.form.get('location', '').strip()
        bheight = request.form.get('bheight', '').strip()
        ftype = request.form.get('ftype', '').strip()
        fmaterial = request.form.get('fmaterial', 'Reinforced Concrete (M40 grade)').strip()
        pspace = request.form.get('pspace', '').strip()
        erate = request.form.get('erate', '').strip()
        sdesc = request.form.get('sdesc', '').strip()
        plog = request.form.get('plog', '').strip()
        status = request.form.get('status', 'Ongoing').strip()
        
        # Determine fallback picture based on category
        if 'Commercial' in pcat:
            img_url = 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=600&q=70'
        elif 'Residential' in pcat:
            img_url = 'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=600&q=70'
        else:
            img_url = 'https://images.unsplash.com/photo-1590069261209-f8e9b8642343?auto=format&fit=crop&w=600&q=70'
            
        # Check if project picture is uploaded
        if 'projectImage' in request.files:
            file = request.files['projectImage']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                unique_filename = f"proj_{timestamp}_{filename}"
                filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
                absolute_filepath = os.path.join('d:/internship netsoft/python/website', filepath)
                file.save(absolute_filepath)
                img_url = "/" + filepath.replace("\\", "/")

        con = get_db()
        cur = con.cursor()
        cur.execute("""
            INSERT INTO projects (pcat, pname, ptype, duration, area, client, location, bheight, ftype, fmaterial, pspace, erate, sdesc, poverview, plog, status, img)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (pcat, pname, ptype, duration, area, client, location, bheight, ftype, fmaterial, pspace, erate, sdesc, plog, plog, status, img_url))
        con.commit()
            
        return json.dumps({"status": "success", "message": "Project added successfully."}), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}), 500, {'Content-Type': 'application/json'}

@app.route("/admin/delete_project", methods=['POST'])
def delete_project():
    try:
        data = request.get_json()
        if not data:
            return json.dumps({"status": "error", "message": "Missing JSON data."}), 400, {'Content-Type': 'application/json'}
            
        project_id = data.get('id')
        if not project_id:
            return json.dumps({"status": "error", "message": "Project ID is required."}), 400, {'Content-Type': 'application/json'}
            
        con = get_db()
        cur = con.cursor()
        cur.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        con.commit()
            
        return json.dumps({"status": "success", "message": "Project deleted successfully."}), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}), 500, {'Content-Type': 'application/json'}

# API to retrieve all dynamic projects
@app.route("/api/projects", methods=['GET'])
def api_projects():
    try:
        con = get_db()
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM projects")
        rows = cur.fetchall()
        projects = [dict(row) for row in rows]
        return json.dumps(projects), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}), 500, {'Content-Type': 'application/json'}

# API to retrieve project detail along with associated reviews
@app.route("/api/project/<int:project_id>", methods=['GET'])
def api_project_detail(project_id):
    try:
        con = get_db()
        con.row_factory = sql.Row
        cur = con.cursor()
        
        cur.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        project_row = cur.fetchone()
        if not project_row:
            return json.dumps({"status": "error", "message": "Project not found."}), 404, {'Content-Type': 'application/json'}
        
        project = dict(project_row)
        
        cur.execute("""
            SELECT r.*, u.name as reviewer_name, u.img as reviewer_img
            FROM reviews r
            JOIN users u ON r.user_id = u.id
            WHERE r.project_id = ?
            ORDER BY r.id DESC
        """, (project_id,))
        reviews = [dict(row) for row in cur.fetchall()]
        project['reviews'] = reviews
        
        return json.dumps(project), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}), 500, {'Content-Type': 'application/json'}

# API to post a review to a project
@app.route("/api/project/<int:project_id>/add_review", methods=['POST'])
def api_add_review(project_id):
    try:
        data = request.get_json()
        if not data:
            return json.dumps({"status": "error", "message": "Missing review data."}), 400, {'Content-Type': 'application/json'}
            
        user_id = data.get('user_id')
        review_text = data.get('review_text', '').strip()
        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if not user_id or not review_text:
            return json.dumps({"status": "error", "message": "User ID and review content are required."}), 400, {'Content-Type': 'application/json'}
            
        con = get_db()
        cur = con.cursor()
        cur.execute("""
            INSERT INTO reviews (project_id, user_id, review_text, date_time)
            VALUES (?, ?, ?, ?)
        """, (project_id, user_id, review_text, date_time))
        con.commit()
        
        return json.dumps({"status": "success", "message": "Review submitted successfully."}), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}), 500, {'Content-Type': 'application/json'}

# API to submit image crack analysis predictions
@app.route("/api/analyze", methods=['POST'])
def api_analyze():
    try:
        if 'crackImage' in request.files:
            file = request.files['crackImage']
        elif 'inspectionImage' in request.files:
            file = request.files['inspectionImage']
        else:
            return json.dumps({"status": "error", "message": "No file uploaded."}), 400, {'Content-Type': 'application/json'}
            
        userid = request.form.get('userid', 2)
        
        if file.filename == '':
            return json.dumps({"status": "error", "message": "No selected file."}), 400, {'Content-Type': 'application/json'}
            
        if file:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            unique_filename = f"{timestamp}_{filename}"
            filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
            absolute_filepath = os.path.join('d:/internship netsoft/python/website', filepath)
            file.save(absolute_filepath)
            
            is_crack = random.choice([True, False])
            confidence = round(random.uniform(0.78, 0.98), 2)
            
            if is_crack:
                pred_result = "Crack Detected"
                avg_depths = f"{round(random.uniform(1.2, 4.8), 1)} mm"
            else:
                pred_result = "No Crack Detected"
                avg_depths = "0.0 mm"
                confidence = round(random.uniform(0.92, 0.99), 2)
            
            pred_image = filepath
            original_image = filepath
            date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            con = get_db()
            cur = con.cursor()
            cur.execute("""
                INSERT INTO prediction (userid, pred_result, pred_image, orginal_image, avg_depths, confidence, date_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (userid, pred_result, pred_image, original_image, avg_depths, confidence, date_time))
            con.commit()
            
            prediction_id = cur.lastrowid
            prediction_data = {
                "id": prediction_id,
                "userid": userid,
                "pred_result": pred_result,
                "pred_image": "/" + pred_image.replace("\\", "/"),
                "orginal_image": "/" + original_image.replace("\\", "/"),
                "avg_depths": avg_depths,
                "confidence": confidence,
                "date_time": date_time
            }
            return json.dumps({"status": "success", "prediction": prediction_data}), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}), 500, {'Content-Type': 'application/json'}

# API to retrieve prediction records for the current user
@app.route("/api/predictions", methods=['GET'])
def api_predictions():
    try:
        userid = request.args.get('userid')
        if not userid:
            return json.dumps({"status": "error", "message": "Missing User ID."}), 400, {'Content-Type': 'application/json'}
            
        con = get_db()
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM prediction WHERE userid = ? ORDER BY id DESC", (userid,))
        rows = cur.fetchall()
        predictions = []
        for row in rows:
            predictions.append({
                "id": row["id"],
                "userid": row["userid"],
                "pred_result": row["pred_result"],
                "pred_image": "/" + row["pred_image"].replace("\\", "/"),
                "orginal_image": "/" + row["orginal_image"].replace("\\", "/"),
                "avg_depths": row["avg_depths"],
                "confidence": row["confidence"],
                "date_time": row["date_time"]
            })
        return json.dumps(predictions), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}), 500, {'Content-Type': 'application/json'}

# API to retrieve all reviews submitted by a specific user
@app.route("/api/user_reviews", methods=['GET'])
def api_user_reviews():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return json.dumps({"status": "error", "message": "Missing User ID."}), 400, {'Content-Type': 'application/json'}
            
        con = get_db()
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("""
            SELECT r.*, p.pname as project_name
            FROM reviews r
            JOIN projects p ON r.project_id = p.id
            WHERE r.user_id = ?
            ORDER BY r.id DESC
        """, (user_id,))
        reviews = [dict(row) for row in cur.fetchall()]
        return json.dumps(reviews), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}), 500, {'Content-Type': 'application/json'}

if __name__ == "__main__":
    app.run(debug=True)
