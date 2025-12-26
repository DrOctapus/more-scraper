import os
import random
import time
import requests
import json
import re
import sys

# --- HTML TEMPLATE ---
# This contains the CSS and JS for the single-file output
HTML_TEMPLATE_START = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Theater Scraper (Dark Mode)</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #121212; color: #e0e0e0; margin: 0; padding: 20px; }
        h1 { text-align: center; color: #ffffff; letter-spacing: 1px; }
        .timestamp { text-align: center; font-size: 0.9em; color: #aaaaaa; margin-bottom: 20px; }
        
        table { width: 100%; border-collapse: collapse; background: #1e1e1e; box-shadow: 0 4px 10px rgba(0,0,0,0.5); border-radius: 8px; overflow: hidden; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #333333; }
        
        /* Sticky Header */
        th { background-color: #00796b; color: white; position: sticky; top: 0; z-index: 10; user-select: none; font-weight: 600; text-transform: uppercase; font-size: 0.85em; letter-spacing: 0.5px; }
        th.sort { cursor: pointer; }
        th.sort:hover { background-color: #004d40; }
        th.sort::after { content: ' \\21F5'; opacity: 0.5; font-size: 0.8em; }
        
        /* Row Styling */
        tr:nth-child(even) { background-color: #252525; }
        
        /* Specific Column Styles */
        .col-name { font-weight: bold; color: #80cbc4; font-size: 1.05em; }
        .col-link a { text-decoration: none; color: white; background-color: #1976d2; padding: 6px 12px; border-radius: 4px; font-size: 0.85em; display: inline-block; transition: background 0.2s; }
        .col-link a:hover { background-color: #1565c0; }
        
        /* Hotness Bar */
        .hotness-bar-bg { width: 100px; height: 6px; background-color: #444; border-radius: 3px; overflow: hidden; display: inline-block; vertical-align: middle; margin-right: 8px; }
        .hotness-bar-fill { height: 100%; background-color: #2cb31d; box-shadow: 0 0 5px rgba(255, 82, 82, 0.5); }
        .hotness-text { font-size: 0.85em; color: #bbb; font-weight: bold; }
        
        /* Prices */
        .price-list { font-size: 0.85em; margin: 0; padding-left: 0; list-style: none; color: #ddd; }
        .price-list li { margin-bottom: 3px; }
        .price-list strong { color: #81c784; }
        .warning { color: #ffab91; font-weight: bold; font-size: 0.8em; display: block; margin-top: 4px; }
    </style>
</head>
<body>
    <h1>Theater List</h1>
    <div class="timestamp">Generated on: {generated_time}</div>
    
    <table id="myTable">
        <thead>
            <tr>
                <th class="sort" onclick="sortTable(0)">Play Name</th>
                <th class="sort" onclick="sortTable(1)">Start Date</th>
                <th class="sort" onclick="sortTable(2)">End Date</th>
                <th class="sort" onclick="sortTable(3)">Total Days</th>
                <th class="sort" onclick="sortTable(4)">Seat Availability</th>
                <th class="sort" onclick="sortTable(5)">Sold Out</th>
                <th ">Prices</th>
                <th ">Link</th>
            </tr>
        </thead>
        <tbody>
"""

HTML_TEMPLATE_END = """
        </tbody>
    </table>

    <script>
        function sortTable(n) {
            var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
            table = document.getElementById("myTable");
            switching = true;
            dir = "asc"; 
            
            while (switching) {
                switching = false;
                rows = table.rows;
                
                for (i = 1; i < (rows.length - 1); i++) {
                    shouldSwitch = false;
                    x = rows[i].getElementsByTagName("TD")[n];
                    y = rows[i + 1].getElementsByTagName("TD")[n];
                    
                    // Check if we should sort by custom data attribute (numbers/dates) or text
                    var xVal = x.getAttribute("data-sort") || x.innerHTML.toLowerCase();
                    var yVal = y.getAttribute("data-sort") || y.innerHTML.toLowerCase();
                    
                    // Convert to number if possible for correct numeric sorting
                    if (!isNaN(parseFloat(xVal)) && isFinite(xVal)) {
                        xVal = parseFloat(xVal);
                        yVal = parseFloat(yVal);
                    }

                    if (dir == "asc") {
                        if (xVal > yVal) { shouldSwitch = true; break; }
                    } else if (dir == "desc") {
                        if (xVal < yVal) { shouldSwitch = true; break; }
                    }
                }
                if (shouldSwitch) {
                    rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                    switching = true;
                    switchcount ++; 
                } else {
                    if (switchcount == 0 && dir == "asc") {
                        dir = "desc";
                        switching = true;
                    }
                }
            }
        }
    </script>
</body>
</html>
"""

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
        file1.write("Paste the theatre links under here, paste as many you want, seperated by new line")
    sys.exit()

SORT = 0

with open(IN_DIR, "r", encoding="utf-8") as file2:
    LINKS = []
    INVALID_LINKS = []
    for line in file2:
        if line.startswith("https://www.more.com/gr-el/tickets/"):
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


def is_cache_fresh(filepath):
    if not os.path.exists(filepath):
        return False

    file_age = time.time() - os.path.getmtime(filepath)
    if file_age < CACHE_MAX_AGE:
        return True

    return False


def process_page_data(page):
    data = {"dates": []}
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

    # Safe Calculations
    data["min_date"] = min(data["dates"]) if data["dates"] else "N/A"
    data["max_date"] = max(data["dates"]) if data["dates"] else "N/A"

    total_events = total_sold_out + total_available
    data["total_sold_out"] = total_sold_out
    data["total_events"] = total_events
    data["total_available"] = total_available

    data["availability"] = 0
    if total_available > 0:
        data["availability"] = int(total_availability_prcnt / total_available)

    # Process Prices
    data["prices_html"] = []
    for list in page["json"]["pricelists"]:
        items = []
        for price in list["discounts"]:
            p_name = price["discount-name"]
            p_val = price["price"]
            items.append(f"<li>{p_name}: <strong>€{p_val}</strong></li>")

        data["prices_html"].append(f"<ul class='price-list'>{''.join(items)}</ul>")

    page["data"] = data
    return page


def generate_html_row(page):
    d = page["data"]

    # Pre-calculate sort values (for data-sort attribute)
    availability = d["availability"]

    # Create HTML row
    row = "<tr>"
    row += f"<td class='col-name'>{page['name']}</td>"
    row += f"<td data-sort='{d['min_date']}'>{d['min_date']}</td>"
    row += f"<td data-sort='{d['max_date']}'>{d['max_date']}</td>"
    row += f"<td data-sort='{d['total_available']}'>{d['total_available']}</td>"

    # Availability Bar
    bar = f"""
    <div style='display:flex; align-items:center;'>
        <div class='hotness-bar-bg'>
            <div class='hotness-bar-fill' style='width:{availability}%'></div>
        </div>
        <span class='hotness-text'>{availability}%</span>
    </div>
    """
    row += f"<td data-sort='{availability}'>{bar}</td>"

    row += f"<td data-sort='{d['total_sold_out']}'>{d['total_sold_out']}/{d['total_events']}</td>"

    # Prices TODO
    row += f"<td>{d['prices_html'][0]}</td>"

    # Link
    row += f"<td class='col-link'><a href='{page['url']}' target='_blank'>Url</a></td>"
    row += "</tr>"
    return row


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
                raise Exception
            page["json"] = json.loads(match.group(1))

            with open(json_path, "w", encoding="utf-8") as file4:
                json.dump(page["json"], file4, ensure_ascii=False)

            # Avoid scraping detection
            sleep_time = random.uniform(2, 5)
            time.sleep(sleep_time)

        except Exception as e:
            INVALID_LINKS.append(url)
            continue

    page["name"] = page["json"]["plays"][0]["play-title"].strip()

    page = process_page_data(page)
    PAGES.append(page)

LINKS = [link for link in LINKS if link not in INVALID_LINKS]

timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
html_content = HTML_TEMPLATE_START.replace("{generated_time}", timestamp)

for page in PAGES:
    html_content += generate_html_row(page)

html_content += HTML_TEMPLATE_END

with open(os.path.join(BASE_DIR, "report.html"), "w", encoding="utf-8") as f:
    f.write(html_content)
