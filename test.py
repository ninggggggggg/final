from flask import Flask, request, session, render_template_string, redirect, url_for
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'testing')  # fallback nếu chưa set env var

# Cấu hình folder
UPLOAD_FOLDER_BASE = 'uploads'
UPLOAD_FOLDER = {
    'student': os.path.join(UPLOAD_FOLDER_BASE, 'students'),
    'teacher': os.path.join(UPLOAD_FOLDER_BASE, 'teachers')
}

@app.route('/student', methods=['GET', 'POST'])
def student_home():
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


if __name__ == '__main__':
    app.run(debug=True)