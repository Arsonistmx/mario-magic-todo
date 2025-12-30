# 🍄 Mario Magic Do List (MARIO_SYS_V1.1)

A high-performance, dark-mode desktop Task Manager built with Python. Designed for deep-work sessions with a "Matrix/Hacker" terminal aesthetic, infinite sub-tasking, and privacy-first AI reporting.

## 🚀 Project Overview
* **Type:** Desktop GUI Application
* **Language:** Python 3.x
* **UI Framework:** `customtkinter` (Sharp, High-Contrast Dark Mode)
* **Database:** `sqlite3` (Local, Relational, Self-Referencing)
* **Performance:** **Eco-Mode Engine** (<2% CPU Usage in Idle).

## ✨ Core Features

### 1. "Eco-Mode" Rendering 🌿
* **Smart Focus Detection:** The Matrix Rain animation automatically pauses when you click away to another window, dropping CPU usage to near 0%.
* **Optimized Graphics:** Rain density and frame rate are tuned for maximum battery life while maintaining the "Hacker" aesthetic.

### 2. Advanced Task Management
* **Hierarchy:** Infinite nesting (Main Task $\rightarrow$ Sub-task $\rightarrow$ Sub-sub-task...).
* **Action Menu:** New dedicated `[...]` button per task for stable Editing, Deleting, and Archiving.
* **Work-First Workflow:** Smart separation of **🏢 WORK** and **🏠 PERSONAL** tasks.
* **Focus Mode:** "Show Personal" toggle hides non-work items during business hours.

### 3. AI-Ready Reporting 📄
* **Custom Date Ranges:** Generate reports for the Current Week, Last Week, or any specific Date Range.
* **Context Injection:** Optional "AI Prompt" checkbox automatically prepends context rules so tools like ChatGPT/Claude understand your project structure immediately.
* **Privacy First:** Reports strictly exclude "Personal" items—only Work tasks are exported.

### 4. Time Tracking Engine ⏱️
* **Precise Logging:** Play/Stop buttons track exact seconds.
* **Crash-Proof:** Timer state saves to DB instantly; survives app restarts.
* **Time Propagation:** Time spent on a sub-task bubbles up to the Parent Task's total.

---

## 🛠️ Technical Architecture

### Application Logic (`main.py`)
* **`TodoApp`:** Main controller handling the "Rain" canvas, tabs, and focus events (Idle optimization).
* **`TaskWidget`:** Reusable row component. Handles indentation (depth), timing logic, and the new Action Menu.
* **`ActionDialog`:** A stable popup system replacing the standard right-click menu for task operations.
* **`MatrixRainLite`:** Custom canvas implementation for the background visual effects.

### Database Schema (`database.py`)
* **Self-Referencing Table:** Tasks point to `parent_id` to create tree structures.
* **Sessions Table:** Logs every "Start/Stop" interval for granular time auditing.

---

## ⚙️ Installation

1.  **Clone/Create Project Folder:**
    ```bash
    mkdir TodoApp
    cd TodoApp
    ```

2.  **Create Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # Activate it:
    # Windows: venv\Scripts\activate
    # Mac/Linux: source venv/bin/activate
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

## 🔮 Roadmap & Status

### ✅ Completed
* **Performance:** CPU "Idle Trick" implemented (Pause animation on blur).
* **Visuals:** Fixed border rendering (Sharp corners `corner_radius=0`, correct z-layering).
* **UX Upgrade:** Replaced unstable Right-Click menu with dedicated `[...]` Action Buttons.
* **Reporting:** Added Custom Date Pickers and AI Prompt Injection.

### 🚧 In Progress
* **Sound:** Adding retro SFX for timer interactions.
* **Packaging:** Converting to `.exe` for portable use.

### 📝 Planned
* **Analytics:** Visual charts for time spent per category inside the app.
