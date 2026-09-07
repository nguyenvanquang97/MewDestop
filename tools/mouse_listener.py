#!/usr/bin/env python3
"""
Global Mouse Wheel Click (Middle Click) Listener for macOS.
Monitors the middle mouse button (scroll wheel click / kCGMouseButtonCenter)
and notifies Godot via local UDP socket (127.0.0.1:45455).
Godot then reads DisplayServer.mouse_get_position() directly for 100% accurate native pixel coordinates.
"""

import sys
import time
import socket
import signal
import ctypes

def main():
    try:
        cg = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')
    except Exception as e:
        sys.stderr.write(f"[mouse_listener] Failed to load macOS frameworks: {e}\n")
        sys.exit(1)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    target_addr = ('127.0.0.1', 45455)

    running = True

    def handle_signal(sig, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    prev_pressed = False
    print("[mouse_listener] macOS Global middle-click listener active.", flush=True)

    while running:
        # kCGEventSourceStateCombinedSessionState = 0, kCGMouseButtonCenter = 2
        btn_state = cg.CGEventSourceButtonState(0, 2)
        is_pressed = (btn_state != 0)

        if is_pressed and not prev_pressed:
            # Triggered on button down
            try:
                sock.sendto(b"click", target_addr)
            except Exception:
                pass

        prev_pressed = is_pressed
        time.sleep(0.016) # ~60 Hz polling, 0% CPU

    sock.close()
    print("[mouse_listener] Terminated cleanly.", flush=True)

if __name__ == '__main__':
    main()
