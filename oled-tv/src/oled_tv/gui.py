import tkinter as tk
from tkinter import ttk
import serial
import time
import threading
import mss
from PIL import Image

from oled_tv.serial_manager import get_ports
from oled_tv.display import to_oled

START = 0xAA
END = 0x55

# ---------------- STATE ----------------
running = False
ser = None
thread = None

# ---------------- COLORS ----------------
BG = "#0f172a"
CARD = "#1e293b"
TEXT = "#e2e8f0"
GOOD = "#22c55e"
BAD = "#ef4444"
ACCENT = "#38bdf8"

# ---------------- MIRROR LOOP ----------------
def mirror_loop(top, left, width, height, status_label):
    global running, ser

    with mss.mss() as sct:
        while running:
            try:
                monitor = {
                    "top": top.get(),
                    "left": left.get(),
                    "width": width.get(),
                    "height": height.get()
                }

                shot = sct.grab(monitor)
                img = Image.frombytes("RGB", shot.size, shot.rgb)

                frame = to_oled(img)

                ser.write(bytes([START]))
                ser.write(frame)
                ser.write(bytes([END]))

            except Exception as e:
                status_label.config(text="Error", fg=BAD)
                stop_stream(status_label)
                return

            time.sleep(0.05)

# ---------------- START ----------------
def start_stream(port_var, top, left, width, height, status_label):
    global running, ser, thread

    if running:
        return

    port = port_var.get()
    if not port:
        status_label.config(text="No Port Selected", fg=BAD)
        return

    try:
        ser = serial.Serial(port, 115200, timeout=1)
        time.sleep(2)
    except:
        status_label.config(text="Connection Failed", fg=BAD)
        return

    running = True
    status_label.config(text="Streaming...", fg=GOOD)

    thread = threading.Thread(
        target=mirror_loop,
        args=(top, left, width, height, status_label),
        daemon=True
    )
    thread.start()

# ---------------- STOP ----------------
def stop_stream(status_label):
    global running, ser

    running = False

    try:
        if ser:
            ser.close()
    except:
        pass

    status_label.config(text="Stopped", fg=TEXT)

# ---------------- REFRESH PORTS ----------------
def refresh_ports(menu):
    menu["values"] = get_ports()

# ---------------- GUI ----------------
def launch_gui():
    root = tk.Tk()
    root.title("📺 OLED TV Driver")
    root.geometry("420x520")
    root.configure(bg=BG)

    def card(parent):
        f = tk.Frame(parent, bg=CARD, padx=10, pady=10)
        f.pack(fill="x", padx=10, pady=8)
        return f

    # TITLE
    tk.Label(
        root,
        text="📺 OLED TV Driver",
        bg=BG,
        fg=TEXT,
        font=("Helvetica", 18, "bold")
    ).pack(pady=10)

    # ---------------- PORT CARD ----------------
    port_card = card(root)

    tk.Label(port_card, text="Serial Port", bg=CARD, fg=TEXT).pack(anchor="w")

    port_var = tk.StringVar()
    port_menu = ttk.Combobox(port_card, textvariable=port_var, values=get_ports())
    port_menu.pack(fill="x", pady=5)

    tk.Button(
        port_card,
        text="Refresh Ports",
        command=lambda: refresh_ports(port_menu),
        bg=ACCENT,
        fg="black"
    ).pack(fill="x")

    # ---------------- CAPTURE CARD ----------------
    cap_card = card(root)

    tk.Label(cap_card, text="Capture Area", bg=CARD, fg=TEXT).pack(anchor="w")

    def slider(label, default):
        tk.Label(cap_card, text=label, bg=CARD, fg=TEXT).pack(anchor="w")
        s = tk.Scale(
            cap_card,
            from_=0,
            to=1200,
            orient="horizontal",
            bg=CARD,
            fg=TEXT,
            highlightthickness=0
        )
        s.set(default)
        s.pack(fill="x")
        return s

    top = slider("Top", 250)
    left = slider("Left", 500)
    width = slider("Width", 600)
    height = slider("Height", 360)

    # ---------------- CONTROL CARD ----------------
    ctrl = card(root)

    tk.Button(
        ctrl,
        text="▶ Start",
        bg=GOOD,
        fg="black",
        command=lambda: start_stream(port_var, top, left, width, height, status_label)
    ).pack(fill="x", pady=2)

    tk.Button(
        ctrl,
        text="■ Stop",
        bg=BAD,
        fg="white",
        command=lambda: stop_stream(status_label)
    ).pack(fill="x", pady=2)

    # ---------------- STATUS ----------------
    status_label = tk.Label(
        root,
        text="Idle",
        bg=BG,
        fg=TEXT,
        font=("Helvetica", 12)
    )
    status_label.pack(pady=10)

    root.mainloop()
