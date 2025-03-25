import requests
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
import subprocess
import time
import re
import os

banner = r"""
  _____     _     _       ____  _                
 |  ___| __(_) __| | __ _| __ )| | __ _ _______  
 | |_ | '__| |/ _` |/ _` |  _ \| |/ _` |_  / _ \ 
 |  _|| |  | | (_| | (_| | |_) | | (_| |/ /  __/ 
 |_|  |_|  |_|\__,_|\__,_|____/|_|\__,_/___\___| 
                                                 
============= Fridra Automation =============
"""

print(banner)

### -------------------------
### FETCH SCRIPTS
### -------------------------
def fetch_scripts(page):
    """Fetches script URLs from CodeShare Frida pages."""
    url = f"https://codeshare.frida.re/browse?page={page}"
    response = requests.get(url)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    script_links = []

    for h2_tag in soup.find_all('h2'):
        a_tag = h2_tag.find('a')
        if a_tag and 'href' in a_tag.attrs:
            script_url = a_tag['href']
            script_links.append(script_url)

    return script_links


def search_scripts(keyword, end_page=20):
    """Searches scripts by keyword dynamically and displays related URLs."""
    urls = []
    print(f"\n[+] Searching for scripts with '{keyword}'...\n")

    try:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(fetch_scripts, i) for i in range(1, end_page + 1)]

            for future in futures:
                script_urls = future.result()
                keyword_scripts = [url for url in script_urls if keyword.lower() in url.lower()]
                urls.extend(keyword_scripts)

        if not urls:
            print("\n[-] No matching scripts found.")
            return []

        print("\n[+] Found Scripts:")
        script_info = []

        for idx, url in enumerate(urls, start=1):
            project_name = url.split('/')[-2]  # Extract project name from URL
            script_info.append((project_name, url))
            print(f"{idx}. Project: {project_name}\n   URL: {url}\n")

        return script_info

    except KeyboardInterrupt:
        print("\n[-] Terminated by user.")
        return []


### -------------------------
### EXECUTE SCRIPTS
### -------------------------
def execute_script(script_url, package_name, timeout=120):
    """Executes a Frida script from CodeShare with a timeout."""
    
    # Extracting script name
    match = re.search(r'/@(.+?)/(.+)', script_url)
    
    if match:
        script_name = f"{match.group(1)}/{match.group(2)}"
    else:
        print("\n[❌] Invalid script URL format.")
        return False

    print(f"\n[+] Executing: {script_name} on {package_name}")
    command = f"frida -U --codeshare {script_name} -f {package_name}"

    return execute_command(command, timeout)


def execute_local_script(script_path, package_name, timeout=120):
    """Executes a local Frida script."""
    
    if not os.path.isfile(script_path):
        print("\n[❌] Local script not found.")
        return False

    print(f"\n[+] Executing Local Script: {script_path} on {package_name}")
    command = f"frida -U -f {package_name} -l {script_path}"

    return execute_command(command, timeout)


def execute_command(command, timeout):
    """Executes a Frida command with a timeout and handles errors."""
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        start_time = time.time()

        while True:
            if process.poll() is not None:  # Process completed
                if process.returncode == 0:
                    print("\n[✅] Hooking Successful.")
                    return True
                else:
                    print("\n[❌] Hooking Failed.")
                    return False

            # Timeout handling
            if time.time() - start_time > timeout:
                process.terminate()
                print("\n[-] Hooking timed out. Returning to main menu.")
                return False

            time.sleep(1)

    except Exception as e:
        print(f"\n[!] Error: {e}")
        return False


### -------------------------
### VALIDATE CUSTOM CODESHARE URL
### -------------------------
def validate_codeshare_url(url):
    """Validates and extracts the script name from a CodeShare URL."""
    pattern = r'^https://codeshare\.frida\.re/@[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+/?$'

    if re.match(pattern, url):
        return True
    else:
        print("\n[❌] Invalid CodeShare URL format.")
        return False


### -------------------------
### MAIN FUNCTION
### -------------------------
def main():
    # Step 1: Ask for the package name first
    package_name = input("\n[?] Enter the target package name: ").strip()

    if not package_name:
        print("[-] Invalid package name.")
        return

    while True:
        # Step 2: Choose execution type
        print("\n[1] Custom URL")
        print("[2] Local Script")
        print("[3] CodeShare Search")
        print("[4] Exit")
        
        exec_type = input("\n[?] Choose execution type (1/2/3/4): ").strip()

        if exec_type == '4':
            print("\n[✅] Exiting... Goodbye! Happy Hacking!")
            break

        success = False

        ### ✅ Custom URL Execution
        if exec_type == '1':
            custom_url = input("\n[?] Enter the custom CodeShare URL: ").strip()

            if validate_codeshare_url(custom_url):
                print("\n[+] Executing custom script...")
                success = execute_script(custom_url, package_name)

        ### ✅ Local Script Execution
        elif exec_type == '2':
            local_script_path = input("\n[?] Enter the local script path (e.g., /path/to/script.js): ").strip()

            if os.path.isfile(local_script_path):
                success = execute_local_script(local_script_path, package_name)
            else:
                print("\n[❌] Invalid local script path.")

        ### ✅ CodeShare Search Execution with Dynamic Input
        elif exec_type == '3':
            search_term = input("\n[?] Enter the search keyword: ").strip()

            if not search_term:
                print("\n[❌] Invalid search term.")
                continue

            scripts = search_scripts(search_term)

            if not scripts:
                continue

            while True:
                try:
                    choice = int(input("\n[?] Enter the script number to execute (0 to exit): "))

                    if choice == 0:
                        print("Exiting search...")
                        break

                    if 1 <= choice <= len(scripts):
                        _, script_url = scripts[choice - 1]
                        success = execute_script(script_url, package_name)
                        if success:
                            break
                except ValueError:
                    print("[-] Invalid input. Please enter a number.")
                except KeyboardInterrupt:
                    print("\n[-] Terminated by user.")
                    break

        if success:
            print("\n[✅] Execution successful.")
        else:
            print("\n[❌] Execution failed. Returning to the menu...")


if __name__ == '__main__':
    main()
