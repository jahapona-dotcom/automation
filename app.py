import time
import os
from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

app = Flask(__name__)

def run_auto_commenter(email, password, comment_text, comments_per_page=150, max_pages=10):
    options = webdriver.ChromeOptions()
    
    # Headless Environment Options for Render/Docker
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    
    # Chromium binary path in Docker
    options.binary_location = "/usr/bin/chromium"

    driver = webdriver.Chrome(options=options)
    
    try:
        # ১. ফেসবুকে প্রবেশ ও লগইন
        driver.get("https://www.facebook.com/")
        time.sleep(3)

        email_element = driver.find_element(By.ID, "email")
        pass_element = driver.find_element(By.ID, "pass")
        
        email_element.send_keys(email)
        pass_element.send_keys(password)
        pass_element.send_keys(Keys.RETURN)
        
        time.sleep(7)

        # লুপ পরিচালনা (সর্বোচ্চ ১০টি পেজ পর্যন্ত)
        for page_index in range(1, max_pages + 1):
            try:
                profile_btn = driver.find_element(By.XPATH, '//div[@aria-label="Your profile" or @aria-label="Controls and status"]')
                profile_btn.click()
                time.sleep(2)

                try:
                    see_all = driver.find_element(By.XPATH, '//*[contains(text(), "See all profiles") or contains(text(), "সব প্রোফাইল দেখুন")]')
                    see_all.click()
                    time.sleep(2)
                except Exception:
                    pass

                page_items = driver.find_elements(By.XPATH, '//div[@role="button" or @role="link"]')
                if page_index < len(page_items):
                    page_items[page_index].click()
                    time.sleep(6)
                else:
                    break
            except Exception as e:
                print(f"Page switch error: {e}")
                break

            comments_done_in_current_page = 0
            while comments_done_in_current_page < comments_per_page:
                block_warnings = driver.find_elements(By.XPATH, '//*[contains(text(), "Action Blocked") or contains(text(), "You can\'t comment")]')
                if block_warnings:
                    driver.quit()
                    return False, "YOUR COMMENT HAS BEEN BLOCKED! কমেন্ট ব্লক হওয়ার কারণে প্রোগ্রাম বন্ধ করা হয়েছে।"

                comment_boxes = driver.find_elements(By.XPATH, '//div[@role="textbox" and contains(@aria-label, "Comment")]')
                
                for box in comment_boxes:
                    if comments_done_in_current_page >= comments_per_page:
                        break
                    try:
                        driver.execute_script("arguments[0].scrollIntoView(true);", box)
                        time.sleep(1)
                        
                        box.click()
                        box.send_keys(comment_text)
                        time.sleep(1.5)
                        box.send_keys(Keys.RETURN)
                        
                        comments_done_in_current_page += 1
                        time.sleep(2)
                    except Exception:
                        continue

                driver.execute_script("window.scrollBy(0, 800);")
                time.sleep(3)

        driver.quit()
        return True, "প্রক্রিয়াটি সফলভাবে সম্পন্ন হয়েছে।"

    except Exception as e:
        driver.quit()
        return False, f"ত্রুটি ঘটেছে: {str(e)}"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start-automation", methods=["POST"])
def start_automation():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    comment = data.get("comment")

    if not email or not password or not comment:
        return jsonify({"success": False, "message": "সবগুলো ফিল্ড সঠিকভাবে পূরণ করুন!"})

    success, message = run_auto_commenter(email, password, comment)
    return jsonify({"success": success, "message": message})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)