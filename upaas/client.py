# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import requests

from slumber import API


class UpaasAPI(API):

    def __init__(self, login, apikey, *args, **kwargs):
        session = requests.Session()
        session.headers.update({
            'X-UPAAS-LOGIN': login,
            'X-UPAAS-APIKEY': apikey,
        })
        kwargs['session'] = session
        super(UpaasAPI, self).__init__(*args, **kwargs)
