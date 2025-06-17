from flask import Flask, request, jsonify, session, render_template, send_from_directory, redirect, url_for, render_template_string
from ldap3 import Server, Connection, ALL, SUBTREE
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

UPLOAD_FOLDER_BASE = 'uploads'
UPLOAD_FOLDER = {
    'student': os.path.join(UPLOAD_FOLDER_BASE, 'students'),
    'teacher': os.path.join(UPLOAD_FOLDER_BASE, 'teachers')
}

# Tạo folder nếu chưa có
for folder in UPLOAD_FOLDER.values():
    os.makedirs(folder, exist_ok=True)

LDAP_SERVER = os.getenv("LDAP_SERVER")
LDAP_BASE_DN = os.getenv("LDAP_BASE_DN")
LDAP_BIND_USER = os.getenv("LDAP_BIND_USER")
LDAP_BIND_PASSWORD = os.getenv("LDAP_BIND_PASSWORD")



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if 'guest_access' in request.form:
            session['username'] = 'guest'
            session['role'] = 'guest'
            return redirect(url_for('labs_home'))
        
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

@app.route('/labs')
def labs_home():
    # Dữ liệu cho Kill Chain
    kill_chain = [
        {
            "phase": "1. Reconnaissance",
            "description": "Thu thập thông tin mục tiêu và dò quét hệ thống.",
            "labs": [1]
        },
        {
            "phase": "2. Weaponization", 
            "description": "Chuẩn bị công cụ và payload để tấn công hệ thống.",
            "labs": [2]
        },
        {
            "phase": "3. Delivery",
            "description": "Gửi payload qua endpoint /search và đăng nhập máy trạm.",
            "labs": [1, 2]
        },
        {
            "phase": "4. Exploitation",
            "description": "Khai thác lỗ hổng SSTI và kỹ thuật Kerberoasting.",
            "labs": [1, 2, 3]
        },
        {
            "phase": "5. Installation",
            "description": "Truy cập domain controller và cài foothold (hash access).",
            "labs": [3]
        },
        {
            "phase": "6. Command & Control",
            "description": "Điều khiển máy chủ thông qua kỹ thuật Pass-the-Hash.",
            "labs": [3]
        },
        {
            "phase": "7. Actions on Objectives",
            "description": "Chiếm quyền truy cập, trích xuất dữ liệu nhạy cảm.",
            "labs": [1, 2, 3]
        }
    ]

    # Dữ liệu cho các Lab
    labs = [
        {
            "id": 1,
            "title": "💥 Exploiting SSTI in Flask WebApp",
            "category": "Reconnaissance",
            "difficulty": "Beginner",
            "description": "Khám phá kỹ thuật thu thập thông tin và khai thác lỗ hổng Server-Side Template Injection (SSTI) trên một ứng dụng Flask cấu hình sai.",
            "objectives": [
                "Dò tìm endpoint bị lộ hoặc cấu hình sai",
                "Xác định và khai thác lỗ hổng SSTI",
                "Thực thi mã lệnh và đọc file nội bộ trên server",
                "Trích xuất thông tin nhạy cảm phục vụ tấn công kế tiếp"
            ],
            "url": "/labs/1"
        },
        {
            "id": 2,
            "title": "🧠 Privilege Escalation & AD Hash Extraction",
            "category": "Lateral Movement",
            "difficulty": "Intermediate",
            "description": "Mô phỏng quá trình leo thang đặc quyền trong môi trường domain thông qua kỹ thuật Kerberoasting và AS-REP Roasting, bắt đầu từ một tài khoản người dùng thông thường đã bị chiếm quyền.",
            "objectives": [
                "Chiếm quyền truy cập máy trạm nội bộ (Workstation01)",
                "Thực hiện AS-REP Roasting để thu thập hash từ tài khoản không yêu cầu pre-auth",
                "Thực hiện Kerberoasting để thu thập hash từ tài khoản có SPN",
                "Crack offline các hash để lấy thông tin đăng nhập có đặc quyền cao hơn"
            ],
            "url": "/labs/2"
        },
        {
            "id": 3,
            "title": "🛡️ Exploiting Backup Privileges on Domain Controller",
            "category": "Privilege Escalation",
            "difficulty": "Advanced",
            "description": "Mô phỏng tấn công vào Domain Controller bằng cách lạm dụng quyền SeBackupPrivilege để dump registry hive (SAM & SYSTEM) và trích xuất hash mật khẩu từ máy chủ AD, không cần đặc quyền admin.",
            "objectives": [
                "Sử dụng tài khoản có quyền SeBackupPrivilege (Backup Operators)",
                "Dump offline SAM và SYSTEM từ Domain Controller",
                "Trích xuất và phân tích NTLM hash bằng công cụ như secretsdump.py",
                "Sử dụng kỹ thuật Pass-the-Hash hoặc crack offline để mở rộng quyền truy cập"
            ],
            "url": "/labs/3"
        }
    ]
    
    return render_template('lab.html', kill_chain=kill_chain, labs=labs)

@app.route('/labs/1')
def lab1():
    return render_template('lab1.html')

@app.route('/labs/2')
def lab2():
    return render_template('lab2.html')

@app.route('/labs/3')
def lab3():
    return render_template('lab3.html')



@app.route('/search')
def search_files():
    role = request.args.get('role')

    if role not in UPLOAD_FOLDER:
        role = 'student'  # Mặc định là student nếu không có role

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

@app.route('/student', methods=['GET', 'POST'])
def student_home():
    if 'username' not in session or session['role'] != 'student':
        return redirect(url_for('login'))

    error = None
    success = None

    if request.method == 'POST':
        if 'file' not in request.files:
            error = 'Không có file upload!'
        else:
            file = request.files['file']
            if file.filename == '':
                error = 'Tên file trống!'
            else:
                try:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(UPLOAD_FOLDER['student'], filename))
                    success = f'Đã tải lên thành công: {filename}'
                except Exception as e:
                    error = f'Lỗi khi tải file: {str(e)}'

    return render_template('student_home.html', error=error, success=success)


@app.route('/teacher', methods=['GET', 'POST'])
def teacher_home():
    if 'username' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))

    error = None
    success = None
    
    if request.method == 'POST':
        if 'file' not in request.files:
            error = 'Không có file upload!'
        else:
            file = request.files['file']
            if file.filename == '':
                error = 'Tên file trống!'
            else:
                try:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(UPLOAD_FOLDER['teacher'], filename))
                    success = f'Đã tải lên thành công: {filename}'
                except Exception as e:
                    error = f'Lỗi khi tải file: {str(e)}'

    return render_template('teacher_home.html', error=error, success=success)

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