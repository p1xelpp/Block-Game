import argparse
import sys

# -------------------------
# PARSE ARGS
# -------------------------
parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=["1", "2", "3"], default="1")
parser.add_argument("--port", type=int, default=27015)
parser.add_argument("--ip", default="localhost")
args = parser.parse_args()

mode = args.mode
port = args.port
ip = args.ip

# -------------------------
# MODE 2 = HEADLESS (Render)
# Ursina mag NIET geladen worden!
# -------------------------
if mode == "2":
    from c00lnet import Server, ServerClient

    print("Running in headless server mode (Render)")

    server = Server(port=port)
    print(f"Server running on port {port}")

    # GEEN Ursina importeren
    # GEEN C00lWorld importeren
    # GEEN window openen
    # GEEN game starten

    while True:
        pass  # keep server alive


# -------------------------
# MODE 1 & 3 = CLIENT (LOCAL)
# Ursina mag WEL geladen worden
# -------------------------
else:
    from ezy3d import C00lWorld
    from c00lnet import ServerClient

    net = None

    if mode == "3":
        net = ServerClient()
        if not net.connect(ip, port):
            raise SystemExit(f"Could not connect to server {ip}:{port}")

    game = C00lWorld(network=net)
    game.test_plane()
    game.start()
