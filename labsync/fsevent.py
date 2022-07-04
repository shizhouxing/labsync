import re
from watchdog.events import (FileSystemEventHandler, PatternMatchingEventHandler,
                            DirCreatedEvent, FileCreatedEvent, DirModifiedEvent, FileModifiedEvent,
                            EVENT_TYPE_CREATED, EVENT_TYPE_DELETED, EVENT_TYPE_MODIFIED, EVENT_TYPE_MOVED)
from fnmatch import fnmatch


class FSEventHandler(PatternMatchingEventHandler):
    def __init__(self, synchronizer, patterns=None, ignore_patterns=None, 
                ignore_patterns_re=[]):
        super().__init__(patterns, ignore_patterns)
        self.synchronizer = synchronizer
        self.paused = False
        self.ignore_patterns_re = [re.compile(pattern) for pattern in ignore_patterns_re]

    def dispatch(self, event):
        if self.paused:
            pass
        else:
            for pattern in self.ignore_patterns_re:
                if pattern.match(event.src_path):
                    return 
            super().dispatch(event) 

    def on_moved(self, event):
        self.synchronizer.mv(event.src_path, event.dest_path)

    def on_created(self, event):
        if isinstance(event, DirCreatedEvent):
            self.synchronizer.mkdir(event.src_path)
        elif isinstance(event, FileCreatedEvent):
            self.synchronizer.upload(event.src_path)
        else:
            raise TypeError

    def on_deleted(self, event):
        # Ignore the deletion event.
        pass

    def on_modified(self, event):
        if isinstance(event, DirModifiedEvent):
            # Handle specific files in the directory, but not the directory itself
            pass
        elif isinstance(event, FileModifiedEvent):
            self.synchronizer.upload(event.src_path)          
        else:
            raise TypeError

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False