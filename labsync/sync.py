import os

class Synchronizer:
    def __init__(self, servers, local_root):
        self.servers = servers
        for server in self.servers:
            if not server.is_alive():
                server.start()

    def _add_task(self, task):
        for server in self.servers:
            server.add_task(task)

    def _parse_path(self, path):
        return os.path.relpath(path)

    def upload(self, path):
        self._add_task({
            'action': 'upload',
            'path': self._parse_path(path)
        })

    def mkdir(self, path):
        self._add_task({
            'action': 'mkdir',
            'path': self._parse_path(path)
        })

    def mv(self, src_path, dest_path):
        self._add_task({
            'action': 'mv',
            'src_path': self._parse_path(src_path),
            'dest_path': self._parse_path(dest_path)
        })