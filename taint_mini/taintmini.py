import os
import time
from .wxjs import gen_pdg, handle_wxjs
from .wxml import handle_wxml
from .inter_page import handle_inter_page_data, add_inter_page_data
from .storage import Storage
import multiprocessing as mp


def filter_results(results, config):
    # no filters, just return
    if ("sources" not in config or len(config["sources"]) == 0) and \
            ("sinks" not in config or len(config["sinks"]) == 0):
        return results

    filtered = {}
    for page in results:
        filtered[page] = []
        for flow in results[page]:
            # filter source
            if "sources" in config and len(config["sources"]) > 0:
                if "sinks" in config and len(config["sinks"]) > 0:
                    # apply source and sink filter
                    if flow['source'] in config["sources"] and flow['sink'] in config["sinks"]:
                        filtered[page].append(flow)
                    # handle double binding in source
                    if "[double_binding]" in config["sources"] and "[data from" in flow['source'] \
                            and flow['sink'] in config["sinks"]:
                        filtered[page].append(flow)
                else:
                    # no sink filter, just apply source filter
                    if flow['sink'] in config["sinks"]:
                        filtered[page].append(flow)
            else:
                # no source filter, apply sink filter
                if "sinks" in config and len(config["sinks"]) > 0:
                    # apply sink filter
                    if flow['sink'] in config["sinks"]:
                        filtered[page].append(flow)
        # remove empty entries
        if len(filtered[page]) == 0:
            filtered.pop(page)
    return filtered


def analyze_worker(app_path, page_path, results_path, config, queue, inter_page_queue):
    # generate pdg first
    r = gen_pdg(os.path.join(app_path, "pages", f"{page_path}.js"), results_path)
    # init shared storage (per process)
    Storage.init(r, app_path, page_path, config)
    # analyze double binding
    handle_wxml(os.path.join(app_path, "pages", f"{page_path}.wxml"))
    # analyze data flow
    handle_wxjs(r)
    # retrieve results
    storage = Storage.get_instance()
    inter_page_queue.put(storage)
    # filter results
    filtered = filter_results(storage.get_results(), config)
    # send results
    queue.put(filtered)


def analyze_listener(result_path, queue):
    with open(result_path, "w") as f:
        f.write("page_name|page_method|ident|source|sink\n")
        while True:
            message = queue.get()
            if message == "kill":
                break
            if isinstance(message, dict):
                for page in message:
                    for flow in message[page]:
                        f.write(f"{page}|{flow['method']}|{flow['ident']}|{flow['source']}|{flow['sink']}\n")
                f.flush()
        f.flush()


def inter_page_analyze_listener(result_path, queue):
    with open(result_path, "w") as f:
        f.write("from_page|to_page|event_name|source|sink\n")
        while True:
            message = queue.get()
            if message == "kill":
                try:
                    # array of result
                    results = handle_inter_page_data()
                    for result in results:
                        f.write(f"{result['from_page']}|{result['to_page']}|{result['event_name']}|"
                                f"{result['source']}|{result['sink']}\n")
                    f.flush()
                except Exception as e:
                    print(f"[inter_page listener] error: {e}")
                break
            if isinstance(message, Storage):
                # add storage to inter_page_storage
                add_inter_page_data(message)


def obtain_valid_page(files):
    sub_pages = set()
    for f in files:
        sub_pages.add(str.split(f, ".")[0])
    for f in list(sub_pages):
        if f"{f}.js" not in files or f"{f}.wxml" not in files:
            sub_pages.remove(f)
    return sub_pages


def retrieve_pages(app_path):
    pages = set()
    for root, dirs, files in os.walk(os.path.join(app_path, "pages/")):
        for s in obtain_valid_page(files):
            pages.add(f"{root[len(os.path.join(app_path, 'pages/')):]}/{s}")
    return pages


def analyze_mini_program(app_path, results_path, config, workers, bench):
    if not os.path.exists(app_path):
        print("[main] invalid app path")

    # obtain pages
    pages = retrieve_pages(app_path)
    if len(pages) == 0:
        print(f"[main] no page found")
        return

    # prepare output path
    if not os.path.exists(results_path):
        os.mkdir(results_path)
    elif os.path.isfile(results_path):
        print(f"[main] error: invalid output path")
        return

    manager = mp.Manager()
    queue = manager.Queue()
    inter_page_queue = manager.Queue()
    pool = mp.Pool(workers + 2 if workers is not None else mp.cpu_count())

    # put listeners to pool first
    pool.apply_async(analyze_listener, (os.path.join(results_path, f"{os.path.basename(app_path)}-result.csv"), queue))
    pool.apply_async(inter_page_analyze_listener, (os.path.join(results_path, f"{os.path.basename(app_path)}-inter-page"
                                                                              f"-result.csv"), inter_page_queue))

    bench_out = None
    if bench:
        bench_out = open(os.path.join(results_path, f"{os.path.basename(app_path)}-bench.csv"), "w")
        bench_out.write("page|start|end\n")

    # execute workers
    workers = dict()
    for p in pages:
        workers[p] = dict()
        workers[p]["job"] = pool.apply_async(analyze_worker,
                                             (app_path, p, results_path, config, queue, inter_page_queue))
        if bench:
            workers[p]["begin_time"] = int(time.time())

    # collect results
    for p in pages:
        try:
            workers[p]["job"].get()
        except Exception as e:
            print(f"[main] critical error: {e}")
        finally:
            if bench:
                workers[p]["end_time"] = int(time.time())

    queue.put("kill")
    inter_page_queue.put("kill")
    pool.close()
    pool.join()

    if bench and bench_out is not None:
        for p in pages:
            bench_out.write(f"{p}|{workers[p]['begin_time']}|{workers[p]['end_time']}\n")
        bench_out.close()
