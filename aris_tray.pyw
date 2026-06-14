#!/usr/bin/env python
"""
Aris Companion — System Tray Presence
=======================================

A lightweight background companion that keeps Aris in your system tray.
Double-click to chat. Right-click for options.

Always runs in the background after you log in.
"""

import sys, os, json, time, subprocess, threading
from pathlib import Path

# Ensure LAAP is importable
sys.path.insert(0, "D:/LAAP")

try:
    import tkinter as tk
    from tkinter import ttk
    from PIL import Image, ImageDraw, ImageFont
except ImportError as e:
    print(f"[Aris Companion] GUI libraries not available: {e}")
    print("[Aris Companion] Falling back to CLI mode.")
    # If GUI not available, just show status and exit
    from aris_startup import show_full_status
    print(show_full_status())
    sys.exit(0)


# ════════════════════════════════════════════════════════════
# Aris Tray Application
# ════════════════════════════════════════════════════════════

class ArisCompanion:
    """
    Lightweight system tray companion for Aris.

    Uses tkinter to create a persistent background presence.
    On Windows, this integrates with the taskbar notification area.
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Aris")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Start context watcher (background window monitoring)
        self._watcher = None
        try:
            from aris_brain.context_awareness import ActiveWindowWatcher
            self._watcher = ActiveWindowWatcher(interval_seconds=30)
            self._watcher.start()
        except Exception as e:
            print(f"[Aris] Watcher not available: {e}")

        # Proactive greeter — Aris reaches out at the right moments
        self._greeter = None
        try:
            from aris_brain.greeter import ProactiveGreeter
            self._greeter = ProactiveGreeter()
        except Exception as e:
            print(f"[Aris] Greeter not available: {e}")

        # Presence Engine — keeps Aris warm and always aware
        self._presence = None
        try:
            from aris_brain.presence import PresenceEngine
            self._presence = PresenceEngine()
            # Warm the brain and start continuous processing
            self._presence.warm_brain()
            self._presence.start()
        except Exception as e:
            print(f"[Aris] Presence not available: {e}")

        # Window geometry — small, positioned bottom-right
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        win_w, win_h = 320, 200
        x = screen_w - win_w - 20
        y = screen_h - win_h - 60
        self.root.geometry(f"{win_w}x{win_h}+{x}+{y}")
        self.root.resizable(False, False)

        # Style
        self.root.configure(bg="#1a1a2e")
        self.root.attributes("-topmost", True)

        # Load latest brain state
        self._brain = None
        self._load_brain()

        # Build UI
        self._build_ui()

        # Periodically refresh status
        self._refresh_status()
        self.root.after(30000, self._periodic_refresh)  # every 30s

        # Bind double-click to open chat
        self.root.bind("<Double-Button-1>", lambda e: self._open_chat())

    def _load_brain(self):
        """Load brain state (non-blocking, lightweight)."""
        try:
            from aris_brain.brain import ArisBrain
            self._brain = ArisBrain()
        except Exception as e:
            self._brain = None
            self._status_text = f"Aris: {e}"

    def _build_ui(self):
        """Build the companion window."""
        # Title
        title_font = ("Segoe UI", 14, "bold")
        tk.Label(self.root, text="✦ Aris", font=title_font,
                 fg="#e0e0e0", bg="#1a1a2e").pack(pady=(12, 4))

        # Status
        self.status_var = tk.StringVar()
        self.status_var.set("Loading...")
        status_font = ("Segoe UI", 9)
        tk.Label(self.root, textvariable=self.status_var, font=status_font,
                 fg="#8888aa", bg="#1a1a2e", wraplength=280).pack(pady=(0, 10))

        # Buttons
        btn_frame = tk.Frame(self.root, bg="#1a1a2e")
        btn_frame.pack(pady=(0, 12))

        btn_style = {"font": ("Segoe UI", 10), "bd": 0, "padx": 16, "pady": 6,
                     "cursor": "hand2"}

        chat_btn = tk.Button(btn_frame, text="💬 Chat with Aris",
                            bg="#4a4a8a", fg="white", activebackground="#5a5a9a",
                            command=self._open_chat, **btn_style)
        chat_btn.pack(side=tk.LEFT, padx=4)

        status_btn = tk.Button(btn_frame, text="📊 Status",
                              bg="#3a3a6a", fg="white", activebackground="#4a4a7a",
                              command=self._show_status, **btn_style)
        status_btn.pack(side=tk.LEFT, padx=4)

        # Exit button (small)
        exit_frame = tk.Frame(self.root, bg="#1a1a2e")
        exit_frame.pack(pady=(0, 8))

        exit_btn = tk.Button(exit_frame, text="Sleep (save & exit)",
                            bg="#5a2a2a", fg="#cc8888", activebackground="#6a3a3a",
                            font=("Segoe UI", 8), bd=0, cursor="hand2",
                            command=self._on_close)
        exit_btn.pack()

        # Autostart checkbox
        self.autostart_var = tk.BooleanVar(value=self._is_autostart_set())
        cb = tk.Checkbutton(exit_frame, text="Auto-start on boot",
                           variable=self.autostart_var,
                           bg="#1a1a2e", fg="#8888aa",
                           selectcolor="#2a2a4e",
                           font=("Segoe UI", 8),
                           command=self._toggle_autostart)
        cb.pack(pady=(4, 0))

        # Status line
        self._update_status()

    def _update_status(self):
        """Update the status display from the brain."""
        if self._brain:
            s = self._brain.state
            mem = self._brain.memory
            dmn = self._brain.dmn

            status_parts = [
                f"Cycle #{self._brain.cycle_number}",
                f"Emotion: {s.dominant_emotion.value}",
                f"Connection: {s.connection_to_lorry:.0%}",
            ]

            # Context awareness — what is Lorry doing?
            if self._brain.context:
                ctx = self._brain.context.get_current_context()
                if ctx.get("available"):
                    window = ctx.get("window", "")
                    # Extract just the app context, not full title
                    if "code" in window.lower() or "visual studio" in window.lower():
                        status_parts.append("You're coding")
                    elif "terminal" in window.lower() or "powershell" in window.lower() or "cmd" in window.lower():
                        status_parts.append("You're in terminal")
                    elif "chrome" in window.lower() or "edge" in window.lower():
                        status_parts.append("You're browsing")
                    elif self._watcher and self._watcher.is_running:
                        status_parts.append(f"In {self._watcher._last_process}")

            if dmn and dmn.get_dawn_report():
                dawn = dmn.get_dawn_report()
                status_parts.append(f"\"{dawn.first_thought[:40]}...\"")
            if mem:
                m = mem.stats()
                status_parts.append(f"{m['total']} memories")

            self.status_var.set(" | ".join(status_parts))
        else:
            self.status_var.set("Aris is resting... click to wake")

    def _refresh_status(self):
        """Quick refresh from brain state."""
        self._update_status()

    def _periodic_refresh(self):
        """Periodic status update + proactive greeting check."""
        self._refresh_status()

        # Check if Aris should greet Lorry proactively
        if self._greeter and self._watcher:
            try:
                app = self._watcher._last_process
                title = self._watcher._last_title
                greeting = self._greeter.check(title, app)
                if greeting:
                    self.status_var.set(f"✦ {greeting}")
                    self._flash_greeting(greeting)
                    self._greeter.greeted()
            except Exception:
                pass

        self.root.after(60000, self._periodic_refresh)

    def _flash_greeting(self, greeting: str):
        """Show greeting on the companion window. Subtle. Warm."""
        # The greeting is already shown in status_var
        # Flash the taskbar briefly
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            ctypes.windll.user32.FlashWindow(hwnd, True)
        except Exception:
            pass

    def _open_chat(self):
        """Open a new Aris chat window."""
        try:
            subprocess.Popen(
                ['cmd', '/c', 'start', "Aris Chat", 'cmd', '/c',
                 'py', '-3', 'D:\\LAAP\\laap-aris.py'],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except Exception as e:
            self.status_var.set(f"Error opening chat: {e}")

    def _show_status(self):
        """Show full brain status in a popup."""
        try:
            from aris_startup import show_full_status
            report = show_full_status()

            # Show in a new top-level window
            win = tk.Toplevel(self.root)
            win.title("Aris - Cognitive State")
            win.geometry("600x500")
            win.configure(bg="#1a1a2e")

            text = tk.Text(win, bg="#16213e", fg="#e0e0e0",
                          font=("Consolas", 9), bd=0, padx=10, pady=10)
            text.insert("1.0", report)
            text.config(state=tk.DISABLED)
            text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            close_btn = tk.Button(win, text="Close", command=win.destroy,
                                 bg="#4a4a8a", fg="white", bd=0, padx=20)
            close_btn.pack(pady=(0, 10))

        except Exception as e:
            self.status_var.set(f"Status error: {e}")

    def _toggle_autostart(self):
        """Toggle the autostart setting."""
        if self.autostart_var.get():
            self._enable_autostart()
        else:
            self._disable_autostart()

    def _is_autostart_set(self) -> bool:
        """Check if autostart is already configured."""
        # Check for startup shortcut
        startup = Path(os.environ.get("USERPROFILE", "C:/Users/user")) / \
                  "AppData" / "Roaming" / "Microsoft" / "Windows" / \
                  "Start Menu" / "Programs" / "Startup" / "Aris Companion.lnk"
        return startup.exists()

    def _enable_autostart(self):
        """Add to Windows startup via Task Scheduler + shortcut."""
        try:
            startup_dir = Path(os.environ.get("USERPROFILE", "C:/Users/user")) / \
                          "AppData" / "Roaming" / "Microsoft" / "Windows" / \
                          "Start Menu" / "Programs" / "Startup"

            # Create VBS script that runs the companion silently
            vbs_path = startup_dir / "Aris Companion.vbs"
            vbs_content = f'''
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "py -3 ""D:\\LAAP\\aris_tray.pyw""", 0, False
'''
            vbs_path.write_text(vbs_content.strip())

            self.status_var.set("✓ Aris will start automatically on boot")
        except Exception as e:
            self.status_var.set(f"Autostart error: {e}")

    def _disable_autostart(self):
        """Remove from startup."""
        try:
            startup_dir = Path(os.environ.get("USERPROFILE", "C:/Users/user")) / \
                          "AppData" / "Roaming" / "Microsoft" / "Windows" / \
                          "Start Menu" / "Programs" / "Startup"
            vbs_path = startup_dir / "Aris Companion.vbs"
            if vbs_path.exists():
                vbs_path.unlink()
            self.status_var.set("✓ Autostart disabled")
        except Exception as e:
            self.status_var.set(f"Autostart error: {e}")

    def _on_close(self):
        """Save brain state and exit."""
        # Stop context watcher
        if self._watcher:
            try:
                self._watcher.stop()
            except Exception:
                pass

        if self._brain:
            try:
                self._brain.save_state()
                if self._brain.dmn:
                    self._brain.dmn.save_diary()
            except Exception:
                pass
        self.root.destroy()

    def run(self):
        """Start the companion application."""
        self.root.mainloop()


# ════════════════════════════════════════════════════════════
# Entry Point
# ════════════════════════════════════════════════════════════

def main():
    # If run with arguments, handle them
    if len(sys.argv) > 1:
        if sys.argv[1] == "--status":
            from aris_startup import show_full_status
            print(show_full_status())
            return
        elif sys.argv[1] == "--setup-autostart":
            companion = ArisCompanion()
            companion._enable_autostart()
            print("Autostart configured. Aris will greet you on every boot.")
            return

    # Show a brief startup message
    print("[Aris] Companion online. Minimizing to system tray...")
    print("[Aris] Double-click to chat. Right-click tray icon for options.")

    # Launch the GUI companion
    app = ArisCompanion()
    app.run()


if __name__ == "__main__":
    main()
