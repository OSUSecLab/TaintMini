from .storage import InterPageStorage


def add_inter_page_data(storage):
    if InterPageStorage.get_instance() is None:
        InterPageStorage.init()
    inter_page_storage = InterPageStorage.get_instance()
    inter_page_storage.add_page_ast(storage.get_page_path(), storage.get_node())
    inter_page_storage.add_page_results(storage.get_results())
    inter_page_storage.add_page_events(storage.get_events())
    print(f"[inter_page add] got new page data: {storage.get_page_path()}")


def handle_inter_page_data():
    if InterPageStorage.get_instance() is None:
        raise ValueError("[inter page] instance is None")
    page_asts = InterPageStorage.get_instance().get_page_asts()
    page_results = InterPageStorage.get_instance().get_page_results()
    page_events = InterPageStorage.get_instance().get_page_events()
    return resolve_inter_page_flows(page_asts, page_results, page_events)


def resolve_inter_page_flows(page_asts, page_results, page_events):
    if len(page_events) == 0:
        print(f"[inter_page resolve] no events found in pages, skipping")
        return

    print(f"[inter_page resolve] resolving flows within {len(page_events)} pages")
    results = list()
    for page in page_events:
        # for now, we only handles sinks from onLoad
        for event in page_events[page]:
            if event["method_name"] == "onLoad" and event["event_type"] == "on" \
                    and event["event_emitter"] == "this.getOpenerEventChannel" \
                    and event["event_data_sink"] is not None:
                # got opener channel event, finding source
                event_emit_sources = find_event_emit_source(page_events, event["event_name"])
                for emit_source in event_emit_sources:
                    print(f"[inter_page flow] got inter page flow: page {emit_source['page_name']} --> {page}, "
                          f"event: {event['event_name']}, source: {emit_source['event_data_source']}"
                          f" to sink: {event['event_data_sink']}")
                    results.append({
                        "from_page": emit_source["page_name"],
                        "to_page": page,
                        "event_name": event["event_name"],
                        "source": emit_source["event_data_source"],
                        "sink": event["event_data_sink"]
                    })
    print(f"[inter_page resolve] resolving finished, got {len(results)} inter page flow(s)")
    return results


def find_event_emit_source(page_events, event_name):
    emit_sources = list()
    for page in page_events:
        for event in page_events[page]:
            # don't handle "on" type event and ignore different event
            if event["event_type"] != "emit" or event["event_name"] != event_name:
                continue
            # don't handle event emitter that does not from wx.navigateTo
            # this can be improved to find general events but for now, we
            # only handle wx.navigateTo event channel
            if event["event_emitter"] != "wx.navigateTo":
                continue
            for source in event["event_data_source"]:
                # filter those source points to wx.navigateTo
                if source != "wx.navigateTo":
                    emit_sources.append({
                        "page_name": page,
                        "event_data_source": source
                    })
    return emit_sources

