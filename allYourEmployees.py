#!/usr/bin/env python2.7

### ended up using mechanize: http://stackoverflow.com/questions/13703772/sending-form-data-to-aspx-page
# much help from http://stackoverflow.com/questions/14746750/post-request-using-python-to-asp-net-page
# also http://stackoverflow.com/questions/1480356/how-to-submit-query-to-aspx-page-in-python
# also https://stackoverflow.com/questions/9446387/how-to-retry-urllib2-request-when-fails

debug = False

from bs4 import BeautifulSoup as bs
from csv import writer
from datetime import date
from functools import wraps
from itertools import product
import mechanize
import multiprocessing as mp
import random
from string import ascii_lowercase as letters
from time import sleep
import urllib

if (debug):
    letters = 's'

outputFile = str(date.today()) + " employees.csv"

# all 2-letter combos
combos = ["".join(x) for x in product(letters, letters)]

# header for csv
header = [["Last Name", "First Name", "Title", "Department", "Phone", "Email", "Type"]]

url = 'http://staff.cps.edu/EmployeeSearch/default.aspx'

# sometimes the connection gets reset; this works around that.
def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param ExceptionToCheck: the exception to check. may be a tuple of
        exceptions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """
    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck, e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print msg
                    sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry


@retry(IOError, tries=4, delay=3, backoff=2)
def getEmployees(combo, q):
    '''
    gets all employees whose email starts with `combo`
    '''
    print("parsing combo %s..." % combo)

    employees = []

    # get parseable form of form page
    if (debug):
        print(combo + "opening page...")
    r = urllib.FancyURLopener().open(url)
    if (debug):
        print(combo + "...page opened.")
    soup = bs(r, 'html.parser')

    viewstate = soup.select("#__VIEWSTATE")[0]['value']
    viewstategenerator = soup.select("#__VIEWSTATEGENERATOR")[0]['value']
    eventvalidation = soup.select("#__EVENTVALIDATION")[0]['value']

    # this structure mostly serves to record the form fields
    payload = (
        ('__VIEWSTATE', viewstate),
        ('__VIEWSTATEGENERATOR', viewstategenerator),
        ('__EVENTVALIDATION', eventvalidation),
        ('ctl00$ContentPlaceHolder1$SEARCH_LAST_NAME', ''),
        ('ctl00$ContentPlaceHolder1$SEARCH_FIRST_NAME', ''),
        ('ctl00$ContentPlaceHolder1$SEARCH_EMAIL', 'aa'),
        ('ctl00$ContentPlaceHolder1$btnSearch', '1')
    )

    # that creature has to be encoded
    encodedPayload = urllib.urlencode(payload)

    # compose and post form to get form object
    request = mechanize.Request(url)
    response = mechanize.urlopen(request)

    # the form we want is the first one, could search by id/class I suppose
    form = mechanize.ParseResponse(response, backwards_compat=False)[0]

    # tidy up
    response.close()

    form['ctl00$ContentPlaceHolder1$SEARCH_EMAIL'] = combo

    # post form; this .click() method is why the mechanize module is great,
    # otherwise I couldn't figure out how to post this form properly because
    # the ASP.NET framework relies on some kind of javascript activated by
    # the button to submit the damn form
    results = mechanize.urlopen(form.click()).read()

    # beautifulsoup is also great :)
    soup = bs(results, 'html.parser')

    # there might be a better way to pick out this table, meh
    for table in soup.select("table"):
        try:
            if table['id'] == 'ctl00_ContentPlaceHolder1_gvEmployees':
                for tr in table.select("tr")[1:]: # skip first row
                    # get email
                    employee = [
                        tr.select("td")[1].get_text().strip().encode('utf8'),
                        tr.select("td")[2].get_text().strip().encode('utf8'),
                        tr.select("td")[3].get_text().strip().encode('utf8'),
                        tr.select("td")[4].get_text().strip().encode('utf8'),
                        tr.select("td")[5].get_text().strip().encode('utf8'),
                        tr.select("td")[6].get_text().strip().encode('utf8'),
                        tr.select("td")[7].get_text().strip().encode('utf8')
                    ]

                    employees.append(employee)
        except KeyError:
            pass

    if (debug):
        print(combo + "sleeping...")
    sleep(round(random.random(), 3))
    if (debug):
        print(combo + "...done sleep.")

    q.put(employees)

def listener(q):
    '''
    listens to queue and outputs to a file
    '''

    with open(outputFile, 'wb') as o:
        # set up CSV writer
        employeeCSV = writer(o)

        while True:
            m = q.get()
            if m == "kill":
                print("done with everything!")
                break # get out of this joint
            employeeCSV.writerows(m)
            o.flush() # might be redundant

def main():
    # must use Manager queue or it doesn't work
    manager = mp.Manager()
    q = manager.Queue()
    pool = mp.Pool(mp.cpu_count() + 2)

    # start listener first
    watcher = pool.apply_async(listener, (q,))

    # start workers
    jobs = []
    for combo in combos:
        job = pool.apply_async(getEmployees, (combo, q))
        jobs.append(job)

    # collect results
    for job in jobs:
        job.get()

    # all done working, stop the listener
    q.put("kill")
    pool.close()

if __name__ == "__main__":

    with open(outputFile, 'wb') as o:
        # set up CSV
        employeeCSV = writer(o)
        employeeCSV.writerow(header)

    main()
