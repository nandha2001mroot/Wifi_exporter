import os
import platform
import subprocess
import re

def get_wifi_passwords():
    system = platform.system()
    networks = []

    if system == "Windows":
        # Get list of profiles
        result = subprocess.run(
            ["netsh", "wlan", "show", "profiles"],
            capture_output=True, text=True, shell=True
        )
        ssids = re.findall(r"All User Profile\s*: (.*)", result.stdout)
        for ssid in ssids:
            ssid = ssid.strip()
            # Get password for each
            profile = subprocess.run(
                ["netsh", "wlan", "show", "profile", ssid, "key=clear"],
                capture_output=True, text=True, shell=True
            )
            pwd_match = re.search(r"Key Content\s*: (.*)", profile.stdout)
            password = pwd_match.group(1).strip() if pwd_match else "None"
            networks.append((ssid, password))

    elif system == "Linux":
        try:
            # Get Wi-Fi connections via nmcli (NetworkManager)
            conns = subprocess.check_output(
                ["nmcli", "-g", "name,type", "connection", "show"],
                stderr=subprocess.DEVNULL, text=True
            ).strip().split("\n")
            for line in conns:
                if ":" not in line:
                    continue
                name, ctype = line.split(":", 1)
                if "wifi" in ctype.lower():
                    try:
                        psk = subprocess.check_output(
                            ["nmcli", "-s", "-g", "802-11-wireless-security.psk", "connection", "show", name],
                            stderr=subprocess.DEVNULL, text=True
                        ).strip()
                        networks.append((name, psk or "None"))
                    except:
                        networks.append((name, "Access denied"))
        except FileNotFoundError:
            print("❌ nmcli not found. Only NetworkManager-based Linux is supported.")
            return []

    elif system == "Darwin":  # macOS
        try:
            # Get list of networks
            output = subprocess.check_output(
                ["/usr/sbin/system_profiler", "SPAirPortDataType", "-xml"],
                text=True
            )
            from plistlib import loads
            plist = loads(output.encode())
            networks_list = plist[0]["_items"][0].get("spairport_airport-networks", [])
            for net in networks_list:
                ssid = net.get("spairport_airport-network-ssid")
                if ssid:
                    try:
                        pwd = subprocess.check_output(
                            ["/usr/bin/security", "find-generic-password", "-wa", ssid],
                            stderr=subprocess.DEVNULL, text=True
                        ).strip()
                        networks.append((ssid, pwd))
                    except:
                        networks.append((ssid, "Keychain access denied"))
        except Exception as e:
            print(f"❌ macOS error: {e}")
            return []
    else:
        print(f"❌ Unsupported OS: {system}")
        return []

    return networks

def save_to_file(networks, filename="wifi_passwords.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        for ssid, pwd in networks:
            f.write(f"SSID: {ssid}\nPassword: {pwd}\n{'-'*40}\n\n")
    print(f"✅ Saved to: {os.path.abspath(filename)}")

def main():
    print("📡 Fetching saved Wi-Fi passwords...\n")
    networks = get_wifi_passwords()

    if not networks:
        print("❌ No Wi-Fi networks found.")
        return

    for ssid, pwd in networks:
        print(f"SSID: {ssid}\nPassword: {pwd}\n")

    save = input("\n💾 Save to file? (y/n): ").strip().lower()
    if save == "y":
        filename = input("📁 Enter filename (default: wifi_passwords.txt): ").strip()
        if not filename:
            filename = "wifi_passwords.txt"
        save_to_file(networks, filename)

if __name__ == "__main__":
    main()