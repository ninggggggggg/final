from ldap3 import Server, Connection, All

LDAP_SERVER = 'ldap://10.2.1.1'
USERNAME = '20215607@iris.com.vn'  # Hoặc CN=20215607,OU=Users,DC=iris,DC=com,DC=vn
PASSWORD = '123'

# Khởi tạo server object
server = Server(LDAP_SERVER, get_info=ALL)

# Kết nối với user + password
try:
    conn = Connection(server, user=USERNAME, password=PASSWORD, auto_bind=True)
    if conn.bind():
        print('Kết nối LDAP thành công!')
        conn.unbind()
    else:
        print('Kết nối LDAP thất bại!')
except Exception as e:
    print(f'Kết nối LDAP lỗi: {e}')