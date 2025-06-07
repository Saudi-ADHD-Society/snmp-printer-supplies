import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path
import argparse

# Handle environments without __file__ 
try:
    base_dir = Path(__file__).parent
except NameError:
    base_dir = Path.cwd()

LOG_PATH = base_dir / "printer_status_log.json"
SLACK_SCRIPT = "/home/jeremy/scripts/slack/slack_notify_lan_servers.sh"
EMAIL_SCRIPT = '/home/jeremy/scripts/email_notify/send_mail.py'

# SNMP OIDs (numeric)
SYS_DESCR_OID = ".1.3.6.1.2.1.1.1.0"
MODEL_OID = ".1.3.6.1.2.1.25.3.2.1.3.1"
NAME_BASE = ".1.3.6.1.2.1.43.11.1.1.6.1."
VALUE_BASE = ".1.3.6.1.2.1.43.11.1.1.9.1."
TOTAL_BASE = ".1.3.6.1.2.1.43.11.1.1.8.1."

# Printers to check
PRINTERS = {
    "192.168.0.102": 5,
    "192.168.0.103": 6,
    "192.168.0.104": 4,
    "192.168.0.105": 9,
    "192.168.0.106": 5,
#    "192.168.0.107": 1, # ID Card Printer
}

# Get email recipients from command line args
parser = argparse.ArgumentParser(description="Monitor printer and notify.")
parser.add_argument(
    '--email',
    nargs='+',
    help='One or more email addresses to notify',
    required=True
)
parser.add_argument(
    '--cc',
    nargs='*',
    default=[],
    help='Optional CC email addresses'
)
args = parser.parse_args()
email_recipients = args.email
cc_recipients = args.cc

# --- Utilities ---

def load_log():
    if LOG_PATH.exists():
        try:
            with open(LOG_PATH, "r") as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except (json.JSONDecodeError, IOError):
            print(f"Warning: Failed to parse log file at {LOG_PATH}. Starting fresh.")
            return {}
    return {}

def save_log(log):
    with open(LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)

def days_since(date_str):
    return (datetime.now() - datetime.strptime(date_str, "%Y-%m-%d")).days

def notify_slack(message, level):
    subprocess.run([SLACK_SCRIPT, message, level])

def notify_email(to, subject, body, cc=None):
    cmd = ['python3', EMAIL_SCRIPT, '--to', to, '--subject', subject, '--body', body]
    if cc:
        cmd.extend(['--cc', cc])
    subprocess.run(cmd)

def run_snmpwalk(ip, oid, options='-Ova'):
    try:
        result = subprocess.check_output(['snmpwalk', '-v', '1', '-c', 'public', options, ip, oid], text=True)
        result = result.replace('STRING: ', '').replace('INTEGER: ', '').replace('"', '').strip()
        return result
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"

def check_availability(ip):
    try:
        subprocess.run(
            ["snmpget", "-v", "1", "-c", "public", "-t", "1", "-r", "1", ip, SYS_DESCR_OID],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False

def get_supply_count(ip):
    base_oid = NAME_BASE.rstrip('.')
    result = run_snmpwalk(ip, base_oid)
    return result.count("\n") if result else 0

# --- Main logic ---

def check_printer(ip, supply_count, log):
    print(f"\nChecking printer at {ip}\n" + "-"*30)
    today = datetime.now().strftime("%Y-%m-%d")

    if not check_availability(ip):
        print(f"Timeout: No Response from {ip}")
        record = log.get(ip, {})
        last_seen = record.get("last_seen")
        if last_seen and days_since(last_seen) > 7 and not record.get("offline_alerted"):
            printer_name = record.get("name", ip).replace('"', '').strip()

            msg = f"Printer {printer_name} offline for {days_since(last_seen)} days"

            notify_slack(msg, "Info")

            notify_email(
                to='it@adhd.org.sa',
                subject= f"Printer {printer_name} Offline",
                body=msg,
            )

            record["offline_alerted"] = True
        elif not last_seen:
            record["last_seen"] = today
        log[ip] = record
        return

    model = run_snmpwalk(ip, MODEL_OID)
    print(f"Model: {model}")
    record = log.get(ip, {"name": model})
    record["last_seen"] = today
    record["offline_alerted"] = False

    if supply_count is None:
        supply_count = get_supply_count(ip)

    toner_alerts = record.get("toner_alerted", {})
    new_alerts = {}
    slack_needed = []
    for i in range(1, supply_count + 1):
        name = run_snmpwalk(ip, NAME_BASE + str(i))
        value = run_snmpwalk(ip, VALUE_BASE + str(i))
        total = run_snmpwalk(ip, TOTAL_BASE + str(i))

        try:
            value = int(value)
            total = int(total)
            percent = int(value / total * 100) if total > 0 else 0
        except (ValueError, ZeroDivisionError):
            percent = value

        needs_order = isinstance(percent, int) and (percent < 0 or 0 < percent < 20)
        order_str = "YES" if needs_order else "NO"
        print(f"  - {name}: {percent}% remaining | Order: {order_str}")

        if needs_order:
            last_alerted = toner_alerts.get(name)
            if not last_alerted or days_since(last_alerted) >= 7:
                slack_needed.append(name)
                new_alerts[name] = today
            else:
                new_alerts[name] = last_alerted
        elif name in toner_alerts:
            # Toner level recovered — do not retain in new_alerts
            pass

    if slack_needed:
        clean_model = model.replace('"', '').strip()
        clean_list = "\n".join(s.replace('"', '').strip() for s in slack_needed)

        msg = f"Order Toner for printer {clean_model}\n{clean_list}"

        notify_slack(msg, "ToDo")

        notify_email(
            to=', '.join(email_recipients),
            cc=', '.join(cc_recipients) if cc_recipients else None,
            subject='Order Printer Toner',
            body=msg,
        )

    record["toner_alerted"] = new_alerts
    log[ip] = record

# --- Entry point ---

def main():
    log_data = load_log()
    for ip, count in PRINTERS.items():
        check_printer(ip, count, log_data)
    save_log(log_data)

if __name__ == "__main__":
    main()
