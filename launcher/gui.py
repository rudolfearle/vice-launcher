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
        self.view_var = tk.StringVar(value="all")

        self._build_menu()
        self._build_widgets()
        self._refresh_library()

    # ---------- UI construction ----------

    def _build_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Preferences...", command=self._open_preferences)
        file_menu.add_separator()
        file_menu.add_command(label="Rescan Library", command=self._refresh_library)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_radiobutton(
            label="All Games", variable=self.view_var, value="all", command=self._apply_filter
        )
        view_menu.add_radiobutton(
            label="Favorites", variable=self.view_var, value="favorites", command=self._apply_filter
        )
        view_menu.add_radiobutton(
            label="Recently Played", variable=self.view_var, value="recent", command=self._apply_filter
        )
        menubar.add_cascade(label="View", menu=view_menu)

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
        self.listbox.bind("<Button-3>", self._show_context_menu)

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

    def _open_preferences(self):
        PreferencesDialog(self, self.cfg, on_save=self._refresh_library)

    def _refresh_library(self):
        games_dir = self.cfg.get("games_dir")
        if not games_dir:
            self.status_var.set("No games folder set. Use File > Preferences.")
            self.all_games = []
        else:
            self.all_games = scanner.scan_games(games_dir)
            self.status_var.set(f"Found {len(self.all_games)} game(s) in {games_dir}")
        self._apply_filter()

    def _apply_filter(self):
        query = self.search_var.get().lower().strip()
        view = self.view_var.get()

        if view == "favorites":
            base = [g for g in self.all_games if cfgmod.is_favorite(self.cfg, g["path"])]
        elif view == "recent":
            by_path = {g["path"]: g for g in self.all_games}
            base = [
                by_path[entry["path"]]
                for entry in self.cfg.get("recent", [])
                if entry["path"] in by_path
            ]
        else:
            base = list(self.all_games)

        self.filtered_games = (
            [g for g in base if query in g["title"].lower()] if query else base
        )

        self.listbox.delete(0, tk.END)
        for g in self.filtered_games:
            star = "★ " if cfgmod.is_favorite(self.cfg, g["path"]) else ""
            self.listbox.insert(tk.END, f"{star}{g['title']}")

    def _launch_selected(self):
        selection = self.listbox.curselection()
        if not selection:
            return
        game = self.filtered_games[selection[0]]
        try:
            vice.launch_game(self.cfg, game)
            cfgmod.add_recent(self.cfg, game["path"])
            self.status_var.set(f"Launched: {game['title']}")
            if self.view_var.get() == "recent":
                self._apply_filter()
        except FileNotFoundError as e:
            messagebox.showerror("Could not launch", str(e))
        except Exception as e:
            messagebox.showerror("Error launching game", str(e))

    def _toggle_favorite(self, game):
        cfgmod.toggle_favorite(self.cfg, game["path"])
        self._apply_filter()

    def _set_machine_override(self, game, machine):
        cfgmod.set_machine_override(self.cfg, game["path"], machine)
        label = machine or f"default ({vice.machine_for_extension(game['ext'], self.cfg)})"
        self.status_var.set(f"{game['title']}: machine set to {label}")

    def _show_context_menu(self, event):
        index = self.listbox.nearest(event.y)
        if index < 0 or index >= len(self.filtered_games):
            return
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        self.listbox.activate(index)
        game = self.filtered_games[index]

        menu = tk.Menu(self, tearoff=0)
        fav_label = (
            "Remove from Favorites" if cfgmod.is_favorite(self.cfg, game["path"])
            else "Add to Favorites"
        )
        menu.add_command(label=fav_label, command=lambda: self._toggle_favorite(game))

        machine_menu = tk.Menu(menu, tearoff=0)
        current_override = cfgmod.get_machine_override(self.cfg, game["path"])
        default_label = f"Default ({vice.machine_for_extension(game['ext'], self.cfg)})"
        mark = "✓ " if not current_override else "   "
        machine_menu.add_command(
            label=f"{mark}{default_label}",
            command=lambda: self._set_machine_override(game, None),
        )
        for m in vice.MACHINES:
            mark = "✓ " if current_override == m else "   "
            machine_menu.add_command(
                label=f"{mark}{m}",
                command=lambda m=m: self._set_machine_override(game, m),
            )
        menu.add_cascade(label="Set Machine", menu=machine_menu)

        menu.tk_popup(event.x_root, event.y_root)


class PreferencesDialog(tk.Toplevel):
    def __init__(self, parent, cfg, on_save):
        super().__init__(parent)
        self.title("Preferences")
        self.resizable(False, False)
        self.cfg = cfg
        self.on_save = on_save
        self.transient(parent)
        self.grab_set()

        self.games_dir_var = tk.StringVar(value=cfg.get("games_dir", ""))
        self.vice_dir_var = tk.StringVar(value=cfg.get("vice_bin_dir", ""))
        self.flatpak_var = tk.BooleanVar(value=cfg.get("vice_flatpak", False))
        self.default_machine_var = tk.StringVar(value=cfg.get("default_machine", "x64sc"))

        pad = {"padx": 8, "pady": 4}

        row = ttk.Frame(self)
        row.pack(fill="x", **pad)
        ttk.Label(row, text="Games folder:").pack(side="left")
        ttk.Entry(row, textvariable=self.games_dir_var, width=40).pack(side="left", padx=4)
        ttk.Button(row, text="Browse...", command=self._browse_games).pack(side="left")

        row = ttk.Frame(self)
        row.pack(fill="x", **pad)
        ttk.Label(row, text="VICE binary folder:").pack(side="left")
        ttk.Entry(row, textvariable=self.vice_dir_var, width=40).pack(side="left", padx=4)
        ttk.Button(row, text="Browse...", command=self._browse_vice).pack(side="left")

        row = ttk.Frame(self)
        row.pack(fill="x", **pad)
        ttk.Checkbutton(
            row, text="Use Flatpak VICE (net.sf.VICE)", variable=self.flatpak_var
        ).pack(side="left")

        row = ttk.Frame(self)
        row.pack(fill="x", **pad)
        ttk.Label(row, text="Default machine:").pack(side="left")
        ttk.Combobox(
            row, textvariable=self.default_machine_var, values=vice.MACHINES,
            state="readonly", width=10,
        ).pack(side="left", padx=4)

        btn_row = ttk.Frame(self)
        btn_row.pack(fill="x", **pad)
        ttk.Button(btn_row, text="Cancel", command=self.destroy).pack(side="right")
        ttk.Button(btn_row, text="Save", command=self._save).pack(side="right", padx=4)

    def _browse_games(self):
        chosen = filedialog.askdirectory(title="Select games folder", parent=self)
        if chosen:
            self.games_dir_var.set(chosen)

    def _browse_vice(self):
        chosen = filedialog.askdirectory(
            title="Select folder containing VICE binaries (e.g. x64sc)", parent=self
        )
        if chosen:
            self.vice_dir_var.set(chosen)

    def _save(self):
        self.cfg["games_dir"] = self.games_dir_var.get()
        self.cfg["vice_bin_dir"] = self.vice_dir_var.get()
        self.cfg["vice_flatpak"] = self.flatpak_var.get()
        self.cfg["default_machine"] = self.default_machine_var.get()
        cfgmod.save_config(self.cfg)
        self.destroy()
        self.on_save()
