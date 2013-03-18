# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import sys
import codecs
import logging

from plumbum import cli


class UPaaSApplication(cli.Application):

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
