from cgitb import html
from distutils.command.clean import clean
from http.client import ImproperConnectionState
import requests
import re
import urllib.request
from bs4 import BeautifulSoup
from collections import deque
from html.parser import HTMLParser
from urllib.parse import urlparse
import os

# Regex pattern to match URL 
HTTP_URL_PATTERN = r'^http[s]{0,1}://.+$'
domain = "openai.com" # domain to crawl
full_url = "https://openai.com/" # put your domain to be crawled with https or http
# create a class to parse the HTML and get the hyperlinks
class HyperlinkParser(HTMLParser):
    def __init__(self):
        super().__init__() # 
        # create a list to store the hyperlinks
        self.hyperLinks = []
    #Override the HTMLParser's handle_starttag method to get the hyperlinks
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        # If the tag is an anchor tag and it has an href attribute, add the href attribute to the list of hyperlinks
        if tag == "a" and "href" in attrs:
            self.hyperLinks.append(attrs["href"])
# this function takes in the URL as an argument, opens the URL and reads the HTML content
def get_hyperlinks(url):
    # try to open the URL and get the HTML text
    try:
        # open the URL and read the HTML
        with urllib.request.urlopen(url) as response:
            # if the response is not HTML, return an empty list
            if not (response.info().get('Content-Type').startswith("text/html")):
                return []
            # decode the html
            html = response.read().decode('utf-8')
    except Exception as e:
        print(e)
        return []
    # create the HTML Parser and then Parse the HTML to get hyperlinks
    parser = HyperlinkParser() # instance of the HyperlinkParser() class
    parser.feed(html) # you are 'feeding' the html into the freshly created instace if the HyperLinkParse class
    return parser.hyperLinks
# the goal is to crawl through and index only the context that lives under the OpenAI domain
# For this purpose, a function that calls the get_hyperlinks function but filters out any 
# URLs that are not part of the specified domain is needed.
# Function to get the hyperlinks from a URL that are within the same domain
def get_domain_hyperlinks(local_domain, url):
    clean_links = []
    for link in set(get_hyperlinks(url)):
        clean_link = None
        # If the link is a URL, check if it is within the same domain
        if re.search(HTTP_URL_PATTERN, link):
            # Parse the URL and check if the domain is the same
            url_obj = urlparse(link)
            if url_obj.netloc == local_domain:
                clean_link = link
        # If the link is not a URL, check if it is a relative link
        else:
            if link.startswith("/"):
                link = link[1:]
            elif (link.startswith("#") or link.startswith("mailto:") or link.startswith("tel:")):
                continue
            clean_link = "https://" + local_domain + "/" + link
        if clean_link:
            if clean_link.endswith("/"):
                clean_link = clean_link[:-1]
            clean_links.append(clean_link)
    # Return the list of hyperlinks that are within the same domain
    return list(set(clean_links))
# The crawl function is the final step in the web crawling task setup. 
# it keeps track of the visited URLs to avoid repeating the same page
def crawl(url):
    # Parse the URL and get the domain
    local_domain = urlparse(url).netloc
    # Create a queue to store the URLs to crawl
    queue = deque([url])
    # Create a set to store the URLs that have already been seen (no duplicates)
    seen = set([url])
    # Create a directory to store the text files
    if not os.path.exists("text/"):
            os.mkdir("text/")
    if not os.path.exists("text/"+local_domain+"/"):
            os.mkdir("text/" + local_domain + "/")
    # Create a directory to store the csv files
    if not os.path.exists("processed"):
            os.mkdir("processed")
    # While the queue is not empty, continue crawling
    while queue:
        # Get the next URL from the queue
        url = queue.pop()
        print(url) # for debugging and to see the progress
        # Save text from the url to a <url>.txt file
        with open('text/'+local_domain+'/'+url[8:].replace("/", "_") + ".txt", "w", encoding="UTF-8") as f:
            # Get the text from the URL using BeautifulSoup
            soup = BeautifulSoup(requests.get(url).text, "html.parser")
            # Get the text but remove the tags
            text = soup.get_text()
            # If the crawler gets to a page that requires JavaScript, it will stop the crawl
            if ("You need to enable JavaScript to run this app." in text):
                print("Unable to parse page " + url + " due to JavaScript being required")
            # Otherwise, write the text to the file in the text directory
            f.write(text)
        # Get the hyperlinks from the URL and add them to the queue
        for link in get_domain_hyperlinks(local_domain, url):
            if link not in seen:
                queue.append(link)
                seen.add(link)
crawl(full_url)

