class Storage:
    instance = None
    node = None
    results = None
    app_path = None
    page_path = None
    events = None
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
        # data structure: {
        #   [page_name]: [
        #       { method: [method_name],
        #         event_name: [event_name],
        #         event_type: [emit|on],
        #         event_call_expr: [call_expr],
        #         event_data_source: set([source]),
        #         event_emitter: [event_emitter]
        #       },
        #    ]
        #  }
        self.events = dict()
        self.config = _config

    def get_node(self):
        return self.node

    def get_results(self):
        return self.results

    def get_app_path(self):
        return self.app_path

    def get_page_path(self):
        return self.page_path

    def get_events(self):
        return self.events

    def get_config(self):
        return self.config

    @staticmethod
    def init(_node, _app_path, _page_path, _config):
        Storage.instance = Storage(_node, _app_path, _page_path, _config)

    @staticmethod
    def get_instance():
        return Storage.instance


class InterPageStorage:
    instance = None
    page_asts = None
    page_results = None
    page_events = None
    inter_page_results = None

    def __init__(self):
        self.page_asts = dict()
        self.page_results = dict()
        self.page_events = dict()
        self.inter_page_results = list()

    def add_page_ast(self, page_name, ast_root):
        self.page_asts[page_name] = ast_root

    def get_page_asts(self):
        return self.page_asts

    def add_page_results(self, results):
        for page in results:
            self.page_results[page] = results[page]

    def add_page_events(self, events):
        for page in events:
            self.page_events[page] = events[page]

    def get_page_results(self):
        return self.page_results

    def get_page_events(self):
        return self.page_events

    @staticmethod
    def init():
        InterPageStorage.instance = InterPageStorage()

    @staticmethod
    def get_instance():
        return InterPageStorage.instance
