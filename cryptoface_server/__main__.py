from cryptoface_server import create_server
import sys

if sys.argv == 3:
    HOST = sys.argv[1]
    PORT = sys.argv[2]
else:
    HOST = "127.0.0.1"
    PORT = 4567

app = create_server()

app.run(HOST, PORT)
