#!/usr/bin/env python3
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT / "MINOR PROJECT GROUP NO"
DISPLAY = os.environ.get("APP_DISPLAY", ":99")
VNC_PORT = int(os.environ.get("VNC_PORT", "5901"))
WEB_PORT = int(os.environ.get("WEB_PORT", "6080"))
JAVA = os.environ.get(
    "JAVA",
    str(Path.home() / ".local/jdks/temurin-27/bin/java"),
)


def fail(message):
    print(message, file=sys.stderr)
    raise SystemExit(1)


for executable in ("Xvfb", "fluxbox", "x11vnc", "websockify"):
    if not shutil.which(executable):
        fail(f"Missing {executable}; install the Codespaces desktop packages first.")

if not Path(JAVA).is_file() and not shutil.which(JAVA):
    fail(f"Java executable not found: {JAVA}")

version = subprocess.run(
    [JAVA, "-version"], capture_output=True, text=True, check=False
)
match = re.search(r'version "(\d+)', version.stderr + version.stdout)
if version.returncode != 0 or not match or int(match.group(1)) < 27:
    fail(f"Java 27 or later is required. Could not verify {JAVA}.")

jar = APP_DIR / "minorproject.jar"
if not jar.is_file():
    fail(f"Application JAR not found: {jar}")

environment = os.environ.copy()
environment["DISPLAY"] = DISPLAY
children = []
stopping = False


def stop(signum, frame):
    global stopping
    stopping = True


def cleanup():
    for child in reversed(children):
        if child.poll() is None:
            child.terminate()
    for child in reversed(children):
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()


signal.signal(signal.SIGINT, stop)
signal.signal(signal.SIGTERM, stop)

try:
    display_number = DISPLAY.removeprefix(":").split(".", 1)[0]
    socket_path = Path(f"/tmp/.X11-unix/X{display_number}")
    if socket_path.exists():
        fail(f"Display {DISPLAY} is already in use; set APP_DISPLAY to another display.")

    children.append(
        subprocess.Popen(
            ["Xvfb", DISPLAY, "-screen", "0", "1280x800x24", "-nolisten", "tcp"],
            env=environment,
        )
    )
    for _ in range(100):
        if children[0].poll() is not None:
            fail("Xvfb exited before its display became ready.")
        if socket_path.exists():
            break
        time.sleep(0.1)
    else:
        fail(f"Timed out waiting for display {DISPLAY}.")

    children.append(subprocess.Popen(["fluxbox"], env=environment))
    children.append(
        subprocess.Popen(
            [
                "x11vnc",
                "-display",
                DISPLAY,
                "-forever",
                "-shared",
                "-rfbport",
                str(VNC_PORT),
                "-localhost",
                "-nopw",
            ],
            env=environment,
        )
    )
    children.append(
        subprocess.Popen(
            [
                "websockify",
                "--web",
                "/usr/share/novnc",
                f"0.0.0.0:{WEB_PORT}",
                f"127.0.0.1:{VNC_PORT}",
            ],
            env=environment,
        )
    )

    if codespace := os.environ.get("CODESPACE_NAME"):
        print(
            f"Open https://{codespace}-{WEB_PORT}.app.github.dev/"
            "vnc.html?autoconnect=true&resize=remote&path=websockify",
            flush=True,
        )
        print(
            f"Keep forwarded port {WEB_PORT} private in the Codespaces Ports tab.",
            flush=True,
        )
    else:
        print(f"Open http://localhost:{WEB_PORT}/vnc.html?autoconnect=true", flush=True)

    os.chdir(APP_DIR)
    children.append(subprocess.Popen([JAVA, "-jar", str(jar)], env=environment))

    while not stopping:
        for child in children:
            result = child.poll()
            if result is not None:
                if child is children[-1]:
                    raise SystemExit(result)
                fail(f"A desktop service exited unexpectedly with status {result}.")
        time.sleep(0.5)
finally:
    cleanup()
