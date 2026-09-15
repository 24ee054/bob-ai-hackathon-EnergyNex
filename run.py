import os
import sys
import time
import webbrowser
import subprocess
import threading

def open_browser():
    time.sleep(2)
    url = "http://127.0.0.1:8000/"
    print(f"\n[OK] Opening G-EnergySense AI Dashboard at {url}...")
    webbrowser.open(url)

def main():
    print("=" * 65)
    print("⚡ G-EnergySense AI — Gujarat State Grid Command Center")
    print("   IBM Bob AI Innovation Hackathon 2026")
    print("=" * 65)
    print("\n[1/2] Checking database and running migrations...")
    os.system(f'"{sys.executable}" manage.py migrate --noinput')
    
    print("\n[2/2] Starting server at http://127.0.0.1:8000/...")
    threading.Thread(target=open_browser, daemon=True).start()
    os.system(f'"{sys.executable}" manage.py runserver 127.0.0.1:8000')

if __name__ == "__main__":
    main()
