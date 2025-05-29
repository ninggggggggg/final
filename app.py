from flask import Flask, request, jsonify, session, render_template, send_from_directory, redirect, url_for
from ldap3 import Server, Connection, ALL
import os

app = Flask(__name__)
app.secret_key = 'testing'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

LDAP_SERVER = 'ldap://10.2.1.1'
LDAP_BASE_DN = 'DC=iris,DC=com,DC=vn'

@app.route('/')
def index():
    if 'username' in session:
        if session['role'] == 'teacher':
            return redirect(url_for('teacher_home'))
        elif session['role'] == 'student':
            return redirect(url_for('student_home'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_dn = f'CN={username},OU=Users,{LDAP_BASE_DN}'
        server = Server(LDAP_SERVER, get_info=ALL)
        conn = Connection(server, user=user_dn, password=password, auto_bind=True)
        if conn.bind():
            conn.search(search_base=LDAP_BASE_DN,
                        search_filter=f'(sAMAccountName={username})',
                        attributes=['distinguishedName'])
            dn = conn.entries[0].distinguishedName.value
            if 'OU=Students' in dn:
                role = 'student'
            elif 'OU=Teachers' in dn:
                role = 'teacher'
            else:
                role = 'unknown'
            session['username'] = username
            session['role'] = role
            return redirect(url_for(f'{role}_home'))  # teacher_home hoặc student_home
        else:
            return render_template('login.html', error='Đăng nhập thất bại!')
    return render_template('login.html')

@app.route('/student')
def student_home():
    if 'username' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
    files = os.listdir(UPLOAD_FOLDER)
    return render_template('student.html', username=session['username'], files=files)

@app.route('/teacher', methods=['GET', 'POST'])
def teacher_home():
    if 'username' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('teacher.html', username=session['username'], error='Không có file upload!')
        file = request.files['file']
        file.save(os.path.join(UPLOAD_FOLDER, file.filename))
    files = os.listdir(UPLOAD_FOLDER)
    return render_template('teacher.html', username=session['username'], files=files)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
