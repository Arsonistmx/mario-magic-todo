# 🍄 Mario Magic Do List

A modern, dark-mode desktop Task Manager built with Python. It features infinite sub-tasking, precise time-tracking, and a persistent local database. Designed for high-performance workflow with a "Gamified" feel and AI integration.

## 🚀 Project Overview
* **Type:** Desktop GUI Application
* **Language:** Python 3.x
* **UI Framework:** `customtkinter` (Modern, Dark Mode)
* **Database:** `sqlite3` (Local, Relational)
* **Architecture:** Component-Based (MVC pattern)

## ✨ Core Features

### 1. Advanced Task Management
* **Hierarchy:** Infinite nesting of tasks (Main Task $\rightarrow$ Sub-task $\rightarrow$ Sub-sub-task...).
* **Work-First Workflow:** New tasks default to **🏢 WORK** category to reduce friction.
* **Smart Grouping:** Tasks are automatically separated into **🏢 WORK** and **🏠 PERSONAL** headers.
* **Toggle Focus:** "Show Personal" switch allows users to hide personal tasks during work hours.

### 2. Time Tracking Engine ⏱️
* **Stopwatch Logic:** Play/Stop buttons track exact seconds spent on tasks.
* **Crash-Proof:** Timer state is saved in the DB. If the app/computer crashes, the timer continues running in the background.
* **Time Propagation:** Time spent on a sub-task automatically bubbles up and adds to the Main Task's total.

### 3. AI-Ready Reporting 📄 (New!)
* **Smart Context:** Generates a Markdown report optimized for AI tools (ChatGPT/Claude).
* **Visual Hierarchy:** Distinguishes between **🏆 Main Projects** and **Sub-tasks** to clarify progress vs. completion.
* **Custom Ranges:** Select specific date ranges or quick filters (Current Week / Last Week).
* **AI Prompt Injection:** Automatically prepends context rules so the AI understands your project structure immediately.
* **Privacy Focus:** Reports strictly exclude "Personal" items—only Work tasks are exported.

### 4. Data Persistence
* **Active vs. History:** Tabbed interface separates active work from closed tasks.
* **Smart Reopen:** Reopening a task from History automatically resurrects its Parent task to ensure hierarchy integrity.

---

## 🛠️ Technical Architecture

### Database Schema (`database.py`)
The app uses a self-referencing SQL table to handle hierarchy.

| Column | Type | Purpose |
| :--- | :--- | :--- |
| `id` | INTEGER | Primary Key. |
| `parent_id` | INTEGER | Self-reference for sub-tasks (FK). |
| `task_name` | TEXT | Description of the task. |
| `due_date` | TEXT | ETA string (e.g., "2 Hours"). |
| `category` | TEXT | Defaults to 'Work'. |
| `time_spent` | INTEGER | Total seconds worked (accumulated). |
| `current_session_start` | TEXT | Timestamp if timer is running (NULL if stopped). |
| `status` | TEXT | 'NEW', 'IN_PROGRESS', 'COMPLETED'. |

### Application Logic (`main.py`)
* **`TodoApp` Class:** The main controller. Handles the window, tabs, and database connection.
* **`TaskWidget` Class:** A reusable UI component representing a single row. It handles its own buttons, indenting (depth), and right-click events.
* **Report Generation:** A robust system that fetches tasks, filters by date/category, checks parent lineage, and formats strings for AI consumption.

---

## ⚙️ Installation & Setup

1.  **Clone/Create Project Folder:**
    ```bash
    mkdir TodoApp
    cd TodoApp
    ```

2.  **Create Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install customtkinter
    ```

4.  **Run the App:**
    ```bash
    python main.py
    ```

---

## 🔮 Future Roadmap
* **Packaging:** Convert to `.exe` / `.app` using PyInstaller.
* **Analytics Visuals:** Charts for time spent per category inside the app.
* **Sound Effects:** Audio feedback for timer start/stop.
