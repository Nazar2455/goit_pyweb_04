from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import socket
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Клас HTTP-обробника
class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == '/':  # Маршрут для головної сторінки
            self.send_html_file('index.html')
        elif parsed_url.path == '/message':  # Маршрут для сторінки форми
            self.send_html_file('message.html')
        else:  # Помилка 404
            self.send_html_file('error.html', 404)

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == '/submit':  # Обробка форми
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = urllib.parse.parse_qs(body)
            username = data.get('username', [''])[0]
            message = data.get('message', [''])[0]
            if username and message:
                self.send_to_socket_server({'username': username, 'message': message})
                self.send_response(302)
                self.send_header('Location', '/')
                self.end_headers()
            else:
                self.send_html_file('error.html', 400)
        else:
            self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        try:
            self.send_response(status)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open(filename, 'rb') as file:
                self.wfile.write(file.read())
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'File not found')

    def send_to_socket_server(self, message_dict):
        udp_ip = '127.0.0.1'
        udp_port = 5000
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.sendto(json.dumps(message_dict).encode(), (udp_ip, udp_port))
        finally:
            sock.close()

# Функція запуску HTTP-сервера
def run_http_server():
    server_address = ('', 3000)
    httpd = HTTPServer(server_address, HttpHandler)
    print("HTTP сервер запущено на порту 3000")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("HTTP сервер зупинено")
        httpd.server_close()

# UDP Socket сервер
def run_socket_server():
    udp_ip = '127.0.0.1'
    udp_port = 5000
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((udp_ip, udp_port))
    print(f"Socket сервер запущено на {udp_ip}:{udp_port}")
    try:
        while True:
            data, _ = sock.recvfrom(1024)
            message_dict = json.loads(data.decode())
            save_to_json(message_dict)
    except KeyboardInterrupt:
        print("Socket сервер зупинено")
    finally:
        sock.close()

# Збереження повідомлення в JSON-файл
def save_to_json(message_dict):
    timestamp = datetime.now().isoformat()
    file_path = 'storage/data.json'
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    data[timestamp] = message_dict
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

# Запуск серверів у різних потоках
if __name__ == '__main__':
    with ThreadPoolExecutor() as executor:
        executor.submit(run_http_server)
        executor.submit(run_socket_server)