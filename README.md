Requires the *python language* and the requests module.

If python is installed, to get the module you execute `pip install requests` in a terminal with admin privileges.

When executed, it creates a `links.txt` with simple instructions on how to populate it and configure the sorting.
It can either sort be ascending seat availability or ascending "last performance" date.

When execeuted with a populated `links.txt` it scrapes the htmls for the json objects from which it extracts performance dates and prices.
