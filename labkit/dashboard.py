import sys
import os
import time
import logging
import subprocess
import labkit.utils
from threading import Thread
from labkit.frontend.app import app

logger = logging.getLogger(__name__)

class Dashboard(Thread):
    def __init__(self, config, tensorboard=None):
        super().__init__()
        self.port = config.get('port', 3000)
        self.tensorboard = tensorboard
        self.app = app
        self.app.data = {}
        if tensorboard is not None:
            self.app.data['tensorboard'] = tensorboard.port

    def run(self):
        self.app.run(port=self.port)