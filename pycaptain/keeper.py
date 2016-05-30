# -*- coding: utf-8 -*-
# pylint: disable=all
'''
captain client implementation
'''

import time
import threading
import traceback
from requests.exceptions import RequestException


class ServiceKeeper(object):
    '''
    service keeper thread
    '''
    def __init__(self, client):
        self.client = client
        self.stop_event = threading.Event()
        self.keepalive = 10
        self.check_interval = 1000
        self.last_keep_ts = 0

    def start(self):
        t = threading.Thread(target=self.loop)
        t.daemon = True
        t.start()

    def loop(self):
        while not self.stop_event.is_set():
            self.client.shuffle_origin()
            try:
                self.watch()
            except RequestException:
                traceback.print_exc()
            try:
                self.keep()
            except RequestException:
                traceback.print_exc()
            self.stop_event.wait(self.check_interval/1000.0)

    def watch(self):
        flags = self.client.check_dirty()
        if flags[0]:
            dirties = self.client.check_service_versions()
            for name in dirties:
                self.client.reload_service(name)
        if flags[1]:
            dirties = self.client.check_kv_versions()
            for key in dirties:
                self.client.reload_kv(key)

    def keep(self):
        now = int(time.time())
        if now - self.last_keep_ts > self.keepalive:
            self.client.keep_service()
            self.last_keep_ts = now

    def quit(self):
        self.stop_event.set()
