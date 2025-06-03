from flask import Flask, request, jsonify, session, render_template, send_from_directory, redirect, url_for
from ldap3 import Server, Connection, ALL, SUBTREE
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'testing'

UPLOAD_FOLDER_BASE = 'uploads'
UPLOAD_FOLDER = {
    'student': os.path.join(UPLOAD_FOLDER_BASE, 'students'),
    'teacher': os.path.join(UPLOAD_FOLDER_BASE, 'teachers')
}

# Chú ý là nếu tạo folder ở đây thì sẽ cần run app với quyền cao hơn, nên cần tạo folder trước khi chạy ứng dụng
for folder in UPLOAD_FOLDER.values():
    os.makedirs(folder, exist_ok=True)

LDAP_SERVER = 'ldap://10.2.1.1'
LDAP_BASE_DN = 'DC=iris,DC=com,DC=vn'
LDAP_BIND_USER = '20215607@iris.com.vn'
LDAP_BIND_PASSWORD = 'User@123'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        server = Server(LDAP_SERVER, get_info=ALL)

        try:
            conn = Connection(server, user=LDAP_BIND_USER, password=LDAP_BIND_PASSWORD, auto_bind=True)
            conn.search(LDAP_BASE_DN, f'(sAMAccountName={username})', SUBTREE, attributes=['distinguishedName'])

            if not conn.entries:
                return render_template('login.html', error='User không tồn tại!')

            user_dn = conn.entries[0].distinguishedName.value
            conn.unbind()
        except Exception as e:
            return render_template('login.html', error=f'Lỗi kết nối LDAP: {str(e)}')

        try:
            user_conn = Connection(server, user=user_dn, password=password, auto_bind=True)
            role = 'unknown'
            if 'OU=Students' in user_dn:
                role = 'student'
            elif 'OU=Teachers' in user_dn:
                role = 'teacher'

            session['username'] = username
            session['role'] = role
            user_conn.unbind()
            return redirect(url_for(f'{role}_home'))
        except Exception as e:
            return render_template('login.html', error='Đăng nhập thất bại!')

    return render_template('login.html')


@app.route('/')
def index():
    if 'username' in session:
        if session['role'] == 'teacher':
            return redirect(url_for('teacher_home'))
        elif session['role'] == 'student':
            return redirect(url_for('student_home'))
    return redirect(url_for('login'))


@app.route('/student')
def student_home():
    if 'username' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
    files = os.listdir(UPLOAD_FOLDER['student'])
    return render_template('student.html', username=session['username'], files=files)


@app.route('/teacher', methods=['GET', 'POST'])
def teacher_home():
    if 'username' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('teacher.html', username=session['username'], error='Không có file upload!')

        file = request.files['file']
        if file.filename == '':
            return render_template('teacher.html', username=session['username'], error='Tên file trống!')

        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER['teacher'], filename))

    files = os.listdir(UPLOAD_FOLDER['teacher'])
    return render_template('teacher.html', username=session['username'], files=files)


@app.route('/uploads/<role>/<filename>')
def uploaded_file(role, filename):
    if role not in UPLOAD_FOLDER:
        return "Không hợp lệ!", 403
    if 'username' not in session or session['role'] != role:
        return redirect(url_for('login'))

    return send_from_directory(UPLOAD_FOLDER[role], filename)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
