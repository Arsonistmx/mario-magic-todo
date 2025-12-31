import customtkinter as ctk
import tkinter as tk
from datetime import datetime, timedelta
from database import TodoDatabase
from tkinter import messagebox
import random
import time
import logging

# --- 1. LOGGING SETUP ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MarioSys")

# --- THEME CONFIGURATION ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

# HACKER THEME PALETTE
THEME = {
    "BG": "#000000",
    "FG": "#00FF41",
    "DIM": "#008F11",
    "ACCENT": "#111111",
    "BORDER": "#00FF41",
    "FONT_MAIN": ("Consolas", 14, "bold"),
    "FONT_MONO": ("Consolas", 12),
    "FONT_HEADER": ("Courier New", 20, "bold"),
    "FONT_SECTION_ICON": ("Consolas", 32, "bold"),
    "FONT_SECTION_TEXT": ("Consolas", 18, "bold")
}

# --- LAYOUT CONFIGURATION ---
BORDER_PAD = 60


# --- BACKGROUND COMPONENT: MATRIX RAIN ---
class MatrixRainLite(ctk.CTkCanvas):
    def __init__(self, master, width, height, pad_size, **kwargs):
        super().__init__(master, width=width, height=height, **kwargs)
        self.configure(bg="black", highlightthickness=0)
        self.width = width
        self.height = height
        self.pad_size = pad_size
        self.font_size = 14
        self.font_family = "Consolas"
        self.col_spacing = int(self.font_size * 15)
        self.cols = int(self.width // self.col_spacing)
        self.drops = []
        self.chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ@#$%^&*"
        self._init_drops()
        self.running = True
        self.animate()
        self.bind("<Configure>", self._on_resize)

    def _init_drops(self):
        self.drops = []
        for i in range(self.cols):
            stream_len = random.randint(3, 8)
            stream_text = "\n".join([random.choice(self.chars) for _ in range(stream_len)])
            x = i * self.col_spacing
            y = random.randint(-self.height, 0)
            speed = random.randint(3, 10)
            tag = self.create_text(x, y, text=stream_text, fill=THEME["DIM"], anchor="nw",
                                   font=(self.font_family, self.font_size))
            self.drops.append([tag, speed, y, x])

    def _on_resize(self, event):
        self.width = event.width
        self.height = event.height
        if abs(len(self.drops) - (self.width // self.col_spacing)) > 5:
            self.delete("all")
            self.cols = int(self.width // self.col_spacing)
            self._init_drops()

    def animate(self):
        if not self.running: return
        app_left = self.pad_size
        app_right = self.width - self.pad_size
        app_top = self.pad_size
        app_bottom = self.height - self.pad_size

        for drop in self.drops:
            tag_id, speed, current_y, col_x = drop
            is_middle_col = (app_left < col_x < app_right)
            if is_middle_col:
                next_y = current_y + speed
                if current_y < app_top and next_y >= app_top:
                    jump_dist = app_bottom - current_y
                    self.move(tag_id, 0, jump_dist)
                    drop[2] = app_bottom
                elif app_top <= current_y < app_bottom:
                    jump_dist = app_bottom - current_y
                    self.move(tag_id, 0, jump_dist)
                    drop[2] = app_bottom
                else:
                    self.move(tag_id, 0, speed)
                    drop[2] += speed
            else:
                self.move(tag_id, 0, speed)
                drop[2] += speed

            if drop[2] > self.height:
                reset_y = -random.randint(50, 200)
                delta_y = reset_y - drop[2]
                self.move(tag_id, 0, delta_y)
                drop[2] = reset_y
        self.after(200, self.animate)


# --- HELPER FUNCTIONS ---
def format_seconds(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def format_short_date(date_str):
    if not date_str: return ""
    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    return dt.strftime("%y-%m-%d %H:%M")


# --- DIALOGS ---
class TaskDialog(ctk.CTkToplevel):
    def __init__(self, parent, callback, title="NEW_TASK", initial_name="", initial_eta="",
                 include_category=True):
        super().__init__(parent)
        self.callback = callback
        self.include_category = include_category
        self.title(title)
        height = 350 if include_category else 280
        self.geometry(f"450x{height}")
        self.configure(fg_color="black")
        self.transient(parent)
        self.grab_set()

        self.main = ctk.CTkFrame(self, fg_color="black", border_width=2, border_color=THEME["FG"], corner_radius=0)
        self.main.pack(fill="both", expand=True, padx=2, pady=2)
        ctk.CTkLabel(self.main, text=f"// {title}", font=THEME["FONT_MAIN"], text_color=THEME["FG"], anchor="w").pack(
            pady=(20, 10), padx=20, fill="x")

        self.name_entry = self.create_input(self.main, "Task Identifier...", initial_name)
        self.eta_entry = self.create_input(self.main, "Time Constraint (Optional)...", initial_eta)

        if self.include_category:
            ctk.CTkLabel(self.main, text="CLASS:", anchor="w", text_color=THEME["DIM"], font=THEME["FONT_MONO"]).pack(
                pady=(10, 5), padx=20, fill="x")
            self.cat_switch = ctk.CTkSegmentedButton(self.main, values=["DANTE_QUARTERS", "Work"],
                                                     font=THEME["FONT_MONO"],
                                                     fg_color="black", selected_color=THEME["DIM"],
                                                     selected_hover_color=THEME["FG"],
                                                     unselected_color="black", unselected_hover_color="#111",
                                                     corner_radius=0, border_width=1)
            self.cat_switch.set("Work")
            self.cat_switch.pack(pady=5, padx=20, fill="x")

        ctk.CTkButton(self.main, text="[ INITIALIZE ]", height=40, font=THEME["FONT_MAIN"],
                      fg_color="transparent", border_color=THEME["FG"], border_width=1, text_color=THEME["FG"],
                      hover_color="#111", corner_radius=0, command=self.save_task).pack(pady=20, padx=20, fill="x")

    def create_input(self, parent, placeholder, value):
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, font=THEME["FONT_MONO"],
                             fg_color=THEME["ACCENT"], border_color=THEME["DIM"], border_width=1, corner_radius=0,
                             text_color=THEME["FG"], placeholder_text_color=THEME["DIM"])
        entry.pack(pady=5, padx=20, fill="x")
        if value: entry.insert(0, value)
        return entry

    def save_task(self):
        name = self.name_entry.get()
        eta = self.eta_entry.get()
        if self.include_category:
            raw_cat = self.cat_switch.get()
            cat = "Personal" if raw_cat == "DANTE_QUARTERS" else "Work"
        else:
            cat = "Work"

        if name:
            self.callback(name, eta, cat)
            self.destroy()


class NotesDialog(ctk.CTkToplevel):
    def __init__(self, parent, task_name, initial_notes, on_save):
        super().__init__(parent)
        self.title("DATA_LOG")
        self.geometry("500x400")
        self.configure(fg_color="black")
        self.transient(parent)
        self.grab_set()
        self.on_save = on_save

        self.main = ctk.CTkFrame(self, fg_color="black", border_width=2, border_color=THEME["FG"], corner_radius=0)
        self.main.pack(fill="both", expand=True, padx=2, pady=2)

        ctk.CTkLabel(self.main, text=f"LOG: {task_name}", font=THEME["FONT_MAIN"], text_color=THEME["FG"],
                     anchor="w").pack(
            pady=(10, 5), padx=10, fill="x")

        self.textbox = ctk.CTkTextbox(self.main, font=THEME["FONT_MONO"], fg_color="#111", text_color="white",
                                      corner_radius=0)
        self.textbox.pack(fill="both", expand=True, padx=10, pady=5)
        self.textbox.insert("1.0", initial_notes)

        ctk.CTkButton(self.main, text="[ SAVE_DATA ]", font=THEME["FONT_MAIN"],
                      fg_color="transparent", border_color=THEME["FG"], border_width=1, text_color=THEME["FG"],
                      hover_color="#222", corner_radius=0, command=self.save).pack(pady=10, padx=10, fill="x")

    def save(self):
        txt = self.textbox.get("1.0", "end-1c")
        self.on_save(txt)
        self.destroy()


class DateFilterDialog(ctk.CTkToplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("FILTER_DATE")
        self.geometry("300x180")
        self.configure(fg_color="black")
        self.transient(parent)
        self.grab_set()
        self.callback = callback

        self.main = ctk.CTkFrame(self, fg_color="black", border_width=2, border_color=THEME["FG"], corner_radius=0)
        self.main.pack(fill="both", expand=True, padx=2, pady=2)

        ctk.CTkLabel(self.main, text="ENTER START DATE:", font=THEME["FONT_MONO"], text_color=THEME["DIM"]).pack(
            pady=(20, 5))

        self.entry = ctk.CTkEntry(self.main, placeholder_text="YYYY-MM-DD", font=THEME["FONT_MONO"],
                                  fg_color="#111", border_color=THEME["DIM"], text_color=THEME["FG"])
        self.entry.pack(pady=5, padx=20, fill="x")

        ctk.CTkButton(self.main, text="[ APPLY FILTER ]", font=THEME["FONT_MAIN"],
                      fg_color="transparent", border_color=THEME["FG"], border_width=1, text_color=THEME["FG"],
                      hover_color="#222", corner_radius=0, command=self.apply).pack(pady=20, padx=20, fill="x")

    def apply(self):
        date_str = self.entry.get()
        try:
            # Validate format
            datetime.strptime(date_str, "%Y-%m-%d")
            # Append time to make it a full timestamp for comparison
            full_date_str = f"{date_str} 00:00:00"
            self.callback(full_date_str)
            self.destroy()
        except ValueError:
            tk.messagebox.showerror("Error", "Invalid Format. Use YYYY-MM-DD")


class ActionDialog(ctk.CTkToplevel):
    def __init__(self, parent, task_name, on_edit, on_delete, on_archive, on_ai_report):
        super().__init__(parent)
        self.title("TASK_OPERATIONS")
        self.geometry("300x280")
        self.configure(fg_color="black")
        self.transient(parent)
        self.grab_set()

        self.main = ctk.CTkFrame(self, fg_color="black", border_width=2, border_color=THEME["FG"], corner_radius=0)
        self.main.pack(fill="both", expand=True, padx=2, pady=2)
        ctk.CTkLabel(self.main, text=f"OP: {task_name[:15]}...", font=("Consolas", 12), text_color=THEME["DIM"]).pack(
            pady=(15, 10))

        def action_btn(txt, cmd, color=THEME["FG"]):
            ctk.CTkButton(self.main, text=txt, font=THEME["FONT_MAIN"],
                          fg_color="transparent", border_color=color, border_width=1,
                          text_color=color, hover_color="#222", corner_radius=0,
                          command=lambda: [cmd(), self.destroy()]).pack(pady=5, padx=20, fill="x")

        action_btn("[ GENERATE AI REPORT ]", on_ai_report, color="#f1c40f")
        action_btn("[ EDIT PROPERTIES ]", on_edit)
        # Archive Button Removed
        action_btn("[ DELETE ]", on_delete, color="#ff4444")
        ctk.CTkButton(self.main, text="[ CANCEL ]", font=("Consolas", 10), text_color="#666",
                      fg_color="transparent", hover_color="#111", command=self.destroy).pack(pady=(10, 0))


# --- TASK WIDGET ---
class TaskWidget(ctk.CTkFrame):
    def __init__(self, parent, task_data, db, reload_callback, toggle_fold_callback, app_reference, is_folded=False,
                 depth=0,
                 is_history=False, has_children=False):
        super().__init__(parent, fg_color="transparent", border_width=0, corner_radius=0)
        self.pack(fill="x", pady=2, padx=(depth * 25 + 5, 5))
        self.inner = ctk.CTkFrame(self, fg_color="transparent", border_color=THEME["DIM"], border_width=1,
                                  corner_radius=0)
        self.inner.pack(fill="both", expand=True)

        self.db = db
        self.task_data = task_data
        self.reload_callback = reload_callback
        self.toggle_fold_callback = toggle_fold_callback
        self.app_reference = app_reference
        self.task_id = task_data['id']
        self.is_history = is_history
        self.status = task_data['status']

        # Indent Arrow
        if depth > 0:
            ctk.CTkLabel(self.inner, text="↳", text_color=THEME["DIM"], font=THEME["FONT_MONO"], width=20).pack(
                side="left", padx=(5, 0))

        # Status & Name
        if self.status == 'COMPLETED':
            text_color = THEME["DIM"]
            name_font = ctk.CTkFont(family="Consolas", size=13, overstrike=True)
            display_name = f"[DONE] {task_data['task_name']}"
        else:
            text_color = THEME["FG"]
            name_font = THEME["FONT_MAIN"]
            display_name = f"> {task_data['task_name']}"

        info_frame = ctk.CTkFrame(self.inner, fg_color="transparent")
        info_frame.pack(side="left", padx=5, expand=True, fill="x")
        ctk.CTkLabel(info_frame, text=display_name, font=name_font, text_color=text_color, anchor="w").pack(fill="x")

        # Meta Data
        created_str = format_short_date(task_data['created_at'])
        date_text = f"ID:{self.task_id} | Init: {created_str}"
        if task_data['due_date']: date_text += f" | ETA: {task_data['due_date']}"
        ctk.CTkLabel(info_frame, text=date_text, font=("Consolas", 10), text_color=THEME["DIM"], anchor="w").pack(
            fill="x")

        # --- RIGHT SIDE BUTTONS ---
        # Order: [ + ] [ KILL ] [ i ] [ ≡ ] [ ▶ ] [ RUN ] 00:00:00

        # 7. Timer Label (Rightmost)
        self.time_str = format_seconds(task_data['time_spent'])
        timer_color = "#3498db" if task_data['current_session_start'] else text_color
        self.timer_label = ctk.CTkLabel(self.inner, text=self.time_str, width=80, text_color=timer_color,
                                        font=("Consolas", 14, "bold"))
        self.timer_label.pack(side="right", padx=10)

        # Helper for Button Creation
        def btn(txt, cmd, color=THEME["FG"], width=30):
            return ctk.CTkButton(self.inner, text=txt, width=width, height=24, fg_color="transparent",
                                 border_width=1, border_color=color, text_color=color,
                                 hover_color="#222", corner_radius=0, font=("Consolas", 11, "bold"), command=cmd)

        if not is_history and self.status != 'COMPLETED':
            # 6. [ RUN ] / [ STOP ]
            if task_data['current_session_start']:
                btn("STOP", self.stop_task, color="red").pack(side="right", padx=2)
            else:
                btn("RUN", self.start_task).pack(side="right", padx=2)

            # 5. [ ▶ ] / [ ▼ ] (Toggle Fold)
            if has_children:
                fold_symbol = "▶" if is_folded else "▼"
                btn(fold_symbol, self.toggle_fold).pack(side="right", padx=2)
            else:
                pass  # Spacer

            # 4. [ ≡ ] (Menu)
            btn("≡", self.open_action_menu, width=30).pack(side="right", padx=(2, 5))

            # 3. [ i ] (Notes)
            has_notes = bool(task_data['notes'] and task_data['notes'].strip())
            note_color = "#00FF41" if has_notes else "#444"
            note_hover = "#111"
            if has_notes: note_hover = "#222"

            note_btn = ctk.CTkButton(self.inner, text="[ i ]", width=30, height=24, fg_color="transparent",
                                     border_width=1, border_color=note_color, text_color=note_color,
                                     hover_color=note_hover, corner_radius=0, font=("Consolas", 11, "bold"),
                                     command=self.open_notes)
            note_btn.pack(side="right", padx=2)

            # 2. [ KILL ] (Mark Done)
            btn("KILL", self.mark_done).pack(side="right", padx=2)

            # 1. [ + ] (Add Subtask)
            if depth < 5:
                btn("+", self.add_subtask).pack(side="right", padx=2)

        elif is_history:
            btn("[REOPEN]", self.reopen_task, width=60).pack(side="right", padx=5)
        elif self.status == 'COMPLETED':
            btn("[UNDO]", self.reopen_task, color="#666").pack(side="right", padx=5)

    def open_notes(self):
        def save_callback(new_text):
            self.db.update_task_notes(self.task_id, new_text)
            self.reload_callback()

        current_notes = self.task_data['notes'] if self.task_data['notes'] else ""
        NotesDialog(self.winfo_toplevel(), self.task_data['task_name'], current_notes, save_callback)

    def open_action_menu(self):
        ActionDialog(self.winfo_toplevel(), self.task_data['task_name'],
                     on_edit=self.edit_task,
                     on_delete=self.delete_task,
                     on_archive=self.archive_task if not self.is_history else None,
                     on_ai_report=self.generate_single_report)

    def generate_single_report(self):
        self.app_reference.generate_task_specific_report(self.task_id)

    def edit_task(self):
        def save(n, e, _):
            self.db.update_task_fields(self.task_id, n, e)
            self.reload_callback()

        TaskDialog(self.winfo_toplevel(), save, title="EDIT_TASK", initial_name=self.task_data['task_name'],
                   initial_eta=self.task_data['due_date'], include_category=False)

    def delete_task(self):
        self.db.delete_task(self.task_id)
        self.reload_callback()

    def archive_task(self):
        self.db.archive_task(self.task_id)
        self.reload_callback()

    def start_task(self):
        self.db.start_timer(self.task_id)
        self.reload_callback()

    def stop_task(self):
        self.db.stop_timer(self.task_id)
        self.reload_callback()

    def mark_done(self):
        self.db.mark_completed(self.task_id)
        self.reload_callback()

    def reopen_task(self):
        self.db.reopen_task(self.task_id)
        self.reload_callback()

    def add_subtask(self):
        def save(n, e, _):
            self.db.add_task(n, due_date=e, category=self.task_data['category'], parent_id=self.task_id)
            self.reload_callback()

        TaskDialog(self.winfo_toplevel(), save, title="SUB_TASK", include_category=False)

    def toggle_fold(self):
        self.toggle_fold_callback(self.task_id)


# --- MAIN APP ---
class TodoApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("TEMagic_Console")
        self.geometry("1050x750")
        self.configure(fg_color="black")
        self.db = TodoDatabase()
        self.folded_parents = set()

        # State variables
        self.show_personal_var = ctk.BooleanVar(value=True)
        self.include_prompt_var = ctk.BooleanVar(value=True)
        self.history_filter_var = ctk.StringVar(value="Current Month")

        # Archive Filter Default: 2 Weeks
        self.history_min_date = (datetime.now() - timedelta(weeks=2)).strftime("%Y-%m-%d %H:%M:%S")

        # Layer 0: Matrix
        self.bg_matrix = MatrixRainLite(self, width=1050, height=750, pad_size=BORDER_PAD)
        self.bg_matrix.place(x=0, y=0, relwidth=1, relheight=1)
        try:
            self.bg_matrix.tk.call('lower', self.bg_matrix._w)
        except:
            pass

        # Layer 1: Container
        self.fg_layer = ctk.CTkFrame(self, fg_color="black", border_width=2, border_color=THEME["BORDER"],
                                     corner_radius=0)
        self.fg_layer.pack(fill="both", expand=True, padx=BORDER_PAD, pady=BORDER_PAD)

        # Header
        self.header = ctk.CTkFrame(self.fg_layer, height=50, corner_radius=0, fg_color="transparent")
        self.header.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(self.header, text="root@MACT_TEM:~#", font=THEME["FONT_HEADER"], text_color=THEME["FG"]).pack(
            side="left", padx=10)

        def head_btn(txt, cmd):
            ctk.CTkButton(self.header, text=txt, font=("Consolas", 12, "bold"),
                          fg_color="transparent", border_color=THEME["FG"], border_width=1,
                          text_color=THEME["FG"], corner_radius=0, hover_color="#222", command=cmd).pack(side="left",
                                                                                                         padx=5)

        head_btn("[ + NEW TASK ]", self.open_add_dialog)
        head_btn("FLUSH_TASK", self.finish_day)
        head_btn("REPORT_WEEK", self.show_report_dialog)

        # UPDATED: Switch Name
        ctk.CTkSwitch(self.header, text="SHOW_QUARTERS", font=("Consolas", 11),
                      progress_color=THEME["DIM"], button_color="white", button_hover_color="gray",
                      fg_color="#333", variable=self.show_personal_var, command=self.refresh_tasks).pack(side="right",
                                                                                                         padx=10)

        # Tabs
        self.tabs = ctk.CTkTabview(self.fg_layer, fg_color="transparent", text_color=THEME["FG"],
                                   segmented_button_fg_color="black",
                                   segmented_button_selected_color="#222", segmented_button_selected_hover_color="#333",
                                   segmented_button_unselected_color="black",
                                   segmented_button_unselected_hover_color="#111", corner_radius=0)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=(0, 20))

        # FIXED: Removed border_color/border_width to avoid crash
        self.tabs._segmented_button.configure(font=THEME["FONT_MONO"])

        # UPDATED: Tab Names
        self.tab_active = self.tabs.add("BRIDGE_COMMAND")
        self.tab_history = self.tabs.add("BRIDGE_ARCHIVES")

        # --- ARCHIVE FILTER BAR (NEW) ---
        self.archive_filter_btn = ctk.CTkSegmentedButton(self.tab_history,
                                                         values=["2 WEEKS", "1 MONTH", "CUSTOM"],
                                                         command=self.on_archive_filter_change,
                                                         font=THEME["FONT_MONO"],
                                                         fg_color="black", selected_color=THEME["DIM"],
                                                         selected_hover_color=THEME["FG"],
                                                         unselected_color="black", unselected_hover_color="#111",
                                                         corner_radius=0, border_width=1)
        self.archive_filter_btn.set("2 WEEKS")
        self.archive_filter_btn.pack(fill="x", padx=20, pady=(0, 10))

        self.active_frame = ctk.CTkScrollableFrame(self.tab_active, fg_color="transparent")
        self.active_frame.pack(fill="both", expand=True, pady=(0, 20))

        self.history_frame = ctk.CTkScrollableFrame(self.tab_history, fg_color="transparent")
        self.history_frame.pack(fill="both", expand=True, pady=(0, 20))

        self.refresh_tasks()
        self.update_timers()

    # --- ARCHIVE FILTER LOGIC ---
    def on_archive_filter_change(self, value):
        if value == "2 WEEKS":
            self.history_min_date = (datetime.now() - timedelta(weeks=2)).strftime("%Y-%m-%d %H:%M:%S")
            self.refresh_tasks()
        elif value == "1 MONTH":
            self.history_min_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
            self.refresh_tasks()
        elif value == "CUSTOM":
            DateFilterDialog(self, self.set_custom_date)

    def set_custom_date(self, date_str):
        self.history_min_date = date_str
        self.refresh_tasks()

    def open_add_dialog(self):
        TaskDialog(self, self.add_task_to_db, include_category=True)

    def add_task_to_db(self, name, eta, category):
        self.db.add_task(name, due_date=eta, category=category)
        self.refresh_tasks()

    def finish_day(self):
        self.db.archive_all_completed()
        self.refresh_tasks()

    def toggle_fold(self, task_id):
        if task_id in self.folded_parents:
            self.folded_parents.remove(task_id)
        else:
            self.folded_parents.add(task_id)
        self.refresh_tasks()

    # --- SINGLE TASK REPORT ---
    def generate_task_specific_report(self, task_id):
        hierarchy = self.db.get_task_hierarchy(task_id)
        if not hierarchy: return

        root_task = hierarchy[0]
        report = [
            f"# PROJECT STATUS REPORT: {root_task['task_name']}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d')}",
            "--------------------------------------------"
        ]

        for t in hierarchy:
            indent = ""
            if t['id'] != root_task['id']:
                indent = "  ↳ "

            status_icon = "✅" if t['status'] == 'COMPLETED' else "🚧"
            line = f"{indent}{status_icon} {t['task_name']} [{t['status']}]"
            report.append(line)

            if t['notes'] and t['notes'].strip():
                note_lines = t['notes'].strip().split('\n')
                for note in note_lines:
                    report.append(f"{indent}    📝 NOTE: {note}")

        report_text = "\n".join(report)

        if self.include_prompt_var.get():
            ai_context = """I am providing a status dump for a specific project hierarchy.
Please summarize the status of this project.
1. Identify the main goal (the root task).
2. List what is Completed vs Pending.
3. SUMMARIZE the "Notes" attached to tasks to explain technical details or blockers.

Data:
-----
"""
            report_text = ai_context + report_text

        self.clipboard_clear()
        self.clipboard_append(report_text)
        self.update()
        tk.messagebox.showinfo("Report Ready", "Project Report (with Notes) copied to clipboard!")

    # --- REPORT DIALOG ---
    def show_report_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("GENERATE_REPORT")
        dialog.geometry("400x500")
        dialog.configure(fg_color="black")
        main = ctk.CTkFrame(dialog, fg_color="black", border_width=1, border_color=THEME["FG"], corner_radius=0)
        main.pack(fill="both", expand=True, padx=2, pady=2)

        ctk.CTkLabel(main, text="REPORT_PARAMETERS", font=THEME["FONT_MAIN"], text_color=THEME["FG"]).pack(pady=15)

        # AI Checkbox
        ctk.CTkCheckBox(main, text="INJECT_AI_PROMPT_CONTEXT", variable=self.include_prompt_var,
                        font=THEME["FONT_MONO"], fg_color=THEME["DIM"], hover_color=THEME["FG"]).pack(pady=5)

        ctk.CTkLabel(main, text="---------------------------------", text_color="#333").pack(pady=10)

        def rpt_btn(txt, mode):
            ctk.CTkButton(main, text=txt, command=lambda: self.generate_report(mode, dialog),
                          fg_color="transparent", border_color=THEME["FG"], border_width=1,
                          text_color=THEME["FG"], corner_radius=0, hover_color="#222").pack(pady=5, padx=20, fill="x")

        rpt_btn("[ CURRENT WEEK ]", "current")
        rpt_btn("[ LAST WEEK ]", "last")

        ctk.CTkLabel(main, text="-- CUSTOM RANGE --", text_color="#666", font=("Consolas", 10)).pack(pady=(15, 5))

        self.start_entry = ctk.CTkEntry(main, placeholder_text="YYYY-MM-DD", font=THEME["FONT_MONO"],
                                        fg_color="#111", border_color="#333", text_color=THEME["FG"])
        self.start_entry.pack(pady=2, padx=20, fill="x")

        self.end_entry = ctk.CTkEntry(main, placeholder_text="YYYY-MM-DD", font=THEME["FONT_MONO"],
                                      fg_color="#111", border_color="#333", text_color=THEME["FG"])
        self.end_entry.pack(pady=2, padx=20, fill="x")

        rpt_btn("[ GENERATE CUSTOM ]", "custom")

    # --- REPORT GENERATION LOGIC ---
    def generate_report(self, mode, dialog_window):
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0)

        if mode == "current":
            start_date = start_of_week
            end_date = today
            title_str = "Current Week"
        elif mode == "last":
            start_date = start_of_week - timedelta(days=7)
            end_date = start_of_week - timedelta(seconds=1)
            title_str = "Last Week"
        elif mode == "custom":
            s_txt = self.start_entry.get()
            e_txt = self.end_entry.get()
            try:
                start_date = datetime.strptime(s_txt, "%Y-%m-%d")
                end_date = datetime.strptime(e_txt, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
                title_str = f"Custom ({s_txt} to {e_txt})"
            except ValueError:
                tk.messagebox.showerror("Error", "Invalid Date Format.\nPlease use YYYY-MM-DD")
                return

        dialog_window.destroy()

        s_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
        e_str = end_date.strftime("%Y-%m-%d %H:%M:%S")

        tasks = self.db.get_tasks_for_report(s_str, e_str)

        report = [
            f"# Work Report: {title_str}\n"
            f"*Generated on {today.strftime('%Y-%m-%d')}*\n"
        ]

        completed = [t for t in tasks if t['status'] in ['COMPLETED', 'ARCHIVED']]
        pending = [t for t in tasks if t['status'] not in ['COMPLETED', 'ARCHIVED']]

        def format_task_line(t):
            if not t['parent_name']:
                return f"\n### 🏆 {t['task_name']}"
            else:
                return f"* **{t['task_name']}** (Part of \"{t['parent_name']}\")"

        report.append("## ✅ Completed / Delivered")
        if completed:
            for t in completed: report.append(format_task_line(t))
        else:
            report.append("* No completed items recorded for this period.")

        report.append("\n## 🚧 In Progress / Pending")
        if pending:
            for t in pending: report.append(format_task_line(t))
        else:
            report.append("* No pending items.")

        report_text = "\n".join(report)

        if self.include_prompt_var.get():
            ai_instructions = """I am pasting a weekly work report generated by my task manager. Please summarize my work based on the following rules:

1. STRUCTURE EXPLANATION:
   - Items marked with "🏆" are MAIN PROJECTS.
   - Items with bullet points "*" are SUBTASKS.
   - If a bullet point says (Part of "Project Name"), it belongs to that parent project.

2. HOW TO INTERPRET PROGRESS:
   - If a "🏆 Main Project" appears in the "✅ Completed" section, announce that the ENTIRE project is finished.
   - If a "🏆 Main Project" appears in "🚧 Pending", but one of its subtasks appears in "✅ Completed", report this as "Progress made on [Project Name]".

3. DESIRED OUTPUT:
   - Write a professional summary of what was achieved.
   - Highlight full project completions first.
   - List specific progress on ongoing projects second.

Here is the report data:
-----------------------
"""
            report_text = ai_instructions + report_text

        self.clipboard_clear()
        self.clipboard_append(report_text)
        self.update()
        tk.messagebox.showinfo("Report Generated", "Work Report copied to clipboard!")

    # --- REFRESH LOGIC ---
    def refresh_tasks(self):
        for w in self.active_frame.winfo_children(): w.destroy()
        for w in self.history_frame.winfo_children(): w.destroy()

        roots = self.db.get_tasks(parent_id=None)

        # TAB 1: ACTIVE (Tree)
        active_roots = [t for t in roots if t['status'] != 'ARCHIVED']
        work_active = [t for t in active_roots if t['category'] == 'Work']
        personal_active = [t for t in active_roots if t['category'] == 'Personal']

        # Helper to draw Big Header
        def draw_header(parent, icon, text):
            # Create a frame to hold the two labels side by side
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.pack(fill="x", padx=10, pady=(15, 5))
            # Huge Icon
            ctk.CTkLabel(f, text=icon, font=THEME["FONT_SECTION_ICON"], text_color=THEME["DIM"]).pack(side="left")
            # Medium-Large Text (Padding Left to separate)
            ctk.CTkLabel(f, text=text, font=THEME["FONT_SECTION_TEXT"], text_color=THEME["DIM"]).pack(side="left",
                                                                                                      padx=10)

        if self.show_personal_var.get() and personal_active:
            # UPDATED: Personal Header using DANTE_QUARTERS with Paw Prints
            draw_header(self.active_frame, "🐾", "DANTE_QUARTERS")
            for task in personal_active: self.render_task_node(task, 0, self.active_frame, is_history=False)

        if work_active:
            # UPDATED: Work Header
            draw_header(self.active_frame, "⚗", "WORK")
            for task in work_active: self.render_task_node(task, 0, self.active_frame, is_history=False)

        # TAB 2: HISTORY
        # UPDATED: Uses self.history_min_date based on Segmented Button
        archived = self.db.get_all_archived_tasks(min_date=self.history_min_date)
        for t in archived:
            display_task = dict(t)
            if t['parent_name']:
                display_task['task_name'] = f"{t['task_name']} (Part of \"{t['parent_name']}\")"
            TaskWidget(self.history_frame, display_task, self.db, self.refresh_tasks, self.toggle_fold, self,
                       is_history=True)

    def render_task_node(self, task, depth, parent_frame, is_history):
        is_folded = task['id'] in self.folded_parents

        children = self.db.get_tasks(parent_id=task['id'])
        active_children = [c for c in children if c['status'] != 'ARCHIVED']
        has_children = len(active_children) > 0

        TaskWidget(parent_frame, task, self.db, self.refresh_tasks, self.toggle_fold, self, is_folded, depth,
                   is_history, has_children)

        for child in active_children:
            if is_folded: continue
            self.render_task_node(child, depth + 1, parent_frame, is_history)

    def update_timers(self):
        current_time = datetime.now()
        for widget in self.active_frame.winfo_children():
            # Must check if it is a TaskWidget because we now have Header Frames in the list too
            if isinstance(widget, TaskWidget) and widget.task_data['current_session_start']:
                start_dt = datetime.strptime(widget.task_data['current_session_start'], "%Y-%m-%d %H:%M:%S")
                elapsed = int((current_time - start_dt).total_seconds())
                total = widget.task_data['time_spent'] + elapsed
                widget.timer_label.configure(text=format_seconds(total), text_color="#00FF41")
        self.after(5000, self.update_timers)

    def on_closing(self):
        self.bg_matrix.running = False
        self.db.close()
        self.destroy()


if __name__ == "__main__":
    app = TodoApp()
    app.bind("<FocusOut>", lambda e: setattr(app.bg_matrix, 'running', False))
    app.bind("<FocusIn>", lambda e: [setattr(app.bg_matrix, 'running', True), app.bg_matrix.animate()])
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()