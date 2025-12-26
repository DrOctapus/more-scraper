Requires requests
pip install requests

When executed, it creates a `links.txt` with simple instructions on how to populate it and configure the sorting.
It can either sort be ascending seat availability or ascending "last performance" date.

When execeuted with a populated `links.txt` it scrapes the htmls for the json objects from which it extracts performance dates and prices.
