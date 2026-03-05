import tkinter as tk

THEME = {
    "bg": "#2C3E50",
    "panel": "#34495E",
    "text": "#ECF0F1",
    "muted": "#95A5A6",
    "accent": "#3498DB",
}


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _=None):
        if self.tip:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.tip = tk.Toplevel(self.widget)
        self.tip.overrideredirect(True)
        self.tip.configure(bg=THEME["panel"])
        lbl = tk.Label(
            self.tip,
            text=self.text,
            bg=THEME["panel"],
            fg=THEME["text"],
            padx=10,
            pady=8,
            justify="left",
            wraplength=340,
        )
        lbl.pack()
        self.tip.geometry(f"+{x}+{y}")

    def hide(self, _=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None
