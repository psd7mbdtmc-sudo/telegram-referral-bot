import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# خادم ويب مصغر لتلبية شروط منفذ الويب على Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running successfully!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# تشغيل خادم الويب في خلفية الكود حتى لا يتعطل البوت
threading.Thread(target=run_server, daemon=True).start()
