import serial
import time
import configparser
import subprocess
from pynput.keyboard import Controller as KeyboardController
from pynput.keyboard import Key

# Configuration
config = configparser.ConfigParser()
config.read('config.ini')
target_os = config['general']['os'].strip().lower()
port = config['general']['port']

# Initialize
keyboard = KeyboardController()
ser = serial.Serial(port, 9600, timeout=0.1)
time.sleep(2)  # Wait for Arduino

# Volume control state tracking
LAST_VOLUME = 50  # Initialize with default volume
VOLUME_THRESHOLD = 5
LAST_UPDATE = 0
UPDATE_DELAY = 0  # Seconds between volume updates

# Mute state tracking
PRE_MUTE_VOLUME = None  # Stores volume level before muting
IS_MUTED = False  # Track mute state manually

def get_current_volume():
    """Get current volume percentage (0-100)"""
    if target_os == "macos":
        result = subprocess.run(
            ['osascript', '-e', 'output volume of (get volume settings)'],
            capture_output=True, text=True
        )
        try:
            return int(result.stdout.strip())
        except:
            return 50  # Default if reading fails
    elif target_os == "linux":
        try:
            result = subprocess.run(
                ["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"],
                capture_output=True, text=True
            )
            # Output looks like: "Volume: 0.50 [MUTED]"
            vol_str = result.stdout.strip().split()[1]
            return int(float(vol_str) * 100)
        except:
            return 50
    return 50  # Default for other OS

def set_volume(percent):
    """Set volume to specific percentage"""
    global LAST_VOLUME
    percent = max(0, min(100, percent))  # Clamp to 0-100
    if target_os == "macos":
        script = f'set volume output volume {percent}'
        subprocess.run(['osascript', '-e', script], check=True)
    elif target_os == "linux":
        vol_float = percent / 100.0  # Convert to 0.0-1.0
        subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{vol_float:.2f}"], check=True)
    LAST_VOLUME = percent

def toggle_mute():
    """Toggle mute using wpctl"""
    if target_os == "macos":
        global PRE_MUTE_VOLUME, IS_MUTED
        if IS_MUTED:
            if PRE_MUTE_VOLUME is not None:
                set_volume(PRE_MUTE_VOLUME)
            IS_MUTED = False
            print(f"Unmuted - restored volume to {PRE_MUTE_VOLUME}")
        else:
            PRE_MUTE_VOLUME = get_current_volume()
            set_volume(0)
            IS_MUTED = True
            print(f"Muted - saved volume {PRE_MUTE_VOLUME}")
    elif target_os == "linux":
        subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"], check=True)

def toggle_mic_mute():
    """Toggle mic mute using wpctl"""
    if target_os == "linux":
        subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", "toggle"], check=True)

def handle_volume(value):
    """Simplified volume handling with direct mapping"""
    global LAST_VOLUME, LAST_UPDATE
    current_time = time.time()
    
    # Direct linear mapping (0-255 → 0-100)
    percent = int((value / 255) * 100)
    percent = max(0, min(100, percent))  # Clamp to valid range
    
    # Only update if changed beyond threshold
    if abs(percent - LAST_VOLUME) >= VOLUME_THRESHOLD or current_time - LAST_UPDATE >= UPDATE_DELAY:
        set_volume(percent)
        LAST_VOLUME = percent
        LAST_UPDATE = current_time
        

def focus_app(name):
    """Bring application to foreground with improved Linux support"""
    if target_os == "macos":
        subprocess.run(["osascript", "-e", f'tell application "{name}" to activate'], check=False)

    elif target_os == "linux":
        subprocess.run(["wmctrl", "-a", name, "-x"], check=False)

def press_key(key):
    """Press and release a media key"""
    keyboard.press(key)
    keyboard.release(key)

def handle_command(cmd):
    """Handle all button commands"""
    print(f"Executing command: {cmd}")
    
    if cmd == "PLAY":
        press_key(Key.media_play_pause)
    elif cmd == "PREV":
        press_key(Key.media_previous)
    elif cmd == "NEXT":
        press_key(Key.media_next)
    elif cmd == "MUTE":
        toggle_mute()
    elif cmd == "MICMUTE":
        toggle_mic_mute()
    elif cmd == "SLEEP":
        if target_os == "macos":
            subprocess.run(["pmset", "sleepnow"])
        elif target_os == "linux":
            subprocess.run(["systemctl", "suspend"])
    elif cmd == "DISCORD":
        focus_app("Discord")
    elif cmd == "FIREFOX":
        focus_app("Firefox")

# Main loop
try:
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            if not line:
                continue

            if ":" in line:  # Potentiometer value
                key, val = line.split(":")
                val = int(val)
                if key == "VOL":
                    handle_volume(val)
                elif key == "MIC" and target_os == "linux":
                    percent = int(val / 255 * 100)
                    subprocess.run(["pactl", "set-source-volume", "@DEFAULT_SOURCE@", f"{percent}%"])
            else:  # Button command
                handle_command(line)
        
        time.sleep(0.01)

except KeyboardInterrupt:
    print("Program stopped.")
finally:
    ser.close()
