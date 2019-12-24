#!/home/ubuntu/.pyenv/shims/python
# -*- coding: utf-8 -*-
# watch.py

import time
import os
from threading import Timer
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

# ----------------------------------------------------------------------------
# Current dir for batch
filedir = os.path.dirname(os.path.realpath(__file__))
os.chdir(filedir)
print("chdir=%s" % filedir)

class MyHandler(PatternMatchingEventHandler):
    i = 0

    def _reset_i(self):
        self.i = 0

    def on_modified(self, event):
        self.i += 1  # firing 3 events when modified
        if self.i == 1:
            if event.src_path.endswith('.js') or event.src_path.endswith('.css'):
                print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())),
                if event.src_path.endswith('.js'):
                    os.system('make js')
                elif event.src_path.endswith('.css'):
                    os.system('make css')
                print('task finalized, continue watching...')
            t = Timer(2.0, self._reset_i)
            t.start()

if __name__ == "__main__":
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()
    os.system('touch portal.js')  # always refresh at start watching, pushの後にリフレッシュが便利
    os.system('make css')                 #
    print('Start watching...')
    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    print('\nEnd watching...')
# End
