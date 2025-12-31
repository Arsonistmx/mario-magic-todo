# 🚀 TEMagic_Console (v1.2)

**TEMagic_Console** is a high-performance, dark-mode terminal interface for task management. It combines a "Matrix/Sci-Fi" aesthetic with deep project tracking, recursive sub-tasking, and AI-powered status reporting.

Designed for the "Commander" who needs to manage **Work Operations** and **Personal Quarters** from a single command bridge.

---

## 🕹️ Current Features

### 1. The Command Bridge 🛸
The interface is split into two primary consoles:
* **BRIDGE_COMMAND (Active):** Your live workspace.
    * **⚗ WORK:** Professional operations and alchemy.
    * **🐾 DANTE_QUARTERS:** Personal tasks, guarded by your loyal Co-Pilot, Dante.
* **BRIDGE_ARCHIVES (History):** A log of completed missions.
    * **Time-Filtering:** Instantly filter archives by `[ 2 WEEKS ]`, `[ 1 MONTH ]`, or `[ CUSTOM ]` ranges to keep the view clean.

### 2. Task Operations
* **Tree Structure:** Infinite nesting. (Main Task $\rightarrow$ Sub-task $\rightarrow$ Sub-sub-task).
* **[ ▶ ] Toggle:** Expand or collapse complex project trees to reduce visual clutter.
* **[ KILL ]:** Instantly mark a task as completed/neutralized.
* **[ i ] Data Logs:** Attach detailed text notes to any task. The icon turns **Green** if intelligence is stored inside.
* **Flush Protocol:** The `[ FLUSH TASK ]` button clears completed items from the Bridge and moves them to the Archives.

### 3. AI Intelligence Reports 🧠
* **Global Report:** Generate a summary of all Work/Personal progress for the week.
* **Scoped Project Report:** Open the menu `≡` on any specific task and click `[ GENERATE AI REPORT ]`. This recursively fetches that task, all its children, and **all attached notes** to generate a specific status update prompt for ChatGPT/Claude.

---

## ⚙️ Installation

1.  **Clone/Create Project Folder:**
    ```bash
    mkdir TEMagic_Console
    cd TEMagic_Console
    ```

2.  **Create Virtual Environment:**
    ```bash
    python -m venv venv
    # Windows: venv\Scripts\activate
    # Mac/Linux: source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install customtkinter
    ```

4.  **Run the Console:**
    ```bash
    python main.py
    ```

---

## 🔮 Roadmap: The "Log Machine" Expansion

The next major update will introduce **Gamification and Lore** to turn productivity into a cosmic journey.

### 🚀 Upcoming Module: COSMIC_ODOMETRY
We are turning the console into a spaceship navigation log.

**1. The Mechanics (Time = Distance)**
* The application will track total focus time across all tasks.
* **Conversion Rate:** `1 Second of Focus = 100 KM traveled`.
* **The Crew:**
    * **Commander:** You (The User).
    * **Navigator:** Dante (The Dog).

**2. Milestones & Destinations**
As we accrue "Distance" (Time Spent), the console will unlock arrival messages at celestial bodies:
* *Leaving Earth Orbit*
* *Arrival: The Moon*
* *Mars Colony*
* *Jupiter Station*
* *The Edge of the Solar System*
* *Deep Space / Alpha Centauri*

**3. Console Atmosphere & "Navigator Dante" Interactions**
* **Boot Sequence:** A randomized "Welcome Commander" message upon opening the app.
* **Flavor Text:** Random status logs from Dante will appear in the header or as toast notifications:
    * *"Navigator Dante reports: Sensors detect treat-shaped asteroids."*
    * *"Engine efficiency at 98%. Tail wagging sensors active."*
    * *"Alert: Walkies required in Sector 7."*

> *"The journey is long, but the company is good."*
