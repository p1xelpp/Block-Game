from ezy3d import C00lWorld
from c00lnet import Server, ServerClient
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=["1", "2", "3"], default="1", help="1=Singleplayer, 2=Host, 3=Join")
parser.add_argument("--port", type=int, default=27015)
parser.add_argument("--ip", default="localhost")
args = parser.parse_args()

mode = args.mode
port = args.port
ip = args.ip

net = None
server = None

# -------------------------
# MODE 2 = HOST SERVER
# -------------------------
if mode == "2":
    server = Server(port=port)
    net = ServerClient()
    if not net.connect("localhost", port):
        raise SystemExit("Could not connect to local server")

# -------------------------
# MODE 3 = JOIN SERVER
# -------------------------
elif mode == "3":
    net = ServerClient()
    if not net.connect(ip, port):
        raise SystemExit(f"Could not connect to server {ip}:{port}")

# -------------------------
# CREATE GAME (ONE TIME!)
# -------------------------
if mode == "1":
    game = C00lWorld()
else:
    game = C00lWorld(network=net)

# -------------------------
# START GAME
# -------------------------
game.test_plane()
game.start()
