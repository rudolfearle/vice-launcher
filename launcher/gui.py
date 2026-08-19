import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import config as cfgmod
from . import scanner
from . import vice


class LauncherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VICE Game Launcher")
        self.geometry("640x480")

        self.cfg = cfgmod.load_config()
        self.all_games = []
        self.filtered_games = []

        self._build_menu()
        self._build_widgets()
        self._refresh_library()

    # ---------- UI construction ----------

    def _build_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Set Games Folder...", command=self._set_games_dir)
        file_menu.add_command(label="Set VICE Binary Folder...", command=self._set_vice_dir)
        self.flatpak_var = tk.BooleanVar(value=self.cfg.get("vice_flatpak", False))
        file_menu.add_checkbutton(
            label="Use Flatpak VICE (net.sf.VICE)",
            variable=self.flatpak_var,
            command=self._toggle_flatpak,
        )
        file_menu.add_separator()
        file_menu.add_command(label="Rescan Library", command=self._refresh_library)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        self.config(menu=menubar)

    def _build_widgets(self):
        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", padx=8, pady=8)

        ttk.Label(search_frame, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._apply_filter())
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side="left", fill="x", expand=True, padx=6)

        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.listbox = tk.Listbox(list_frame, activestyle="dotbox")
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind("<Double-Button-1>", lambda _e: self._launch_selected())
        self.listbox.bind("<Return>", lambda _e: self._launch_selected())

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(button_frame, text="Launch", command=self._launch_selected).pack(side="right")

        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self, textvariable=self.status_var, anchor="w", relief="sunken")
        status_bar.pack(fill="x", side="bottom")

    # ---------- Actions ----------

    def _set_games_dir(self):
        chosen = filedialog.askdirectory(title="Select games folder")
        if chosen:
            self.cfg["games_dir"] = chosen
            cfgmod.save_config(self.cfg)
            self._refresh_library()

    def _set_vice_dir(self):
        chosen = filedialog.askdirectory(
            title="Select folder containing VICE binaries (e.g. x64sc)"
        )
        if chosen:
            self.cfg["vice_bin_dir"] = chosen
            cfgmod.save_config(self.cfg)
            self.status_var.set(f"VICE binary folder set to {chosen}")

    def _toggle_flatpak(self):
        self.cfg["vice_flatpak"] = self.flatpak_var.get()
        cfgmod.save_config(self.cfg)
        state = "enabled" if self.cfg["vice_flatpak"] else "disabled"
        self.status_var.set(f"Flatpak VICE mode {state}")

    def _refresh_library(self):
        games_dir = self.cfg.get("games_dir")
        if not games_dir:
            self.status_var.set("No games folder set. Use File > Set Games Folder.")
            self.all_games = []
        else:
            self.all_games = scanner.scan_games(games_dir)
            self.status_var.set(f"Found {len(self.all_games)} game(s) in {games_dir}")
        self._apply_filter()

    def _apply_filter(self):
        query = self.search_var.get().lower().strip()
        self.listbox.delete(0, tk.END)
        self.filtered_games = (
            [g for g in self.all_games if query in g["title"].lower()]
            if query else list(self.all_games)
        )
        for g in self.filtered_games:
            self.listbox.insert(tk.END, g["title"])

    def _launch_selected(self):
        selection = self.listbox.curselection()
        if not selection:
            return
        game = self.filtered_games[selection[0]]
        try:
            vice.launch_game(self.cfg, game)
            self.status_var.set(f"Launched: {game['title']}")
        except FileNotFoundError as e:
            messagebox.showerror("Could not launch", str(e))
        except Exception as e:
            messagebox.showerror("Error launching game", str(e))
