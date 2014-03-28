# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import sys
import codecs
import logging
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

from plumbum import cli

from slumber.exceptions import SlumberHttpBaseException

from upaas.client import UpaasAPI


class UPaaSApplication(cli.Application):

    api = None
    log = None
    log_level = "warning"
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
                                      logging.WARNING))

    def api_connect(self, login, apikey, url):
        if not self.api:
            url = urljoin(url, '/api/v1/')
            self.log.info("Connecting to API at '%s' as '%s'" % (url, login))
            self.api = UpaasAPI(login, apikey, url)

    def print_msg(self, msg, prefix=">>"):
        if prefix:
            prefix += " "
        for line in msg.splitlines():
            print(("%s%s" % (prefix or '', line)))

    def handle_error(self, err):
        if isinstance(err, SlumberHttpBaseException):
            if err.response.status_code == 401:
                self.log.error("Authentication error")
            elif err.content:
                self.log.error(err.content)
            else:
                self.log.error(err)
        else:
            self.log.error(err)
