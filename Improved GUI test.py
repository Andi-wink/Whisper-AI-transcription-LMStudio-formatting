import tkinter as tk
from tkinter import ttk

class ModernGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Speech Recorder")
        self.geometry("400x500")
        self.configure(bg="#f0f0f0")

        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.style.configure("TButton",
                             padding=10,
                             font=("Helvetica", 12),
                             background="#4a4a4a",
                             foreground="white")

        self.style.map("TButton",
                       background=[('active', '#666666')])

        self.style.configure("TLabel",
                             font=("Helvetica", 18, "bold"),
                             background="#f0f0f0",
                             foreground="#333333")

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="20 20 20 20", style="Main.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.style.configure("Main.TFrame", background="#f0f0f0")

        title_label = ttk.Label(main_frame, text="Speech Recorder", style="TLabel")
        title_label.pack(pady=(0, 20))

        self.record_button = ttk.Button(main_frame, text="Record")
        self.record_button.pack(fill=tk.X, pady=10)

        self.command_button = ttk.Button(main_frame, text="Command")
        self.command_button.pack(fill=tk.X, pady=10)

        self.spaceholder_button = ttk.Button(main_frame, text="Spaceholder")
        self.spaceholder_button.pack(fill=tk.X, pady=10)

        status_frame = ttk.Frame(main_frame, style="Status.TFrame")
        status_frame.pack(fill=tk.X, pady=(20, 0))

        self.style.configure("Status.TFrame", background="#e0e0e0")

        self.status_label = ttk.Label(status_frame, text="Ready", background="#e0e0e0", font=("Helvetica", 10))
        self.status_label.pack(pady=5)

if __name__ == "__main__":
    root = ModernGUI()
    root.mainloop()