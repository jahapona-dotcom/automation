import time
import os
import json
import threading
import uuid
from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

app = Flask(__name__)

PROFILES_FILE = "profiles.json"
active_threads = {}
stop_flags = {}

def load_profiles_data():
    if not os.path.exists(PROFILES_FILE):
        return []
    with open(PROFILES_FILE, "r") as f:
        return json.load(f)

def save_profiles_data(profiles):
    with open(PROFILES_FILE, "w") as f:
        json.dump(profiles, f, indent=4)

def run_auto_commenter_thread(profile_id, email, password, comment_text):
    stop_flags[profile_id] = False
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.binary_location = "/usr/bin/chromium"

    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get("https://www.facebook.com/")
        time.sleep(3)

        email_element = driver.find_element(By.ID, "email")
        pass_element = driver.find_element(By.ID, "pass")
        
        email_element.send_keys(email)
        pass_element.send_keys(password)
        pass_element.send_keys(Keys.RETURN)
        time.sleep(7)

        # Main Loop with Stop Check
        while not stop_flags.get(profile_id, False):
            # Example automation logic loop
            time.sleep(5)
            
    except Exception as e:
        print(f"Error in profile {profile_id}: {e}")
    finally:
        driver.quit()
        stop_flags.pop(profile_id, None)
        active_threads.pop(profile_id, None)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get-profiles", methods=["GET"])
def get_profiles():
    profiles = load_profiles_data()
    for p in profiles:
        p["status"] = "Running" if p["id"] in active_threads else "Stopped"
    return jsonify(profiles)

@app.route("/add-profile", methods=["POST"])
def add_profile():
    data = request.json
    profiles = load_profiles_data()
    new_profile = {
        "id": str(uuid.uuid4()),
        "name": data.get("name"),
        "email": data.get("email"),
        "password": data.get("password"),
        "comment": data.get("comment")
    }
    profiles.append(new_profile)
    save_profiles_data(profiles)
    return jsonify({"success": True})

@app.route("/start-profile/<profile_id>", methods=["POST"])
def start_profile(profile_id):
    if profile_id in active_threads:
        return jsonify({"success": False, "message": "Already running"})

    profiles = load_profiles_data()
    profile = next((p for p in profiles if p["id"] == profile_id), None)
    if not profile:
        return jsonify({"success": False, "message": "Profile not found"})

    t = threading.Thread(
        target=run_auto_commenter_thread,
        args=(profile["id"], profile["email"], profile["password"], profile["comment"]),
        daemon=True
    )
    active_threads[profile_id] = t
    t.start()
    return jsonify({"success": True})

@app.route("/stop-profile/<profile_id>", methods=["POST"])
def stop_profile(profile_id):
    if profile_id in active_threads:
        stop_flags[profile_id] = True
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Not running"})

@app.route("/delete-profile/<profile_id>", methods=["POST"])
def delete_profile(profile_id):
    if profile_id in active_threads:
        stop_flags[profile_id] = True
    
    profiles = load_profiles_data()
    profiles = [p for p in profiles if p["id"] != profile_id]
    save_profiles_data(profiles)
    return jsonify({"success": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
