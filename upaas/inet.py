# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from netifaces import interfaces, ifaddresses, AF_INET


def local_ipv4_addresses():
    ip_list = []
    for interface in interfaces():
        for link in ifaddresses(interface).get(AF_INET, []):
            if link['addr'] != '127.0.0.1':
                ip_list.append(link['addr'])
    return ip_list
