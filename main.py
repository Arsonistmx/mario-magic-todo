import customtkinter as ctk
import tkinter as tk
from datetime import datetime, timedelta
from database import TodoDatabase
from tkinter import messagebox

# --- CONFIGURATION ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


def format_seconds(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def format_short_date(date_str):
    if not date_str: return ""
    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    return dt.strftime("%b %d %H:%M")


# --- COMPONENT 1: DIALOGS ---
class TaskDialog(ctk.CTkToplevel):
    def __init__(self, parent, callback, title="New Task", initial_name="", initial_eta="", include_category=True):
        super().__init__(parent)
        self.callback = callback
        self.include_category = include_category
        self.title(title)
        height = 380 if include_category else 300
        self.geometry(f"400x{height}")
        self.transient(parent)
        self.grab_set()

        ctk.CTkLabel(self, text=title, font=("Arial", 18, "bold")).pack(pady=(15, 10))
        ctk.CTkLabel(self, text="Task Name:", anchor="w", text_color="#aaaaaa", font=("Arial", 12)).pack(pady=(5, 0),
                                                                                                         padx=20,
                                                                                                         fill="x")
        self.name_entry = ctk.CTkEntry(self, placeholder_text="Enter task name...")
        self.name_entry.pack(pady=5, padx=20, fill="x")
        self.name_entry.insert(0, initial_name)
        self.name_entry.focus()

        ctk.CTkLabel(self, text="ETA / Time Limit (Optional):", anchor="w", text_color="#aaaaaa",
                     font=("Arial", 12)).pack(pady=(10, 0), padx=20, fill="x")
        self.eta_entry = ctk.CTkEntry(self, placeholder_text="e.g. 2 Hours, Tomorrow 5PM")
        self.eta_entry.pack(pady=5, padx=20, fill="x")
        self.eta_entry.insert(0, initial_eta)

        if self.include_category:
            ctk.CTkLabel(self, text="Category:", anchor="w", text_color="#aaaaaa", font=("Arial", 12)).pack(
                pady=(10, 5), padx=20, fill="x")
            self.cat_switch = ctk.CTkSegmentedButton(self, values=["Personal", "Work"])
            self.cat_switch.set("Work")  # Default to Work
            self.cat_switch.pack(pady=5, padx=20)

        ctk.CTkButton(self, text="Save Changes", height=40, font=("Arial", 13, "bold"), command=self.save_task).pack(
            pady=20, padx=20, fill="x")

    def save_task(self):
        name = self.name_entry.get()
        eta = self.eta_entry.get()
        cat = "Work"
        if self.include_category: cat = self.cat_switch.get()
        if name:
            self.callback(name, eta, cat)
            self.destroy()


# --- COMPONENT 2: TASK ROW ---
class TaskWidget(ctk.CTkFrame):
    def __init__(self, parent, task_data, db, reload_callback, toggle_fold_callback, is_folded=False, depth=0,
                 is_history=False):
        super().__init__(parent, fg_color="#2b2b2b", corner_radius=6)
        self.pack(fill="x", pady=2, padx=(depth * 25 + 10, 10))

        self.db = db
        self.task_data = task_data
        self.reload_callback = reload_callback
        self.toggle_fold_callback = toggle_fold_callback
        self.task_id = task_data['id']
        self.is_history = is_history
        self.status = task_data['status']

        if depth > 0:
            ctk.CTkLabel(self, text="↳", text_color="gray", width=20).pack(side="left", padx=(5, 0))

        if self.status == 'COMPLETED':
            text_color = "#666666"
            name_font = ctk.CTkFont(family="Arial", size=13, overstrike=True)
        elif self.status == 'ARCHIVED':
            text_color = "#444444"
            name_font = ctk.CTkFont(family="Arial", size=13)
        else:
            text_color = "white"
            name_font = ctk.CTkFont(family="Arial", size=14, weight="bold") if depth == 0 else ctk.CTkFont(
                family="Arial", size=13)

        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(side="left", padx=10, expand=True, fill="x")

        ctk.CTkLabel(info_frame, text=task_data['task_name'], font=name_font, text_color=text_color, anchor="w").pack(
            fill="x")

        created_str = format_short_date(task_data['created_at'])
        date_text = f"Created: {created_str}"
        if self.status == 'COMPLETED':
            date_text += " (Done - Finish Day to Archive)"
        elif self.status == 'ARCHIVED':
            date_text += f" | Closed: {format_short_date(task_data['completed_at'])}"

        ctk.CTkLabel(info_frame, text=date_text, font=("Arial", 10), text_color="gray", anchor="w").pack(fill="x")

        if task_data['due_date']:
            ctk.CTkLabel(self, text=f"🕒 {task_data['due_date']}", text_color="gray", font=("Arial", 11)).pack(
                side="left", padx=10)

        self.time_str = format_seconds(task_data['time_spent'])

        if self.status == 'COMPLETED':
            timer_color = "#555"
        elif task_data['current_session_start']:
            timer_color = "#3498db"
        else:
            timer_color = "gray"

        self.timer_label = ctk.CTkLabel(self, text=self.time_str, width=80, text_color=timer_color,
                                        font=("Consolas", 13, "bold"))
        self.timer_label.pack(side="left", padx=10)

        if not is_history:
            eye_color = "#E67E22" if is_folded else "#555"
            ctk.CTkButton(self, text="👁", width=30, fg_color=eye_color, hover_color="#D35400",
                          command=self.toggle_fold).pack(side="right", padx=2)

        if is_history:
            ctk.CTkButton(self, text="♻ Reopen", width=70, fg_color="#E67E22", hover_color="#D35400",
                          font=("Arial", 11), command=self.reopen_task).pack(side="right", padx=10, pady=5)
        elif self.status == 'COMPLETED':
            ctk.CTkButton(self, text="Undo", width=40, fg_color="#555", command=self.reopen_task).pack(side="right",
                                                                                                       padx=5)
        else:
            ctk.CTkButton(self, text="✔", width=30, fg_color="#27ae60", command=self.mark_done).pack(side="right",
                                                                                                     padx=5)
            if depth < 5:
                ctk.CTkButton(self, text="+", width=30, fg_color="#555", command=self.add_subtask).pack(side="right",
                                                                                                        padx=5)
            if task_data['current_session_start']:
                ctk.CTkButton(self, text="⏹", width=30, fg_color="#c0392b", command=self.stop_task).pack(side="right",
                                                                                                         padx=5)
            else:
                ctk.CTkButton(self, text="▶", width=30, fg_color="#2980b9", command=self.start_task).pack(side="right",
                                                                                                          padx=5)

        self.bind("<Button-3>", self.show_context_menu)
        self.bind("<Button-2>", self.show_context_menu)

    def show_context_menu(self, event):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="✏️ Edit Task", command=self.edit_task)
        if not self.is_history:
            menu.add_command(label="📦 Archive to History", command=self.archive_task)
        menu.add_separator()
        menu.add_command(label="🗑️ Delete Completely", command=self.delete_task)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def edit_task(self):
        def save_edits(new_name, new_eta, _):
            self.db.update_task_fields(self.task_id, new_name, new_eta)
            self.reload_callback()

        TaskDialog(self.winfo_toplevel(), save_edits, title="Edit Task", initial_name=self.task_data['task_name'],
                   initial_eta=self.task_data['due_date'] or "", include_category=False)

    def delete_task(self):
        self.db.delete_task(self.task_id)
        self.reload_callback()

    def archive_task(self):
        self.db.archive_task(self.task_id)
        self.reload_callback()

    def start_task(self):
        dialog = ctk.CTkInputDialog(text="How many minutes will you invest?\n(Leave empty for stopwatch)",
                                    title="Commitment")
        result = dialog.get_input()
        goal_seconds = int(result) * 60 if result and result.isdigit() else None
        self.db.start_timer(self.task_id, goal_seconds=goal_seconds)
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
        def save_sub(name, eta, cat):
            parent_cat = self.task_data['category']
            self.db.add_task(name, due_date=eta, category=parent_cat, parent_id=self.task_id)
            self.reload_callback()

        TaskDialog(self.winfo_toplevel(), save_sub, title="New Sub-Task", include_category=False)

    def toggle_fold(self):
        self.toggle_fold_callback(self.task_id)


# --- MAIN APP ---
class TodoApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Mario Magic Do List")
        self.geometry("950x700")

        self.db = TodoDatabase()
        self.folded_parents = set()

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. HEADER
        self.header = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color="#1a1a1a")
        self.header.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(self.header, text="MARIO MAGIC", font=("Impact", 22), text_color="#f1c40f").pack(side="left",
                                                                                                      padx=20)

        ctk.CTkButton(self.header, text="+ New Task", font=("Arial", 13, "bold"), fg_color="#2980b9", width=120,
                      command=self.open_add_dialog).pack(side="left", padx=10)

        ctk.CTkButton(self.header, text="🏁 Finish Day", font=("Arial", 12, "bold"), fg_color="#27ae60", width=100,
                      command=self.finish_day).pack(side="left", padx=5)

        # Report Button (New)
        ctk.CTkButton(self.header, text="📄 Report", font=("Arial", 12, "bold"), fg_color="#8e44ad", width=80,
                      command=self.show_report_dialog).pack(side="left", padx=5)

        self.show_personal_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(self.header, text="Show Personal", variable=self.show_personal_var,
                      command=self.refresh_tasks).pack(side="right", padx=(10, 20))

        # 2. TABS
        self.tabs = ctk.CTkTabview(self)
        self.tabs.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        self.tab_active = self.tabs.add("Active Tasks")
        self.tab_history = self.tabs.add("History / Closed")

        self.active_frame = ctk.CTkScrollableFrame(self.tab_active, fg_color="transparent")
        self.active_frame.pack(fill="both", expand=True)

        self.history_frame = ctk.CTkScrollableFrame(self.tab_history, fg_color="transparent")
        self.history_frame.pack(fill="both", expand=True)

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

    # --- REPORT GENERATION UPDATED ---
    def show_report_dialog(self):
        """Updated with Custom Range UI & AI Context Checkbox"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Generate AI Report")
        dialog.geometry("350x420")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Select Range (Work Only):", font=("Arial", 14, "bold")).pack(pady=(15, 10))

        # NEW: Checkbox to include prompt text
        self.include_prompt_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(dialog, text="Include AI Context Prompt", variable=self.include_prompt_var).pack(pady=(0, 15))

        # Quick Buttons
        ctk.CTkButton(dialog, text="Current Week", command=lambda: self.generate_report("current", dialog)).pack(pady=5,
                                                                                                                 padx=20,
                                                                                                                 fill="x")
        ctk.CTkButton(dialog, text="Last Week", command=lambda: self.generate_report("last", dialog)).pack(pady=5,
                                                                                                           padx=20,
                                                                                                           fill="x")

        # Custom Range Logic
        ctk.CTkLabel(dialog, text="--- OR Custom Range ---", text_color="gray").pack(pady=10)

        frame_custom = ctk.CTkFrame(dialog, fg_color="transparent")
        frame_custom.pack(pady=0, padx=20, fill="x")

        self.start_entry = ctk.CTkEntry(frame_custom, placeholder_text="Start (YYYY-MM-DD)")
        self.start_entry.pack(pady=5, fill="x")

        self.end_entry = ctk.CTkEntry(frame_custom, placeholder_text="End (YYYY-MM-DD)")
        self.end_entry.pack(pady=5, fill="x")

        ctk.CTkButton(dialog, text="Generate Custom", fg_color="#E67E22", hover_color="#D35400",
                      command=lambda: self.generate_report("custom", dialog)).pack(pady=10, padx=20, fill="x")

    def generate_report(self, mode, dialog_window):
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())  # Monday
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0)

        # Determine dates
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

        # DB now filters out Personal automatically
        tasks = self.db.get_tasks_for_report(s_str, e_str)

        # Build Markdown
        report = [
            f"# Work Report: {title_str}\n"
            f"*Generated on {today.strftime('%Y-%m-%d')}*\n"
        ]

        completed = [t for t in tasks if t['status'] in ['COMPLETED', 'ARCHIVED']]
        pending = [t for t in tasks if t['status'] not in ['COMPLETED', 'ARCHIVED']]

        def format_task_line(t):
            # VISUAL DISTINCTION:
            # If no parent -> Main Task -> Big Header (🏆)
            if not t['parent_name']:
                return f"\n### 🏆 {t['task_name']}"
            # If parent -> Subtask -> Bullet with context
            else:
                return f"* **{t['task_name']}** (Part of \"{t['parent_name']}\")"

        report.append("## ✅ Completed / Delivered")
        if completed:
            for t in completed:
                report.append(format_task_line(t))
        else:
            report.append("* No completed items recorded for this period.")

        report.append("\n## 🚧 In Progress / Pending")
        if pending:
            for t in pending:
                report.append(format_task_line(t))
        else:
            report.append("* No pending items.")

        report_text = "\n".join(report)

        # --- AUTO-INJECT AI PROMPT ---
        if self.include_prompt_var.get():
            ai_instructions = """I am pasting a weekly work report generated by my task manager. Please summarize my work based on the following rules:

1. STRUCTURE EXPLANATION:
   - Items marked with "🏆" are MAIN PROJECTS.
   - Items with bullet points "*" are SUBTASKS.
   - If a bullet point says (Part of "Project Name"), it belongs to that parent project.

2. HOW TO INTERPRET PROGRESS:
   - If a "🏆 Main Project" appears in the "✅ Completed" section, announce that the ENTIRE project is finished.
   - If a "🏆 Main Project" appears in "🚧 Pending", but one of its subtasks appears in "✅ Completed", report this as "Progress made on [Project Name]".
   - Do not list the same project twice; if a project is Pending but has completed subtasks, focus on the progress made.

3. DESIRED OUTPUT:
   - Write a professional summary of what was achieved.
   - Highlight full project completions first.
   - List specific progress on ongoing projects second.

Here is the report data:
-----------------------
"""
            report_text = ai_instructions + report_text
        # -----------------------------

        # Copy to Clipboard
        self.clipboard_clear()
        self.clipboard_append(report_text)
        self.update()

        # Notify User
        tk.messagebox.showinfo("Report Generated", "Work Report copied to clipboard!\n(Ready to paste into AI)")

    def refresh_tasks(self):
        for w in self.active_frame.winfo_children(): w.destroy()
        for w in self.history_frame.winfo_children(): w.destroy()

        roots = self.db.get_tasks(parent_id=None)

        # TAB 1: ACTIVE (Not Archived)
        active_roots = [t for t in roots if t['status'] != 'ARCHIVED']
        work_active = [t for t in active_roots if t['category'] == 'Work']
        personal_active = [t for t in active_roots if t['category'] == 'Personal']

        if self.show_personal_var.get() and personal_active:
            ctk.CTkLabel(self.active_frame, text="🏠 PERSONAL", anchor="w", font=("Arial", 12, "bold"),
                         text_color="#aaa").pack(fill="x", padx=10, pady=(10, 5))
            for task in personal_active: self.render_task_node(task, 0, self.active_frame, is_history=False)

        if work_active:
            ctk.CTkLabel(self.active_frame, text="🏢 WORK", anchor="w", font=("Arial", 12, "bold"),
                         text_color="#aaa").pack(fill="x", padx=10, pady=(10, 5))
            for task in work_active: self.render_task_node(task, 0, self.active_frame, is_history=False)

        # TAB 2: HISTORY (Archived Only)
        archived_roots = [t for t in roots if t['status'] == 'ARCHIVED']
        if archived_roots:
            for task in archived_roots: self.render_task_node(task, 0, self.history_frame, is_history=True)
        else:
            ctk.CTkLabel(self.history_frame, text="No archived tasks yet.", text_color="gray").pack(pady=20)

    def render_task_node(self, task, depth, parent_frame, is_history):
        is_folded = task['id'] in self.folded_parents
        TaskWidget(parent_frame, task, self.db, self.refresh_tasks, self.toggle_fold, is_folded, depth, is_history)

        children = self.db.get_tasks(parent_id=task['id'])
        for child in children:
            if is_history:
                self.render_task_node(child, depth + 1, parent_frame, is_history)
            else:
                if child['status'] == 'ARCHIVED': continue
                if is_folded and child['status'] == 'COMPLETED': continue
                self.render_task_node(child, depth + 1, parent_frame, is_history)

    def update_timers(self):
        current_time = datetime.now()
        for widget in self.active_frame.winfo_children():
            if isinstance(widget, TaskWidget) and widget.task_data['current_session_start']:
                start_dt = datetime.strptime(widget.task_data['current_session_start'], "%Y-%m-%d %H:%M:%S")
                elapsed_this_session = int((current_time - start_dt).total_seconds())
                goal = widget.task_data['session_goal_seconds']

                if goal and goal > 0:
                    remaining = goal - elapsed_this_session
                    if remaining <= 0:
                        widget.timer_label.configure(text="⭐ DONE!", text_color="#2ecc71")
                    else:
                        widget.timer_label.configure(text=f"⏳ {format_seconds(remaining)}", text_color="#e67e22")
                else:
                    total = widget.task_data['time_spent'] + elapsed_this_session
                    widget.timer_label.configure(text=format_seconds(total), text_color="#3498db")
        self.after(1000, self.update_timers)

    def on_closing(self):
        self.db.close()
        self.destroy()


if __name__ == "__main__":
    app = TodoApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()