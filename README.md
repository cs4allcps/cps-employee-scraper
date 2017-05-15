# CPS employee downloader
This script scrapes CPS' employees from the CPS employee search tool.

Caveats:

- This tool only works on the CPS network
- ITS may catch on and decide they don't want their server hit by 26^2 requests on occasion. Connection reset errors are not unknown.

# CPS employee comparer: compare.py
This tool compares two lists of CPS employees scraped from the employee search tool, and creates these lists:

- new employees
- dearly departed employees
- employees with changed information.

Employees are identified by their email rather than their name.

## usage
`./compare.py before.csv after.csv`
