import os
import random
import time
import requests
import json
import re
import sys

# Directory of the current script
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# hours in secs
HOURS = 6
CACHE_MAX_AGE = 60 * 60 * HOURS

JSON_DIR = os.path.join(BASE_DIR, "json")

# input file with URLs
IN_FILE = "links.txt"
IN_DIR = os.path.join(BASE_DIR, IN_FILE)

if not os.path.exists(JSON_DIR):
    os.makedirs(JSON_DIR)

if not os.path.exists(IN_DIR):
    with open(IN_DIR, "w", encoding="utf-8") as file1:
        file1.write("Sort output by: 1\n")
        file1.write("(1 for Last Available Date, 2 for Percentage of Seats Taken)\n")
        file1.write("Paste more.com links under, seperated by new line\n")
        file1.write("https://www.more.com/gr-el/tickets/theater/THEATRE-NAME-1\n")
        file1.write("https://www.more.com/gr-el/tickets/theater/THEATRE-NAME-2")
    sys.exit()

SORT = 0

with open(IN_DIR, "r", encoding="utf-8") as file2:
    LINKS = []
    INVALID_LINKS = []
    for line in file2:
        if line.startswith("https://www.more.com/gr-el/tickets/theater/"):
            LINKS.append(line.strip())
        elif line.startswith("https"):
            INVALID_LINKS.append(line.strip())
        elif line.startswith("Sort output by: "):
            try:
                SORT = int(line.split(": ")[1][0])
                if SORT not in [1, 2]:
                    raise Exception
            except Exception:
                SORT = 1

with open(IN_DIR, "w", encoding="utf-8") as file21:
    file21.write(f"Sort output by: {SORT}\n")
    file21.write("(1 for Last Available Date, 2 for Percentage of Seats Taken)\n")
    file21.write("Paste more.com links under, seperated by new line\n")
    file21.write("\n".join(LINKS))
    if len(INVALID_LINKS) > 0:
        file21.write("\nINVALID LINKS:\n")
        file21.write("\n".join(INVALID_LINKS))


def is_cache_fresh(filepath):
    if not os.path.exists(filepath):
        return False

    file_age = time.time() - os.path.getmtime(filepath)
    if file_age < CACHE_MAX_AGE:
        return True

    return False


def event_to_string(page):
    output = ""
    output += "-" * 50 + "\n" + page["name"] + "\n"
    output += page["url"] + "\n"

    lData = page["data"]

    output += f"Dates: {lData["min_date"]} - {lData["max_date"]}\n"
    output += f"Total Days: {len(lData["dates"])}\n"

    output += f"NON Sold-Out: {lData["total_available"]}/{lData["total_events"]}\nPercent of Seats Free: {lData["availability_prcnt"]}\n"

    output += "--\n"

    output += lData["prices"]

    return output


# HTTP headers to mimic a real browser
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "Accept-Language": "en-US,en;q=0.9", "Referer": "https://www.google.com/"}

# List to store page information
PAGES = []

for url in LINKS:
    page = {"engName": url.split("/")[-2]}
    json_path = os.path.join(JSON_DIR, f"{page["engName"]}.json")
    page["url"] = url

    if is_cache_fresh(json_path):
        with open(json_path, "r", encoding="utf-8") as file3:
            page["json"] = json.load(file3)
    else:
        try:
            print(f"Reloading {page["url"]}")
            response = requests.get(page["url"], headers=HEADERS, timeout=10)
            response.raise_for_status()

            pattern = r"(?:bookingPanel\.init|scheduleDisplay\.initCalendar)\s*\((.*?)\);"
            match = re.search(pattern, response.text, re.DOTALL)
            if match is None:
                print(f"WARNING {page["engName"]}, {page["url"]} didn't load the json")
            page["json"] = json.loads(match.group(1))

            with open(os.path.join(JSON_DIR, json_path), "w", encoding="utf-8") as file4:
                json.dump(page["json"], file4, ensure_ascii=False)

            # Avoid scraping detection
            sleep_time = random.uniform(2, 5)
            time.sleep(sleep_time)

        except Exception as e:
            print(f"WARNING {page["engName"]}, Error fetching the URL: {e}")

    page["name"] = page["json"]["plays"][0]["play-title"].strip()

    PAGES.append(page)

for page in PAGES:
    data = {}

    data["dates"] = []

    total_sold_out = 0
    total_available = 0
    total_availability_prcnt = 0
    for event in page["json"]["events"]:
        if event["isBookingActive"]:
            total_available += 1
            total_availability_prcnt += event["availability-percentage"]
            date = event["event-date"].split("T")[0]
            if date not in data["dates"]:
                data["dates"].append(date)
        elif event["isSoldout"]:
            total_sold_out += 1

    data["min_date"] = min(data["dates"])
    data["max_date"] = max(data["dates"])

    total_events = total_sold_out + total_available

    data["total_available"] = total_available
    data["total_events"] = total_events
    data["availability_prcnt"] = int(total_availability_prcnt / total_available)

    data["prices"] = ""
    for price in page["json"]["pricelists"][0]["discounts"]:
        data["prices"] += f"{price["discount-name"]}: {price["price"]}\n"

    if len(page["json"]["pricelists"]) > 1:
        data["prices"] += "WARNING, Pricing depends on day. Above prices are just one set of prices\n"

    page["data"] = data

with open(os.path.join(BASE_DIR, "output.txt"), "w", encoding="utf-8") as file5:
    if SORT == 2:
        file5.write("\n".join([event_to_string(page) for page in sorted(PAGES, key=lambda e: e["data"]["availability_prcnt"])]))
    else:
        file5.write("\n".join([event_to_string(page) for page in sorted(PAGES, key=lambda e: e["data"]["max_date"])]))

