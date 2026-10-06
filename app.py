import os, sqlite3, json, urllib.request
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, Response

app = Flask(__name__)
app.secret_key = 'projecthub_secret_key_12345'
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DATABASE = os.path.join(os.path.dirname(__file__), 'database.db')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT NOT NULL,
        tech_stack TEXT NOT NULL, file_path TEXT, status TEXT NOT NULL DEFAULT 'Not Started',
        owner_id INTEGER NOT NULL, created_at TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS project_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER NOT NULL, user_id INTEGER NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
        message TEXT NOT NULL, created_at TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

init_db()

def get_current_user():
    return {'id': session['user_id'], 'name': session.get('user_name')} if 'user_id' in session else None

def generate_fallback_thesis(title, description, tech_stack, status):
    return f"""AI GENERATED PROJECT THESIS
Project Title: {title} | Tech Stack: {tech_stack} | Status: {status}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
================================================================================

1. INTRODUCTION
The project "{title}" is designed to address key practical challenges in its domain through an integrated digital solution.

2. PROBLEM STATEMENT
Manual and disjointed processes often lead to inefficiencies, communication gaps, and tracking delays. "{title}" provides a centralized platform to overcome these barriers.

3. OBJECTIVES
- Build a responsive management platform for "{title}".
- Integrate core stack capabilities using {tech_stack}.
- Monitor development milestones (currently at {status} status).
- Ensure role-based security and collaborative communication.

4. PROPOSED SOLUTION
The system implements a lightweight architecture with direct data workflows. Overview:
"{description}"

5. TECHNOLOGIES USED
The solution is built using: {tech_stack}. These tools provide high reliability, fast response times, and ease of deployment.

6. METHODOLOGY
Development follows an agile process: requirements specification, database modeling, route development, and iterative validation.

7. EXPECTED RESULTS
"{title}" delivers an intuitive operational environment with automated records, file sharing, and direct team coordination.

8. CONCLUSION
"{title}" demonstrates how structured software engineering principles solve domain problems effectively using {tech_stack}.

9. FUTURE SCOPE
Potential future enhancements include automated notifications, advanced progress analytics, and RESTful mobile APIs.
"""

def generate_ai_thesis(title, description, tech_stack, status):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return generate_fallback_thesis(title, description, tech_stack, status)
    try:
        req_data = json.dumps({
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are an academic thesis writer. Generate clean plain text."},
                {"role": "user", "content": f"Write a 9-section project thesis (1. Introduction, 2. Problem Statement, 3. Objectives, 4. Proposed Solution, 5. Technologies Used, 6. Methodology, 7. Expected Results, 8. Conclusion, 9. Future Scope) for {title}. Tech: {tech_stack}. Desc: {description}. Status: {status}."}
            ],
            "temperature": 0.7
        }).encode('utf-8')
        req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=req_data, headers={
            "Content-Type": "application/json", "Authorization": f"Bearer {api_key}"
        })
        with urllib.request.urlopen(req, timeout=10) as res:
            return json.loads(res.read().decode('utf-8'))['choices'][0]['message']['content']
    except Exception:
        return generate_fallback_thesis(title, description, tech_stack, status)

@app.route('/')
def index():
    conn = get_db()
    projects = conn.execute('''SELECT p.*, u.name as owner_name FROM projects p 
                               JOIN users u ON p.owner_id = u.id ORDER BY p.id DESC LIMIT 6''').fetchall()
    conn.close()
    return render_template('index.html', user=get_current_user(), projects=projects)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if not name or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')
        conn = get_db()
        if conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone():
            conn.close()
            flash('An account with this email already exists.', 'error')
            return render_template('register.html')
        conn.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
                     (name, email, generate_password_hash(password)))
        conn.commit()
        conn.close()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'error')
        return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login to access the dashboard.', 'error')
        return redirect(url_for('login'))
    conn = get_db()
    my_projects = conn.execute('''SELECT p.*, u.name as owner_name FROM projects p 
                                  JOIN users u ON p.owner_id = u.id WHERE p.owner_id = ? ORDER BY p.id DESC''', 
                               (session['user_id'],)).fetchall()
    all_projects = conn.execute('''SELECT p.*, u.name as owner_name FROM projects p 
                                   JOIN users u ON p.owner_id = u.id ORDER BY p.id DESC''').fetchall()
    conn.close()
    return render_template('dashboard.html', user=get_current_user(), my_projects=my_projects, all_projects=all_projects)

@app.route('/create-project', methods=['GET', 'POST'])
def create_project():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        tech_stack = request.form.get('tech_stack', '').strip()
        file = request.files.get('project_file')
        if not title or not description or not tech_stack:
            flash('Title, description, and technology stack are required.', 'error')
            return render_template('create_project.html')
        filename = None
        if file and file.filename:
            if not file.filename.lower().endswith('.zip'):
                flash('Only .zip files are allowed for project uploads.', 'error')
                return render_template('create_project.html')
            clean_name = secure_filename(file.filename)
            filename = f"{int(datetime.now().timestamp())}_{clean_name}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''INSERT INTO projects (title, description, tech_stack, file_path, status, owner_id, created_at)
                       VALUES (?, ?, ?, ?, 'Not Started', ?, ?)''',
                    (title, description, tech_stack, filename, session['user_id'], datetime.now().strftime('%Y-%m-%d %H:%M')))
        new_id = cur.lastrowid
        conn.commit()
        conn.close()
        flash('Project created successfully!', 'success')
        return redirect(url_for('project_details', project_id=new_id))
    return render_template('create_project.html', user=get_current_user())

@app.route('/project/<int:project_id>')
def project_details(project_id):
    if 'user_id' not in session:
        flash('Please login to view project details.', 'error')
        return redirect(url_for('login'))
    conn = get_db()
    project = conn.execute('''SELECT p.*, u.name as owner_name, u.email as owner_email FROM projects p
                              JOIN users u ON p.owner_id = u.id WHERE p.id = ?''', (project_id,)).fetchone()
    if not project:
        conn.close()
        flash('Project not found.', 'error')
        return redirect(url_for('dashboard'))
    members = conn.execute('''SELECT u.id, u.name, u.email FROM project_members pm
                              JOIN users u ON pm.user_id = u.id WHERE pm.project_id = ?''', (project_id,)).fetchall()
    is_owner = (session['user_id'] == project['owner_id'])
    is_member = is_owner or any(m['id'] == session['user_id'] for m in members)
    messages = []
    if is_member:
        messages = conn.execute('''SELECT m.*, u.name as sender_name FROM messages m
                                  JOIN users u ON m.user_id = u.id WHERE m.project_id = ? ORDER BY m.id ASC''', (project_id,)).fetchall()
    conn.close()
    return render_template('project.html', project=project, members=members, messages=messages,
                           is_owner=is_owner, is_member=is_member, user=get_current_user())

@app.route('/project/<int:project_id>/status', methods=['POST'])
def update_status(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    project = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
    if not project or project['owner_id'] != session['user_id']:
        conn.close()
        flash('Only the project owner can change the project status.', 'error')
        return redirect(url_for('project_details', project_id=project_id))
    new_status = request.form.get('status')
    if new_status in ['Not Started', 'In Progress', 'Completed']:
        conn.execute('UPDATE projects SET status = ? WHERE id = ?', (new_status, project_id))
        conn.commit()
        flash(f'Project status updated to "{new_status}".', 'success')
    conn.close()
    return redirect(url_for('project_details', project_id=project_id))

@app.route('/project/<int:project_id>/invite', methods=['POST'])
def invite_user(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    project = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
    if not project or project['owner_id'] != session['user_id']:
        conn.close()
        flash('Only the project owner can invite members.', 'error')
        return redirect(url_for('project_details', project_id=project_id))
    email = request.form.get('email', '').strip().lower()
    invited_user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    if not invited_user:
        conn.close()
        flash('User with this email not found.', 'error')
        return redirect(url_for('project_details', project_id=project_id))
    if invited_user['id'] == project['owner_id'] or conn.execute(
        'SELECT id FROM project_members WHERE project_id = ? AND user_id = ?', (project_id, invited_user['id'])).fetchone():
        conn.close()
        flash('User is already the owner or member of this project.', 'error')
        return redirect(url_for('project_details', project_id=project_id))
    conn.execute('INSERT INTO project_members (project_id, user_id) VALUES (?, ?)', (project_id, invited_user['id']))
    conn.commit()
    conn.close()
    flash(f'{invited_user["name"]} has been added as a project member.', 'success')
    return redirect(url_for('project_details', project_id=project_id))

@app.route('/project/<int:project_id>/chat', methods=['POST'])
def send_chat(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    project = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
    if not project:
        conn.close()
        return redirect(url_for('dashboard'))
    is_owner = (project['owner_id'] == session['user_id'])
    is_invited = conn.execute('SELECT id FROM project_members WHERE project_id = ? AND user_id = ?',
                              (project_id, session['user_id'])).fetchone()
    if not (is_owner or is_invited):
        conn.close()
        flash('You do not have permission to post in this chat.', 'error')
        return redirect(url_for('project_details', project_id=project_id))
    msg = request.form.get('message', '').strip()
    if msg:
        conn.execute('INSERT INTO messages (project_id, user_id, message, created_at) VALUES (?, ?, ?, ?)',
                     (project_id, session['user_id'], msg, datetime.now().strftime('%Y-%m-%d %H:%M')))
        conn.commit()
    conn.close()
    return redirect(url_for('project_details', project_id=project_id))

@app.route('/download/<int:project_id>')
def download_project(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    project = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
    if not project:
        conn.close()
        return redirect(url_for('dashboard'))
    is_owner = (project['owner_id'] == session['user_id'])
    is_invited = conn.execute('SELECT id FROM project_members WHERE project_id = ? AND user_id = ?',
                              (project_id, session['user_id'])).fetchone()
    conn.close()
    if not (is_owner or is_invited):
        flash('Access denied. Only the project owner and invited members can download files.', 'error')
        return redirect(url_for('project_details', project_id=project_id))
    if not project['file_path']:
        flash('No file was uploaded for this project.', 'error')
        return redirect(url_for('project_details', project_id=project_id))
    return send_from_directory(app.config['UPLOAD_FOLDER'], project['file_path'], as_attachment=True)

@app.route('/thesis/<int:project_id>')
def view_thesis(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    project = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
    conn.close()
    if not project:
        return redirect(url_for('dashboard'))
    thesis = generate_ai_thesis(project['title'], project['description'], project['tech_stack'], project['status'])
    return render_template('thesis.html', project=project, thesis=thesis, user=get_current_user())

@app.route('/thesis/<int:project_id>/download')
def download_thesis(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    project = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
    conn.close()
    if not project:
        return redirect(url_for('dashboard'))
    thesis = generate_ai_thesis(project['title'], project['description'], project['tech_stack'], project['status'])
    filename = f"{''.join(c for c in project['title'] if c.isalnum() or c in ('_','-')) or 'project'}_thesis.txt"
    return Response(thesis, mimetype="text/plain", headers={"Content-Disposition": f"attachment;filename={filename}"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
