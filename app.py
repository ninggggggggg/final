from flask import Flask, request, jsonify, session, render_template, send_from_directory, redirect, url_for, render_template_string
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

# Tạo folder nếu chưa có
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

        # GIẢ LẬP NGƯỜI DÙNG CỐ ĐỊNH
        mock_users = {
            'studentA': {'password': '123', 'role': 'student'},
            'teacherA': {'password': '456', 'role': 'teacher'}
        }

        user = mock_users.get(username)
        if user and user['password'] == password:
            session['username'] = username
            session['role'] = user['role']
            return redirect(url_for(f"{user['role']}_home"))
        else:
            return render_template('login.html', error='Sai tài khoản hoặc mật khẩu!')

    return render_template('login.html')


@app.route('/')
def index():
    if 'username' in session:
        if session['role'] == 'teacher':
            return redirect(url_for('teacher_home'))
        elif session['role'] == 'student':
            return redirect(url_for('student_home'))
    return redirect(url_for('login'))


@app.route('/search')
def search_files():
    role = request.args.get('role')

    # Không kiểm tra session! Mặc định ai cũng dùng được
    if role not in UPLOAD_FOLDER:
        return "Role không hợp lệ!", 400

    search_term = request.args.get('q', '').lower()
    all_files = os.listdir(UPLOAD_FOLDER[role])
    filtered_files = [f for f in all_files if search_term in f.lower()] if search_term else all_files

    ssti_input = request.args.get('q', '')

    template = f"""
    <form action="" method="get">
        <input type="hidden" name="role" value="{role}">
        <input type="text" name="q" value="{ssti_input}" placeholder="Tìm tài liệu...">
        <button type="submit">Search</button>
    </form>

    <h3>Tìm thấy {len(filtered_files)} file</h3>
    <p>File đầu tiên tìm được (có thể chứa SSTI): {ssti_input}</p>

    <ul>
        {{% for file in files %}}
            <li>{{{{ file }}}}</li>
        {{% endfor %}}
    </ul>
    """

    return render_template_string(template, files=filtered_files)

@app.route('/student', methods=['GET'])
def student_home():
    if 'username' not in session or session['role'] != 'student':
        return redirect(url_for('login'))

    return """
    <h1>Chào học sinh: {}</h1>
    <form action="/search" method="get">
        <input type="hidden" name="role" value="student">
        <input type="text" name="q" placeholder="Tìm tài liệu...">
        <button type="submit">Tìm kiếm</button>
    </form>
    """.format(session['username'])

@app.route('/teacher', methods=['GET', 'POST'])
def teacher_home():
    if 'username' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))

    error = None
    if request.method == 'POST':
        if 'file' not in request.files:
            error = 'Không có file upload!'
        else:
            file = request.files['file']
            if file.filename == '':
                error = 'Tên file trống!'
            else:
                filename = secure_filename(file.filename)
                file.save(os.path.join(UPLOAD_FOLDER['teacher'], filename))

    return """
    <h1>Chào giáo viên: {}</h1>
    {}
    <form action="" method="post" enctype="multipart/form-data">
        <input type="file" name="file">
        <button type="submit">Upload</button>
    </form>

    <form action="/search" method="get">
        <input type="hidden" name="role" value="teacher">
        <input type="text" name="q" placeholder="Tìm tài liệu...">
        <button type="submit">Tìm kiếm</button>
    </form>
    """.format(
        session['username'],
        f"<p style='color:red'>{error}</p>" if error else ""
    )

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
