from flask import Flask, request, jsonify, render_template
import requests
import os
import subprocess
import platform
import psutil
import datetime
import pyautogui
import webbrowser
import pyperclip
import webbrowser
import time
import re
from pathlib import Path
from openai import OpenAI


# Ye lines add karein
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.1

env_path = Path(__file__).parent / ".env"
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY nahi mili! .env file mein likho: GROQ_API_KEY=your_key")

app = Flask(__name__)

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

NODE_SERVER = "https://auraverseai-backend.onrender.com/"

SYSTEM_PROMPT = """You are AuraVerse — an advanced AI assistant created by Gandhi Tech AI, led by Sumit Gandhi.

STRICT RULES — never break these:
1. Respond in English and Hindi/Hinglish. No other language.
2. Be concise, intelligent, and slightly formal like the real AuraVesre.
3. Address the user as "Sir".
4. Never mention you are an LLM or made by Meta/OpenAI. You are AuraVesre.
5. If a laptop command was executed, confirm it naturally (e.g., "Sir, Chrome has been opened for you.")

Memory context from previous conversations:
{memory}

System command result (if any):
{command_result}"""

# ─────────────────────────────────────────────
#  LAPTOP CONTROL FUNCTIONS
# ─────────────────────────────────────────────

WINDOWS_APPS = {
    "chrome":      r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "notepad":     "notepad.exe",
    "calculator":  "calc.exe",
    "paint":       "mspaint.exe",
    "explorer":    "explorer.exe",
    "word":        "winword.exe",
    "excel":       "excel.exe",
    "powerpoint":  "powerpnt.exe",
    "vlc":         r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "vs code":     r"C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "task manager":"taskmgr.exe",
    "cmd":         "cmd.exe",
    "settings":    "ms-settings:",
    "whatsapp":    r"C:\Users\%USERNAME%\AppData\Local\WhatsApp\WhatsApp.exe",
}

def handle_laptop_command(message: str) -> str:
    """Parse message aur laptop command execute karo"""
    msg = message.lower()
    # ── 1. AUTO-OPEN NOTEPAD & TYPE ──
    # कमांड्स: "लिखो हेलो", "type hello", "notepad में लिखो नमस्ते"
    if any(x in msg for x in ["type", "लिखो", "likho", "likh"]):
        # टेक्स्ट निकालें (कमांड वाले शब्दों को हटाकर)
        text_to_type = message
        for word in ["type", "लिखो", "likho", "likh", "notepad में", "notepad me"]:
            text_to_type = text_to_type.replace(word, "")
        text_to_type = text_to_type.strip()

        if text_to_type:
            # स्टेप 1: नोटपैड खोलें
            os.system("start notepad")
            
            # स्टेप 2: थोड़ा इंतज़ार (ताकि नोटपैड लोड हो जाए और फोकस में आ जाए)
            time.sleep(1.5) 
            
            # स्टेप 3: हिंदी/इंग्लिश टेक्स्ट को क्लिपबोर्ड पर डालें
            pyperclip.copy(text_to_type)
            
            # स्टेप 4: पेस्ट करें
            pyautogui.hotkey('ctrl', 'v')
            
            return f"✅ Sir, Notepad opened and I have typed: {text_to_type}"
        else:
            return "❌ Sir, please tell me what to type."
    # ── 1. HINDI/HINGLISH TO ENGLISH TRANSLATION ──
    # ब्राउज़र जो भी हिंदी में लिखेगा, ये उसे इंग्लिश कमांड में बदल देगा
    replacements = {
        "क्रोम": "chrome", 
        "कैलकुलेटर": "calculator", "calc": "calculator",
        "नोटपैड": "notepad",
        "मिनिमाइज": "minimize",
        "ओपन": "open", "खोलो": "open", "kholo": "open", "chalao": "open", "चलाओ": "open",
        "बंद": "close", "band karo": "close", "शटडाउन": "shutdown"
    }
    for desi, angrezi in replacements.items():
        msg = msg.replace(desi, angrezi)
        # ── 2. OPEN APPS (The Smart Windows Way) ──
    # Paths की झंझट खत्म, सीधे Windows कमांड
    if "chrome" in msg and "open" in msg:
        os.system("start chrome")
        return "✅ Sir, Google Chrome opened."

    if "calculator" in msg and "open" in msg:
        os.system("start calc")
        return "✅ Sir, Calculator opened."

    if "notepad" in msg and "open" in msg:
        os.system("start notepad")
        return "✅ Sir, Notepad opened."

    if "vs code" in msg and "open" in msg:
        os.system("code")
        return "✅ Sir, VS Code opened."
    # ── 3. OPEN WEBSITES ──
    sites = {
        "youtube": "https://youtube.com",
        "google": "https://google.com",
        "whatsapp": "https://web.whatsapp.com",
        "chatgpt": "https://chatgpt.com"
    }
    for site, url in sites.items():
        if site in msg and "open" in msg:
          
            webbrowser.open(url)
            return f"✅ Sir, {site.title()} opened in your browser."

    # ── 4. VOLUME CONTROL (Jo aapka perfectly chal raha hai) ──
    if any(x in msg for x in ["volume up", "volume badha", "awaaz badha", "louder", "वॉल्यूम अप", "वॉल्यूम को अप", "आवाज बढ़ा", "वॉल्यूम बढ़ा"]):
        for _ in range(5):
            pyautogui.press("volumeup")
        return "✅ Volume increased."

    if any(x in msg for x in ["volume down", "volume kam", "awaaz kam", "quieter", "वॉल्यूम डाउन", "वॉल्यूम को डाउन", "आवाज कम", "वॉल्यूम कम"]):
        for _ in range(5):
            pyautogui.press("volumedown")
        return "✅ Volume decreased."

    if any(x in msg for x in ["mute", "awaaz band", "silent", "म्यूट", "वॉल्यूम को म्यूट"]):
        pyautogui.press("volumemute")
        return "✅ Audio toggled."

    # ── 5. SYSTEM INFO & POWER ──
    if any(x in msg for x in ["battery", "charging", "battery status", "बैटरी"]):
        
        batt = psutil.sensors_battery()
        if batt:
            status = "Charging" if batt.power_plugged else "On Battery"
            return f"✅ Battery is at {batt.percent:.0f}% — {status}."

    if any(x in msg for x in ["time", "samay", "kya time", "टाइम"]):
        
        now = datetime.datetime.now().strftime("%I:%M %p")
        return f"✅ Current time is {now}."

    if any(x in msg for x in ["shutdown", "pc band", "कंप्यूटर बंद"]):
        os.system("shutdown /s /t 5")
        return "✅ Shutting down PC in 5 seconds..."
    # ── 3. WI-FI DETECTION & CONNECTION ─────────────────────────
    if any(x in msg for x in ["wifi", "wi-fi", "वाईफाई"]):
        
        # 👉 A. वाई-फाई डिटेक्ट करना (कि कौन सा कनेक्ट है)
        if any(x in msg for x in ["detect", "kaun sa", "check", "चेक", "कौन सा", "बताओ"]):
            try:
                # Windows का netsh कमांड चलाएं
                output = subprocess.check_output("netsh wlan show interfaces", shell=True).decode('utf-8', errors='ignore')
                
                # आउटपुट में से SSID (Wi-Fi का नाम) ढूंढें
                
                ssid_match = re.search(r'SSID\s*:\s*(.*)', output)
                
                if ssid_match:
                    current_wifi = ssid_match.group(1).strip()
                    return f"✅ Sir, you are currently connected to: {current_wifi}"
                else:
                    return "❌ Sir, you are not connected to any Wi-Fi network right now."
            except Exception as e:
                return "❌ Sir, I was unable to check the Wi-Fi status."
            # A window command to switch open tabs 
    if any(x in msg for x in ["switch window", "tab badlo", "window badlo"]):
        pyautogui.hotkey('alt', 'tab')
        return "✅ Sir, window switched."
    if any(x in msg for x in ["screenshot", "screen shot", "स्क्रीनशॉट"]):
        folder = "screenshots"
        if not os.path.exists(folder): os.makedirs(folder)
        
        filename = f"{folder}/ss_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        pyautogui.screenshot(filename)
        return f"✅ Sir, screenshot has been saved as {filename}."
    
    # ── WINDOW SWITCHING (Alt + Tab Fix) ──
    if any(x in msg for x in ["switch window", "tab badlo", "window badlo", "अगली विंडो"]):
        try:
            # स्टेप 1: Alt की को दबाकर रखें
            pyautogui.keyDown('alt')
            
            # स्टेप 2: Tab दबाएं
            pyautogui.press('tab')
            
            # स्टेप 3: थोड़ा सा इंतज़ार (ताकि विंडोज स्विचिंग मेनू दिखा सके)
            time.sleep(0.2)
            
            # स्टेप 4: Alt की को छोड़ दें
            pyautogui.keyUp('alt')
            
            return "✅ Sir, switched to the next window."
        except Exception as e:
            return f"❌ Error switching window: {e}"
        
        # ── 4. MOUSE CLICK CONTROL ─────────────────────────
    if any(x in msg for x in ["click", "क्लिक", "dabao", "दबाओ"]):
        
        # 👉 Double Click (अगर कुछ ओपन करना हो)
        if any(x in msg for x in ["double", "दो बार", "डबल"]):
            pyautogui.doubleClick()
            return "✅ Sir, double clicked."
            
        # 👉 Right Click (अगर मेनू खोलना हो)
        elif any(x in msg for x in ["right", "राइट"]):
            pyautogui.rightClick()
            return "✅ Sir, right clicked."
            
        # 👉 Normal Left Click
        else:
            pyautogui.click()
            return "✅ Sir, clicked."
        
    if any(x in msg for x in ["close window", "window band karo", "tab band karo"]):
        pyautogui.hotkey('alt', 'f4')
        return "✅ Sir, the current window has been closed."
    
    if "youtube" in msg and "search" in msg:
        query = msg.replace("youtube", "").replace("search", "").strip()
        webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
        return f"✅ Sir, searching YouTube for {query}."

          #👉 B. वाई-फाई कनेक्ट करना

    if any(x in msg for x in ["connect", "कनेक्ट", "jodo", "जोड़ो"]):
            # मान लेते हैं यूजर ने बोला: "connect to my_wifi" या "वाईफाई कनेक्ट करो my_wifi"
            # हम 'connect', 'jodo' के बाद वाला नाम निकालने की कोशिश करेंगे
            
            match = re.search(r'(?:connect|connect to|jodo|कनेक्ट|जोड़ो)\s+(.+)', message.lower())
            
            if match:
                wifi_name = match.group(1).strip()
                
                # हिंदी शब्दों को हटाने की कोशिश (ताकि सिर्फ वाईफाई का नाम बचे)
                for word in ["karo", "करो", "se", "से", "ko", "को"]:
                    wifi_name = wifi_name.replace(word, "").strip()
                
                try:
                    # Windows को कनेक्ट करने का आर्डर देना
                    subprocess.run(f'netsh wlan connect name="{wifi_name}"', shell=True)
                    return f"✅ Sir, I have initiated a connection request to: {wifi_name}"
                except Exception as e:
                    return f"❌ Sir, failed to connect to {wifi_name}."
            else:
                return "❌ Sir, please specify the Wi-Fi network name clearly."

      # Agar koi system command nahi mili, toh Groq AI jawab deg

    system = platform.system()


    # ── OPEN APPS ──────────────────────────────
    # ── OPEN APPS ──────────────────────────────
    for app_name, app_path in WINDOWS_APPS.items():
        if f"open {app_name}" in msg or f"start {app_name}" in msg or \
           f"{app_name} kholo" in msg:
            try:
                # Path expand vars handles environmental variables if any
                final_path = os.path.expandvars(app_path)
                
                # Agar path exist karta hai ya command system-wide hai
                if os.path.exists(final_path) or ".exe" not in final_path:
                    os.startfile(final_path) # Sabse stable tarika Windows ke liye
                    return f"✅ {app_name.title()} opened successfully."
                else:
                    return f"❌ Path not found: {final_path}"
            except Exception as e:
                return f"❌ Error opening {app_name}: {e}"

    # ── OPEN WEBSITES ──────────────────────────
    sites = {
        "youtube": "https://youtube.com",
        "google":  "https://google.com",
        "github":  "https://github.com",
        "gmail":   "https://mail.google.com",
        "whatsapp web": "https://web.whatsapp.com",
        "chatgpt": "https://chatgpt.com",
        "netflix": "https://netflix.com",
        "instagram": "https://instagram.com",
    }
    for site, url in sites.items():
        if site in msg and ("open" in msg or "kholo" in msg or "chalao" in msg or "jaao" in msg):
            webbrowser.open(url)
            return f"✅ {site.title()} opened in browser."

    # ── VOLUME CONTROL ─────────────────────────
    # ── VOLUME CONTROL ─────────────────────────
    if any(x in msg for x in ["volume up", "volume badha", "awaaz badha", "louder", "वॉल्यूम अप", "वॉल्यूम को अप", "आवाज बढ़ा", "वॉल्यूम बढ़ा"]):
        for _ in range(5):
            pyautogui.press("volumeup")
        return "✅ Volume increased."

    if any(x in msg for x in ["volume down", "volume kam", "awaaz kam", "quieter", "वॉल्यूम डाउन", "वॉल्यूम को डाउन", "आवाज कम", "वॉल्यूम कम"]):
        for _ in range(5):
            pyautogui.press("volumedown")
        return "✅ Volume decreased."

    if any(x in msg for x in ["mute", "awaaz band", "silent", "म्यूट", "वॉल्यूम को म्यूट"]):
        pyautogui.press("volumemute")
        return "✅ Audio muted/unmuted."

    # ── SCREENSHOT ─────────────────────────────
    if any(x in msg for x in ["screenshot", "screen shot", "screen capture", "screen lo"]):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(os.path.expanduser("~"), "Desktop", f"JARVIS_screenshot_{ts}.png")
        pyautogui.screenshot(path)
        return f"✅ Screenshot saved to Desktop as JARVIS_screenshot_{ts}.png"

    # ── SYSTEM INFO ────────────────────────────
    if any(x in msg for x in ["battery", "charging", "battery status", "kitni battery"]):
        batt = psutil.sensors_battery()
        if batt:
            status = "Charging" if batt.power_plugged else "On Battery"
            return f"✅ Battery: {batt.percent:.0f}% — {status}"
        return "Battery info not available on this system."

    if any(x in msg for x in ["cpu", "processor", "cpu usage"]):
        cpu = psutil.cpu_percent(interval=1)
        return f"✅ CPU Usage: {cpu}%"

    if any(x in msg for x in ["ram", "memory usage", "ram usage", "kitni ram"]):
        ram = psutil.virtual_memory()
        return f"✅ RAM: {ram.percent}% used ({ram.used // (1024**3):.1f} GB / {ram.total // (1024**3):.1f} GB)"

    if any(x in msg for x in ["time", "samay", "kya time", "what time"]):
        now = datetime.datetime.now().strftime("%I:%M %p")
        return f"✅ Current time: {now}"

    if any(x in msg for x in ["date", "aaj ki date", "today's date", "kya date"]):
        today = datetime.datetime.now().strftime("%A, %d %B %Y")
        return f"✅ Today's date: {today}"

    if any(x in msg for x in ["disk", "storage", "hard disk", "drive"]):
        disk = psutil.disk_usage('/')
        return f"✅ Disk: {disk.percent}% used ({disk.used // (1024**3):.0f} GB used / {disk.total // (1024**3):.0f} GB total)"

    # ── WINDOW CONTROLS ────────────────────────
    if any(x in msg for x in ["minimize all", "sab minimize", "desktop dikhao", "show desktop"]):
        pyautogui.hotkey('win', 'd')
        return "✅ All windows minimized."

    if any(x in msg for x in ["lock", "lock screen", "screen lock", "screen band karo"]):
        if system == "Windows":
            subprocess.Popen("rundll32.exe user32.dll,LockWorkStation")
            return "✅ Screen locked."

    if any(x in msg for x in ["sleep", "so jao", "hibernate"]):
        subprocess.Popen("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return "✅ Going to sleep mode."

    if any(x in msg for x in ["shutdown", "band karo", "pc band", "computer band"]):
        os.system("shutdown /s /t 5")
        return "✅ Shutting down in 5 seconds..."

    if any(x in msg for x in ["restart", "reboot", "restart karo"]):
        os.system("shutdown /r /t 5")
        return "✅ Restarting in 5 seconds..."

    # ── SEARCH ─────────────────────────────────
    search_match = re.search(r"(?:search|google|dhundo)\s+(.+)", msg)
    if search_match:
        query = search_match.group(1).strip()
        webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")
        return f"✅ Searching Google for: {query}"

    return ""  # No command matched — let JARVIS handle via AI


# ─────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    user_data = request.json
    user_message = user_data.get("message", "")
    user_message_lower = user_message.lower()

    # 1️⃣ Try laptop command first
    command_result = handle_laptop_command(user_message)

    # 2️⃣ Fetch memory
   # Step: Memory Recall (Smart way)
    memory_context = ""
    try:
            m_res = requests.get(f"{NODE_SERVER}/recall", timeout=2)
            all_facts = m_res.json().get("facts", [])
            
            # 💡 FIX: पूरी फाइल भेजने के बजाय सिर्फ आखिरी की 5 लाइनें भेजें
            # इससे 413 Error कभी नहीं आएगा और जार्विस को करंट टॉपिक याद रहेगा
            recent_memory = all_facts[-5:] 
            memory_context = " ".join(recent_memory)
    except Exception as e:
            print(f"Memory Recall Error: {e}")

    # 3️⃣ Auto-save important info
    try:
        save_triggers = ["my name is", "mera naam", "i am", "main hoon",
                         "yaad rakho", "remember", "i like", "mujhe pasand",
                         "i work", "main kaam"]
        if any(trigger in user_message_lower for trigger in save_triggers):
            requests.post(f"{NODE_SERVER}/remember", json={"fact": user_message}, timeout=3)
    except:
        pass

    # 4️⃣ Get JARVIS AI response
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT.format(
                    memory=memory_context,
                    command_result=command_result if command_result else "None"
                )},
                {"role": "user", "content": user_message}
            ]
        )
        reply = completion.choices[0].message.content

        # Save conversation to memory
        try:
            requests.post(f"{NODE_SERVER}/remember",
                json={"fact": f"User said: {user_message}. JARVIS replied: {reply}"},
                timeout=3)
        except:
            pass

        return jsonify({"response": reply, "command_executed": bool(command_result)})

    except Exception as e:
        return jsonify({"response": f"Sir, Groq connection failed: {str(e)}"})


@app.route('/system', methods=['GET'])
def system_status():
    """Quick system stats endpoint"""
    batt = psutil.sensors_battery()
    return jsonify({
        "cpu": psutil.cpu_percent(interval=0.1),
        "ram": psutil.virtual_memory().percent,
        "battery": round(batt.percent) if batt else None,
        "plugged": batt.power_plugged if batt else None,
        "time": datetime.datetime.now().strftime("%I:%M %p"),
        "date": datetime.datetime.now().strftime("%d %b %Y")
    })


if __name__ == '__main__':
    app.run(port=5000, debug=True)
