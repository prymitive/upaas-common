# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import sys
import codecs
import logging
from urlparse import urljoin

from plumbum import cli

from upaas.client import UpaasAPI


class UPaaSApplication(cli.Application):

    api = None
    log = None
    log_level = "info"
    log_output = "-"

    @cli.switch(["l", "log-level"], str, help="Logging level")
    def set_log_level(self, level):
        self.log_level = level

    @cli.switch(["o", "log-output"], str, help="Log file ('-' for console)")
    def set_log_output(self, output):
        self.log_output = output

    def setup_logger(self):
        if self.log_output == "-":
            handler = logging.StreamHandler(
                codecs.getwriter('utf-8')(sys.stdout))
        else:
            handler = logging.FileHandler(self.log_output, encoding='utf-8')

        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s: %(message)s",
                              "%Y-%m-%d %H:%M:%S"))
        self.log = logging.getLogger()
        if not len(self.log.handlers):
            self.log.addHandler(handler)

            self.log.setLevel(getattr(logging, self.log_level.upper(),
                                      logging.INFO))

    def api_connect(self, login, apikey, url):
        if not self.api:
            url = urljoin(url, '/api/v1/')
            self.log.info("Connecting to API at '%s' as '%s'" % (url, login))
            self.api = UpaasAPI(login, apikey, url)
