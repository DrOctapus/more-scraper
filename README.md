Requires *node.js*.

To exexcute `cd` in the directory of the script and run `node scrap.js`.

When executed, it creates a `links.txt` with simple instructions on how to populate it.

When execeuted with a populated `links.txt` it scrapes the htmls for the json objects from which it extracts performance dates and prices.

Can be compiled with the node module `pkg` installed with the command `pkg scraper.js --targets node18-win-x64 --output scraper.exe --compress GZip`
