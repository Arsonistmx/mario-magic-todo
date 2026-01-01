import json
import random
import os
from datetime import datetime


class FlightComputer:
    def __init__(self, db):
        self.db = db
        self.lore_data = self._load_lore()
        self.km_per_second = 100

        # --- NEW: SHUFFLE BAGS ---
        # We create copies of the lists to pull from, so we can deplete them without ruining the master list.
        self.boot_bag = list(self.lore_data.get("boot_sequence", []))
        self.idle_bag = list(self.lore_data.get("idle_logs", []))

        # Shuffle them immediately upon app start
        random.shuffle(self.boot_bag)
        random.shuffle(self.idle_bag)

    def _load_lore(self):
        try:
            with open("lore_data.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading lore: {e}")
            return {"milestones": [], "boot_sequence": ["SYSTEM FAILURE"], "idle_logs": ["SYSTEM FAILURE"],
                    "holidays": {}}

    def calculate_progress(self):
        total_km = self.db.get_total_distance()
        milestones = self.lore_data.get("milestones", [])

        next_target = None
        for m in milestones:
            if m["distance"] > total_km:
                next_target = m
                break

        if not next_target:
            next_target = {"name": "UNKNOWN_SECTOR", "distance": total_km + 1000000}

        remaining = next_target["distance"] - total_km
        return {
            "total": total_km,
            "target_name": next_target["name"].replace("_", " "),
            "target_dist": next_target["distance"],
            "remaining": remaining
        }

    def convert_seconds_to_km(self, seconds):
        km = int(seconds * self.km_per_second)
        self.db.add_distance(km)
        return km

    def get_console_message(self, event_type="idle"):
        # 1. Check for Holidays
        today = datetime.now().strftime("%m-%d")
        holidays = self.lore_data.get("holidays", {})

        if today in holidays:
            # On boot: Always show holiday
            # On idle: 20% chance to remind you (reduced from 50% to be less annoying)
            if event_type == "boot" or random.random() < 0.20:
                return holidays[today]

        # 2. Smart Selection (Shuffle Bag)
        if event_type == "boot":
            if not self.boot_bag:
                # Refill if empty
                self.boot_bag = list(self.lore_data.get("boot_sequence", []))
                random.shuffle(self.boot_bag)
            return self.boot_bag.pop()

        else:  # idle
            if not self.idle_bag:
                # Refill if empty
                self.idle_bag = list(self.lore_data.get("idle_logs", []))
                random.shuffle(self.idle_bag)
            return self.idle_bag.pop()