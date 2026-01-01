# 🚀 Mario Magic To-Do (v2.1)

**Mario Magic To-Do** is a high-performance, dark-mode terminal interface for task management. It combines a "Matrix/Sci-Fi" aesthetic with deep project tracking, recursive sub-tasking, and a fully gamified interstellar journey.

Designed for the "Commander" who needs to manage **Work Operations** and **Personal Quarters** from a single command bridge while traveling through the cosmos.

---

## 🔒 Security & Stability (Verified)

**Status:** ✅ **SECURE for Local Use**

* **Offline / Air-Gapped:** The application contains **no** networking code. It does not connect to the internet, ensuring complete privacy of your tasks and data.
* **Database Safety:** All database operations are protected with transaction rollbacks. If the app crashes or is force-closed, the database automatically unlocks and recovers, preventing data corruption.
* **AI Reporting:** The "Generate AI Report" feature is a passive text generator. It copies a prompt to your clipboard for you to manually paste into an LLM (ChatGPT/Claude). No data is sent automatically.

---

## 🕹️ Command Bridge Features

### 1. The Workspace 🛸
The interface is split into two primary consoles:
* **BRIDGE_COMMAND (Active):** Your live workspace.
    * **⚗ WORK:** Professional operations and alchemy.
    * **🐾 DANTE_QUARTERS:** Personal tasks, guarded by your loyal Co-Pilot, Dante.
* **BRIDGE_ARCHIVES (History):** A log of completed missions.
    * **Time-Filtering:** Instantly filter archives by `[ 2 WEEKS ]`, `[ 1 MONTH ]`, or `[ CUSTOM ]` ranges.

### 2. Task Operations
* **Tree Structure:** Infinite nesting (Main Task $\rightarrow$ Sub-task $\rightarrow$ Sub-sub-task).
* **[ ▶ ] Toggle:** Expand or collapse complex project trees to reduce visual clutter.
* **[ KILL ]:** Instantly mark a task as completed/neutralized.
* **[ i ] Data Logs:** Attach detailed text notes to any task. The icon turns **Green** if intelligence is stored inside.
* **Flush Protocol:** The `[ FLUSH TASK ]` button clears completed items from the Bridge and moves them to the Archives.

### 3. AI Intelligence Reports 🧠
* **Global Report:** Generate a summary of all Work/Personal progress for the week.
* **Scoped Project Report:** Open the menu `≡` on any specific task and click `[ GENERATE AI REPORT ]`. This recursively fetches that task, all its children, and **all attached notes** to generate a specific status update prompt for ChatGPT/Claude.

---

## 🌌 Cosmic Odometry (Gamification)

The application now tracks your productivity as physical distance traveled through the universe.

### 1. The Mechanics
* **Fuel Source:** Completed tasks and focus time drive the ship engines.
* **The Crew:**
    * **Commander:** You (The User).
    * **Navigator:** Dante (The Dog).

### 2. The Lore System (`lore_data.json`)
The application loads a dynamic storyline from an external JSON file. As your distance increases, the system automatically detects your location:
* **Milestones:** Passing real celestial markers triggers special logs (e.g., *Leaving Earth Orbit*, *The Moon*, *Mars Colony*, *Voyager 1*).
* **Mission Logs:** Dynamic updates on the dashboard reflecting your current sector.
* **Idle Chatter:** Random status logs from Dante (e.g., *"Sensors detect treat-shaped asteroids"*).

---

## 🛠️ Tech Stack & Structure

* **Language:** Python 3.x
* **GUI:** CustomTkinter
* **Database:** SQLite (Auto-saves all tasks and history)
* **Data Format:** JSON (Lore and configuration)

**File Structure:**
```text
├── main.py             # Entry point
├── database.py         # SQLite handler (Robust Error Handling)
├── gamification.py     # Cosmic distance & Dynamic Path Loading
├── lore_data.json      # The Story, Planets, and Dante's dialogue
├── check_json.py       # Debugging tool for JSON
└── requirements.txt    # Dependencies
