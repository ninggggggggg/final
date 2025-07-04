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


@app.route('/student', methods=['GET', 'POST'])
def student_home():
    if 'username' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
    search_term = request.args.get('q', '').lower()

    all_files = os.listdir(UPLOAD_FOLDER['student'])

    if search_term:
        filtered_files = [f for f in all_files if search_term in f.lower()]
    else:
        filtered_files = all_files

    ssti_input = request.args.get('q', '')  # GIẢ LẬP SSTI TỪ INPUT

    template = f"""
    <form action="" method="get">
        <input type="text" name="q" value="{ssti_input}" placeholder="Tìm tài liệu...">
        <button type="submit">Search</button>
    </form>
    <h3>Tìm thấy {len(filtered_files)} file</h3>

    <!-- Đây là chỗ có lỗi SSTI -->
    <p>File đầu tiên tìm được (có thể chứa SSTI): {ssti_input}</p>

    <ul>
        {{% for file in files %}}
            <li>{{{{ file }}}}</li>
        {{% endfor %}}
    </ul>
    """

    return render_template_string(template, files=filtered_files)



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
