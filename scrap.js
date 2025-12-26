const fs = require('fs')

// --- CONFIGURATION ---
const HOURS = 6
const CACHE_MAX_AGE = 1000 *     60 * 60 * HOURS // ms

const JSON_DIR = './json/'
const IN_DIR = './links.txt'
const OUTPUT_HTML = './report.html'

// Headers to mimic a browser
const HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.google.com/'
}

// --- HTML TEMPLATE
const HTML_TEMPLATE_START = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Theater Scraper (Dark Mode)</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #121212; color: #e0e0e0; margin: 0; padding: 20px; }
        h1 { text-align: center; color: #ffffff; letter-spacing: 1px; }
        .timestamp { text-align: center; font-size: 0.9em; color: #aaaaaa; margin-bottom: 20px; }
        
        table { width: 100%; border-collapse: separate; border-spacing: 0; background: #1e1e1e; box-shadow: 0 4px 10px rgba(0,0,0,0.5); border-radius: 8px; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #333333; }
        
        th { background-color: #00796b; color: white; cursor: pointer; 
        position: sticky; 
        top: 0; 
        z-index: 100;
        user-select: none; font-weight: 600; text-transform: uppercase; font-size: 0.85em; letter-spacing: 0.5px; border-bottom: 1px solid #333333; }

        th:first-child { border-top-left-radius: 8px; }
        th:last-child { border-top-right-radius: 8px; }
        
        th.sort { cursor: pointer; }
        th.sort:hover { background-color: #004d40; }
        th.sort::after { content: ' \\21F5'; opacity: 0.5; font-size: 0.8em; }
        
        /* Row Styling */
        tr:nth-child(even) { background-color: #252525; }
        
        /* Specific Column Styles */
        .col-name { font-weight: bold; color: #80cbc4; font-size: 1.05em; }
        .col-link a { text-decoration: none; color: white; background-color: #1976d2; padding: 6px 12px; border-radius: 4px; font-size: 0.85em; display: inline-block; transition: background 0.2s; }
        .col-link a:hover { background-color: #1565c0; }
        
        /* Availability Bar */
        .availability-bar-bg { width: 100px; height: 6px; background-color: #444; border-radius: 3px; overflow: hidden; display: inline-block; vertical-align: middle; margin-right: 8px; }
        .availability-bar-fill { height: 100%; background-color: #2cb31d; box-shadow: 0 0 5px rgba(4, 218, 26, 0.5); }
        .availability-text { font-size: 0.85em; color: #bbb; font-weight: bold; }
        
        /* Prices */
        .price-list { font-size: 0.85em; margin: 0; padding-left: 0; list-style: none; color: #ddd; }
        .price-list li { margin-bottom: 3px; }
        .price-list strong { color: #81c784; }

        .error-container { margin-top: 40px; border: 1px solid #ef5350; background-color: #221214ff; border-radius: 8px; padding: 20px; }
        .error-title { color: #ff5252; font-size: 1.2em; margin-bottom: 15px; border-bottom: 1px solid #ef5350; padding-bottom: 5px; }
        .error-list { list-style: none; padding: 0; margin: 0; }
        .error-item { margin-bottom: 10px; border-bottom: 1px solid #442b2d; padding-bottom: 5px; }
        .error-link { color: #ff8a80; font-family: monospace; display: block; text-decoration: none; }
        .error-link:hover { text-decoration: underline; }
        .error-msg { color: #bbb; font-size: 0.85em; margin-top: 2px; font-style: italic; }
    </style>
</head>
<body>
    <h1>Theater List</h1>
    <div class="timestamp">Generated on: {{TIMESTAMP}}</div>
    
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
`

const HTML_TEMPLATE_END = `
        </tbody>
    </table>

    {{ERRORS}}

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
                    
                    // Check for custom data attribute (numbers/dates) or text
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
`

// --- HELPER FUNCTIONS ---
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms))
}

function isCacheFresh(filepath) {
    if (!fs.existsSync(filepath)) return false
    const stats = fs.statSync(filepath)
    const age = Date.now() - stats.mtimeMs
    return age < CACHE_MAX_AGE
}

// Simple fetch wrapper
async function fetchUrl(url) {
    const response = await fetch(url, { headers: HEADERS })
    if (!response.ok) throw new Error(`HTTP Error: ${response.status}`)
    return await response.text()
}

function processPageData(page) {
    const data = { dates: [] }
    let totalSoldOut = 0
    let totalAvailable = 0
    let totalAvailablePrcnt = 0

    const events = page.json?.events || []

    events.forEach(event => {
        if (event.isBookingActive) {
            totalAvailable++
            totalAvailablePrcnt += event['availability-percentage']
            const date = event['event-date']?.split('T')[0]
            if (date && !data.dates.includes(date)) {
                data.dates.push(date)
            }
        } else if (event.isSoldout) {
            totalSoldOut++
        }
    })

    data.dates.sort()

    data.min_date = data.dates.length > 0 ? data.dates[0] : "N/A"
    data.max_date = data.dates.length > 0 ? data.dates[data.dates.length - 1] : "N/A"
    data.total_days = data.dates.length

    data.total_sold_out = totalSoldOut
    data.total_available = totalAvailable
    data.total_events = totalSoldOut + totalAvailable

    data.availability = 0
    if (totalAvailable > 0) {
        data.availability = Math.round(totalAvailablePrcnt / totalAvailable)
    }

    data.pricesHTML = []

    const pricelists = page.json?.pricelists || []
    for (let list of pricelists) {
        const prices = []
        for (let price of list.discounts) {
            prices.push(`<div>${price["discount-name"]}: <strong>${price["price"]}</strong></div>`)
        }
        data.pricesHTML.push(prices)
    }

    page.data = data
    return page
}

function generateHtmlRow(page) {
    const d = page.data
    return `
    <tr>
        <td class='col-name'>${page.name || 'Unknown'}</td>
        <td data-sort='${d.min_date}'>${d.min_date}</td>
        <td data-sort='${d.max_date}'>${d.max_date}</td>
        <td data-sort='${d.total_available}'>${d.total_available}</td>
        <td data-sort='${d.availability}'><div style='display:flex; align-items:center;'>
        <div class='availability-bar-bg'>
            <div class='availability-bar-fill' style='width:${d.availability}%'></div>
        </div>
        <span class='availability-text'>${d.availability}%</span>
    </div></td>
        <td data-sort='${d.total_sold_out}'>${d.total_sold_out}/${d.total_events}</td>
        <td>${d.pricesHTML[0]}</td>
        <td class='col-link'><a href='${page.url}' target='_blank'>LINK</a></td>
    </tr>`
}

// --- MAIN EXECUTION ---
(async () => {
    if (!fs.existsSync(JSON_DIR)) fs.mkdirSync(JSON_DIR)

    if (!fs.existsSync(IN_DIR)) {
        const defaultText =
            "Paste the theatre links under here, separated by new line"
        fs.writeFileSync(IN_DIR, defaultText, 'utf-8')
        process.exit()
    }

    const fileContent = fs.readFileSync(IN_DIR, 'utf-8')
    const links = fileContent.split(/\r?\n/).map(l => l.trim()).filter(l => l.startsWith('http'))

    const pages = []
    const invalids = []

    for (const url of links) {
        const engName = url.split('/').slice(-2)[0] || 'unknown'
        const jsonPath = JSON_DIR + `${engName}.json`
        let page = { engName, url, json: null }

        // Caching check
        if (isCacheFresh(jsonPath)) {
            try {
                page.json = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'))
            } catch (e) { page.json = null }
        }

        // Network Fetch
        if (!page.json) {
            try {
                const html = await fetchUrl(url)

                const regex = /(?:bookingPanel\.init|scheduleDisplay\.initCalendar)\s*\((.*?)\);/s
                const match = html.match(regex)

                if (!match) throw new Error("No JSON data found (Regex failed)")

                page.json = JSON.parse(match[1])
                fs.writeFileSync(jsonPath, JSON.stringify(page.json, null, 2), 'utf-8')

                const sleepTime = Math.random() * 3000 + 2000
                await sleep(sleepTime)

            } catch (e) {
                invalids.push({ url, msg: `Network Error: ${e.message}` })
                continue
            }
        }

        // Data processing
        try {
            page.name = engName
            if (page.json?.plays?.length > 0) {
                page.name = page.json.plays[0]['play-title'].trim()
            }

            page = processPageData(page)
            pages.push(page)

        } catch (e) {
            invalids.push({ url, msg: `Data Error: ${e.message}` })
        }
    }

    const now = new Date().toLocaleString('en-GB', { hour12: false })
    let htmlContent = HTML_TEMPLATE_START.replace('{{TIMESTAMP}}', now)

    pages.forEach(page => {
        htmlContent += generateHtmlRow(page)
    })

    let errorSection = ""
    if (invalids.length > 0) {
        const errorRows = invalids.map(item => `
            <li class="error-item">
                <a href="${item.url}" target="_blank" class="error-link">${item.url}</a>
                <div class="error-msg">${item.msg}</div>
            </li>
        `).join('')

        errorSection = `
            <div class="error-container">
                <div class="error-title">Failed Links (${invalids.length})</div>
                <ul class="error-list">${errorRows}</ul>
            </div>`
    }

    htmlContent += HTML_TEMPLATE_END.replace('{{ERRORS}}', errorSection)

    fs.writeFileSync(OUTPUT_HTML, htmlContent, 'utf-8')

})()
