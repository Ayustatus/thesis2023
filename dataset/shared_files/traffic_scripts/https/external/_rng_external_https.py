# Copied from https://github.com/1tayH/noisy with slight alteration for python version and calling of script.

import argparse
import datetime
import json
import logging
import os
import random
import re
import subprocess
import sys
import time

import requests
from dataset.utils import get_output_folder
from gen_utils import convert_sec_to_milli, write_meta_file
from urllib3.exceptions import LocationParseError

from urllib.parse import urljoin, urlparse




class Crawler(object):
    def __init__(self,source):
        """
        Initializes the Crawl class
        """
        self._config = {}
        self._links = []
        self._start_time = None
        self._end_time = None
        self.source = source
        
        

    class CrawlerTimedOut(Exception):
        """
        Raised when the specified timeout is exceeded
        """
        pass

    def _request(self, url):
        """
        Sends a POST/GET requests using a random user agent
        :param url: the url to visit
        :return: the response Requests object
        """
        random_user_agent = random.choice(self._config["user_agents"])
       # headers = {'user-agent': random_user_agent}

        response = requests.get(url, timeout=10)#headers=headers
        #print(url)
        dest_port = 99999
        if url.startswith("http://"):
            dest_port = 80
        if url.startswith("https://"):
            dest_port = 443
        if dest_port == 99999:
            raise Exception("Port error in rng external")
         # strips http[s]:// 
        url = url.split("//")[1]
        url = url.split("/")[0]  # strips sub pages
        url = url.split("?")[0] #strings get content like ?ans=hello?question=world
        if url.endswith("."):
            url = url[:-1]

        # since we only care about domain we only need the two last sections
        # so string www and other 
        url = ".".join(url.split(".")[-2:])
        #print(url)
        resp = subprocess.run(["dig","+short",url],capture_output=True) 
        ips = resp.stdout.decode().split("\n")
# TARGET is problematic, dig gives multiple ips, which is used is unk at this moment.
        lines = []
        for ip in ips:
            if ip != "":
                #print(ip)
                line = str.format("{0}:{1},{2}:{3},{4},{5},{6}",self.source,"SRC_PORT",ip,dest_port,self.meta_start,self.meta_end,"False")
                lines.append(line)
        folder_path = os.path.join(get_output_folder(),"temp")
        filename = os.path.join(folder_path,str.format("external_https_{0}_{1}.txt",self.source,self.meta_end))
        write_meta_file(folder_path,filename,lines)
        return response

    @staticmethod
    def _normalize_link(link, root_url):
        """
        Normalizes links extracted from the DOM by making them all absolute, so
        we can request them, for example, turns a "/images" link extracted from https://imgur.com
        to "https://imgur.com/images"
        :param link: link found in the DOM
        :param root_url: the URL the DOM was loaded from
        :return: absolute link
        """
        try:
            parsed_url = urlparse(link)
        except ValueError:
            # urlparse can get confused about urls with the ']'
            # character and thinks it must be a malformed IPv6 URL
            return None
        parsed_root_url = urlparse(root_url)

        # '//' means keep the current protocol used to access this URL
        if link.startswith("//"):
            return "{}://{}{}".format(parsed_root_url.scheme, parsed_url.netloc, parsed_url.path)

        # possibly a relative path
        if not parsed_url.scheme:
            return urljoin(root_url, link)

        return link

    @staticmethod
    def _is_valid_url(url):
        """
        Check if a url is a valid url.
        Used to filter out invalid values that were found in the "href" attribute,
        for example "javascript:void(0)"
        taken from https://stackoverflow.com/questions/7160737
        :param url: url to be checked
        :return: boolean indicating whether the URL is valid or not
        """
        regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return re.match(regex, url) is not None

    def _is_blacklisted(self, url):
        """
        Checks is a URL is blacklisted
        :param url: full URL
        :return: boolean indicating whether a URL is blacklisted or not
        """
        return any(blacklisted_url in url for blacklisted_url in self._config["blacklisted_urls"])

    def _should_accept_url(self, url):
        """
        filters url if it is blacklisted or not valid, we put filtering logic here
        :param url: full url to be checked
        :return: boolean of whether or not the url should be accepted and potentially visited
        """
        return url and self._is_valid_url(url) and not self._is_blacklisted(url)

    def _extract_urls(self, body, root_url):
        """
        gathers links to be visited in the future from a web page's body.
        does it by finding "href" attributes in the DOM
        :param body: the HTML body to extract links from
        :param root_url: the root URL of the given body
        :return: list of extracted links
        """
        pattern = r"href=[\"'](?!#)(.*?)[\"'].*?"  # ignore links starting with #, no point in re-visiting the same page
        urls = re.findall(pattern, str(body))

        normalize_urls = [self._normalize_link(url, root_url) for url in urls]
        filtered_urls = list(filter(self._should_accept_url, normalize_urls))

        return filtered_urls

    def _remove_and_blacklist(self, link):
        """
        Removes a link from our current links list
        and blacklists it so we don't visit it in the future
        :param link: link to remove and blacklist
        """
        self._config['blacklisted_urls'].append(link)
        del self._links[self._links.index(link)]

    def _browse_from_links(self, depth=0):
        """
        Selects a random link out of the available link list and visits it.
        Blacklists any link that is not responsive or that contains no other links.
        Please note that this function is recursive and will keep calling itself until
        a dead end has reached or when we ran out of links
        :param depth: our current link depth
        """
        is_depth_reached = depth >= int(self._config['max_depth'])
        if not len(self._links) or is_depth_reached:
            logging.debug("Hit a dead end, moving to the next root URL")
            # escape from the recursion, we don't have links to continue or we have reached the max depth
            return

        if self._is_timeout_reached():
            raise self.CrawlerTimedOut

        random_link = random.choice(self._links)
        try:
            logging.info("Visiting {}".format(random_link))
            sub_page = self._request(random_link).content
            sub_links = self._extract_urls(sub_page, random_link)

            # sleep for a random amount of time
            time.sleep(random.randrange(self._config["min_sleep"], self._config["max_sleep"]))

            # make sure we have more than 1 link to pick from
            if len(sub_links) > 1:
                # extract links from the new page
                self._links = self._extract_urls(sub_page, random_link)
            else:
                # else retry with current link list
                # remove the dead-end link from our list
                self._remove_and_blacklist(random_link)

        except requests.exceptions.RequestException:
            logging.debug("Exception on URL: %s, removing from list and trying again!" % random_link)
            self._remove_and_blacklist(random_link)

        self._browse_from_links(depth + 1)

    def load_config_file(self, file_path):
        """
        Loads and decodes a JSON config file, sets the config of the crawler instance
        to the loaded one
        :param file_path: path of the config file
        :return:
        """
        with open(file_path, 'r') as config_file:
            config = json.load(config_file)
            self.set_config(config)

    def set_config(self, config):
        """
        Sets the config of the crawler instance to the provided dict
        :param config: dict of configuration options, for example:
        {
            "root_urls": [],
            "blacklisted_urls": [],
            "click_depth": 5
            ...
        }
        """
        self._config = config

    def set_option(self, option, value):
        """
        Sets a specific key in the config dict
        :param option: the option key in the config, for example: "max_depth"
        :param value: value for the option
        """
        self._config[option] = value

    def _is_timeout_reached(self):
        """
        Determines whether the specified timeout has reached, if no timeout
        is specified then return false
        :return: boolean indicating whether the timeout has reached
        """
        is_timeout_set = self._config["timeout"] is not False  # False is set when no timeout is desired
        is_timed_out = False
        if self._end_time is not None:
            is_timed_out = datetime.datetime.now() >= self._end_time

        return is_timeout_set and is_timed_out

    def crawl(self):
        """
        Collects links from our root urls, stores them and then calls
        `_browse_from_links` to browse them
        """
        self._start_time = datetime.datetime.now()
        self.meta_start = int(convert_sec_to_milli(time.time()))
        self._end_time = self._start_time + datetime.timedelta(seconds=int(self._config["timeout"]))
        self.meta_end = self.meta_start + convert_sec_to_milli(int(self._config["timeout"]))
        while True:
            url = random.choice(self._config["root_urls"])
            try:
                body = self._request(url).content
                self._links = self._extract_urls(body, url)
                logging.debug("found {} links".format(len(self._links)))
                self._browse_from_links()

            except requests.exceptions.RequestException as e:
                logging.warn("Error connecting to root url: {}".format(url))
                logging.warn(e)
                
            except MemoryError:
                logging.warn("Error: content at url: {} is exhausting the memory".format(url))

            except LocationParseError:
                logging.warn("Error encountered during parsing of: {}".format(url))

            except self.CrawlerTimedOut:
                logging.info("Timeout has exceeded, exiting")
                return

def main(config_file,timeout,source,log_level='info',roots=[],depth=0):
    level = getattr(logging, log_level.upper())
    logging.basicConfig(level=level)

    crawler = Crawler(source)
    crawler.load_config_file(config_file)
    if roots is not [] and len(roots) != 0:
        crawler.set_option("root_urls",[roots])
    if depth != 5: # default of calling function which will always override the functions default
        crawler.set_option("max_depth",depth)

    if timeout is not None:
        crawler.set_option('timeout', int(timeout))
    else:
        raise Exception("No timeout")
    crawler.crawl()