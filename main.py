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
    "FONT_HEADER": ("Courier New", 20, "bold")
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
        self.col_spacing = int(self.font_size * 15)  # Sparse rain
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
        self.after(200, self.animate)  # Eco mode


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
    def __init__(self, parent, callback, title="EXECUTE_NEW_TASK", initial_name="", initial_eta="",
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
            self.cat_switch = ctk.CTkSegmentedButton(self.main, values=["Personal", "Work"], font=THEME["FONT_MONO"],
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
        cat = "Work" if not self.include_category else self.cat_switch.get()
        if name:
            self.callback(name, eta, cat)
            self.destroy()


class ActionDialog(ctk.CTkToplevel):
    def __init__(self, parent, task_name, on_edit, on_delete, on_archive):
        super().__init__(parent)
        self.title("TASK_OPERATIONS")
        self.geometry("300x250")
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

        action_btn("[ EDIT PROPERTIES ]", on_edit)
        if on_archive: action_btn("[ ARCHIVE ]", on_archive)
        action_btn("[ DELETE ]", on_delete, color="#ff4444")
        ctk.CTkButton(self.main, text="[ CANCEL ]", font=("Consolas", 10), text_color="#666",
                      fg_color="transparent", hover_color="#111", command=self.destroy).pack(pady=(10, 0))


# --- TASK WIDGET ---
class TaskWidget(ctk.CTkFrame):
    def __init__(self, parent, task_data, db, reload_callback, toggle_fold_callback, is_folded=False, depth=0,
                 is_history=False):
        super().__init__(parent, fg_color="transparent", border_width=0, corner_radius=0)
        self.pack(fill="x", pady=2, padx=(depth * 25 + 5, 5))
        self.inner = ctk.CTkFrame(self, fg_color="transparent", border_color=THEME["DIM"], border_width=1,
                                  corner_radius=0)
        self.inner.pack(fill="both", expand=True)

        self.db = db
        self.task_data = task_data
        self.reload_callback = reload_callback
        self.toggle_fold_callback = toggle_fold_callback
        self.task_id = task_data['id']
        self.is_history = is_history
        self.status = task_data['status']

        if depth > 0:
            ctk.CTkLabel(self.inner, text="↳", text_color=THEME["DIM"], font=THEME["FONT_MONO"], width=20).pack(
                side="left", padx=(5, 0))

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

        created_str = format_short_date(task_data['created_at'])
        date_text = f"ID:{self.task_id} | Init: {created_str}"
        if task_data['due_date']: date_text += f" | ETA: {task_data['due_date']}"
        ctk.CTkLabel(info_frame, text=date_text, font=("Consolas", 10), text_color=THEME["DIM"], anchor="w").pack(
            fill="x")

        self.time_str = format_seconds(task_data['time_spent'])
        timer_color = "#3498db" if task_data['current_session_start'] else text_color
        self.timer_label = ctk.CTkLabel(self.inner, text=self.time_str, width=80, text_color=timer_color,
                                        font=("Consolas", 14, "bold"))
        self.timer_label.pack(side="left", padx=10)

        def btn(txt, cmd, color=THEME["FG"], width=30):
            return ctk.CTkButton(self.inner, text=txt, width=width, height=24, fg_color="transparent",
                                 border_width=1, border_color=color, text_color=color,
                                 hover_color="#222", corner_radius=0, font=("Consolas", 11, "bold"), command=cmd)

        btn("[...]", self.open_action_menu, width=30).pack(side="right", padx=(2, 5))

        if not is_history and self.status != 'COMPLETED':
            fold_char = "+" if is_folded else "-"
            btn(fold_char, self.toggle_fold).pack(side="right", padx=2)

        if is_history:
            btn("[REOPEN]", self.reopen_task, width=60).pack(side="right", padx=5)
        elif self.status == 'COMPLETED':
            btn("[UNDO]", self.reopen_task, color="#666").pack(side="right", padx=5)
        else:
            btn("OK", self.mark_done).pack(side="right", padx=2)
            if depth < 5: btn("+", self.add_subtask).pack(side="right", padx=2)
            if task_data['current_session_start']:
                btn("STOP", self.stop_task, color="red").pack(side="right", padx=2)
            else:
                btn("RUN", self.start_task).pack(side="right", padx=2)

    def open_action_menu(self):
        ActionDialog(self.winfo_toplevel(), self.task_data['task_name'], on_edit=self.edit_task,
                     on_delete=self.delete_task, on_archive=self.archive_task if not self.is_history else None)

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
        self.title("MARIO_SYS_V1.1")
        self.geometry("1050x750")
        self.configure(fg_color="black")
        self.db = TodoDatabase()
        self.folded_parents = set()

        # State variables
        self.show_personal_var = ctk.BooleanVar(value=True)
        self.include_prompt_var = ctk.BooleanVar(value=True)
        self.history_filter_var = ctk.StringVar(value="Current Month")

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
        ctk.CTkLabel(self.header, text="root@MARIO-SYS:~#", font=THEME["FONT_HEADER"], text_color=THEME["FG"]).pack(
            side="left", padx=10)

        def head_btn(txt, cmd):
            ctk.CTkButton(self.header, text=txt, font=("Consolas", 12, "bold"),
                          fg_color="transparent", border_color=THEME["FG"], border_width=1,
                          text_color=THEME["FG"], corner_radius=0, hover_color="#222", command=cmd).pack(side="left",
                                                                                                         padx=5)

        head_btn("[ + NEW TASK ]", self.open_add_dialog)
        head_btn("[ END DAY ]", self.finish_day)
        head_btn("[ REPORT ]", self.show_report_dialog)

        ctk.CTkSwitch(self.header, text="SHOW_PERSONAL", font=("Consolas", 11),
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

        self.tab_active = self.tabs.add("ACTIVE_PROCESSES")
        self.tab_history = self.tabs.add("LOGS_ARCHIVE")
        self.tabs._segmented_button.configure(font=THEME["FONT_MONO"])

        self.active_frame = ctk.CTkScrollableFrame(self.tab_active, fg_color="transparent")
        self.active_frame.pack(fill="both", expand=True, pady=(0, 20))

        self.history_frame = ctk.CTkScrollableFrame(self.tab_history, fg_color="transparent")
        self.history_frame.pack(fill="both", expand=True, pady=(0, 20))

        self.refresh_tasks()
        self.update_timers()

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

    # --- UPDATED REPORT DIALOG ---
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

    # --- UPDATED REPORT GENERATION LOGIC ---
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

    # --- UPDATED REFRESH LOGIC ---
    def refresh_tasks(self):
        for w in self.active_frame.winfo_children(): w.destroy()
        for w in self.history_frame.winfo_children(): w.destroy()

        roots = self.db.get_tasks(parent_id=None)

        # TAB 1: ACTIVE (Tree)
        active_roots = [t for t in roots if t['status'] != 'ARCHIVED']
        work_active = [t for t in active_roots if t['category'] == 'Work']
        personal_active = [t for t in active_roots if t['category'] == 'Personal']

        if self.show_personal_var.get() and personal_active:
            ctk.CTkLabel(self.active_frame, text="🏠 PERSONAL", anchor="w", font=("Consolas", 12, "bold"),
                         text_color=THEME["DIM"]).pack(fill="x", padx=10, pady=(10, 5))
            for task in personal_active: self.render_task_node(task, 0, self.active_frame, is_history=False)

        if work_active:
            ctk.CTkLabel(self.active_frame, text="🏢 WORK", anchor="w", font=("Consolas", 12, "bold"),
                         text_color=THEME["DIM"]).pack(fill="x", padx=10, pady=(10, 5))
            for task in work_active: self.render_task_node(task, 0, self.active_frame, is_history=False)

        # TAB 2: HISTORY (Simple List)
        # Note: Keeps simple list logic to ensure stability, but you can expand this later.
        archived = self.db.get_all_archived_tasks(min_date=None)
        for t in archived[:20]:
            display_task = dict(t)
            if t['parent_name']:
                display_task['task_name'] = f"{t['task_name']} (Part of \"{t['parent_name']}\")"
            TaskWidget(self.history_frame, display_task, self.db, self.refresh_tasks, self.toggle_fold, is_history=True)

    def render_task_node(self, task, depth, parent_frame, is_history):
        is_folded = task['id'] in self.folded_parents
        TaskWidget(parent_frame, task, self.db, self.refresh_tasks, self.toggle_fold, is_folded, depth, is_history)

        children = self.db.get_tasks(parent_id=task['id'])
        for child in children:
            if child['status'] == 'ARCHIVED': continue
            if is_folded and child['status'] == 'COMPLETED': continue
            self.render_task_node(child, depth + 1, parent_frame, is_history)

    def update_timers(self):
        current_time = datetime.now()
        for widget in self.active_frame.winfo_children():
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