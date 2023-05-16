class Storage:
    instance = None
    node = None
    results = None
    app_path = None
    page_path = None
    config = None

    def __init__(self, _node, _app_path, _path_path, _config):
        self.node = _node
        # data structure: {
        #   [page_name]: [
        #     { method: [method_name],
        #       source: [source_name],
        #       sink:   [sink_name]
        #     },
        #   ]
        # }
        self.results = dict()
        self.app_path = _app_path
        self.page_path = _path_path
        self.config = _config

    def get_node(self):
        return self.node

    def get_results(self):
        return self.results

    def get_app_path(self):
        return self.app_path

    def get_page_path(self):
        return self.page_path

    def get_config(self):
        return self.config

    @staticmethod
    def init(_node, _app_path, _page_path, _config):
        Storage.instance = Storage(_node, _app_path, _page_path, _config)

    @staticmethod
    def get_instance():
        return Storage.instance
