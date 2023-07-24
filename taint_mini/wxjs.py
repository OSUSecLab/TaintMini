from collections import deque
from pdg_js import node as _node
from pdg_js.build_pdg import get_data_flow
from .storage import Storage


def gen_pdg(file_path, results_path):
    return get_data_flow(file_path, benchmarks=dict(), alt_json_path=f"{results_path}/intermediate-data/")


def handle_wxjs(r):
    results = Storage.get_instance().get_results()
    results[Storage.get_instance().get_page_path()] = list()
    events = Storage.get_instance().get_events()
    events[Storage.get_instance().get_page_path()] = list()
    find_page_methods_node(r)


def find_page_methods_node(r):
    for child in r.children:
        if child.name == "ExpressionStatement":
            if len(child.children) > 0 \
                    and child.children[0].name == "CallExpression" \
                    and child.children[0].children[0].attributes["name"] == "Page":
                # found page expression
                for method_node in child.children[0].children[1].children:
                    if method_node.attributes["value"]["type"] == "FunctionExpression":
                        # handle node
                        method_name = method_node.children[0].attributes['name']
                        print(
                            f"[page method] got page method, method name: {method_name}")
                        try:
                            dfs_search(method_node, method_name)
                        except Exception as e:
                            print(f"[wxjs] error in searching method {method_name}: {e}")


def find_nearest_call_expr_node(node):
    return node if node is not None and \
           hasattr(node, "name") and isinstance(node, _node.ValueExpr) and node.name == "CallExpression" \
           else find_nearest_call_expr_node(node.parent if node.parent is not None else None)


def find_nearest_function_expr_node(node):
    return node if node is not None and \
           hasattr(node, "name") and isinstance(node, _node.FunctionExpression) and node.name == "FunctionExpression" \
           else find_nearest_function_expr_node(node.parent if node.parent is not None else None)


def find_success_property_function_expr_node(node):
    if node is None:
        return None
    return node if node is not None and \
        hasattr(node, "name") and isinstance(node, _node.Node) and node.name == "Property" \
        and len(node.children) == 2 and isinstance(node.children[0], _node.Identifier) \
        and "name" in node.children[0].attributes \
        and node.children[0].attributes["name"] == "success" \
        else find_success_property_function_expr_node(node.parent
                                                      if node.parent is not None
                                                      else None)


def obtain_callee_from_member_expr(node):
    def traverse(_n, _callee):
        for _nn in _n.children:
            if hasattr(_nn, "name") and _nn.name == "ThisExpression":
                _callee.append("this")
                continue
            if not isinstance(_nn, _node.Identifier):
                traverse(_nn, _callee)
            if "name" in _nn.attributes:
                _callee.append(_nn.attributes["name"])
    if node.name != "MemberExpression":
        return None
    callee = list()
    traverse(node, callee)
    return ".".join(callee) if len(callee) != 0 else None


def obtain_callee_from_call_expr(node):
    if len(node.children[0].children) == 0 and node.children[0].attributes["name"] != "Page":
        return node.children[0].attributes["name"]
    if hasattr(node.children[0], "name") and node.children[0].name == "MemberExpression":
        return obtain_callee_from_member_expr(node.children[0])
    return ".".join([i.attributes["name"] if "name" in i.attributes else "" for i in node.children[0].children])


def obtain_var_decl_callee(node):
    if(len(node.children)==0):
        return ""
    return ".".join([i.attributes["name"] for i in node.children[0].children])


def obtain_value_expr_callee(node):
    return ".".join([i.attributes["name"] for i in node.children])


def obtain_data_flow_sink(dep):
    # check if the dependence node has CallExpression parent
    if isinstance(dep.extremity.parent, _node.ValueExpr):
        return obtain_value_expr_callee(dep.extremity.parent.children[0])
    return None


def handle_data_parent_node(node):
    source = check_immediate_data_dep_parent(node)
    # if no known pattern match, fall back to general search
    if source is None:
        call_expr_node = find_nearest_call_expr_node(node)
        source = obtain_callee_from_call_expr(call_expr_node)
        print(f"[taint source] got nearest callee (source): {source}")

    # obtain sink
    sink = []
    for child in node.data_dep_children:
        s = obtain_callee_from_call_expr(find_nearest_call_expr_node(child.extremity))
        if s is not None:
            print(f"[taint sink] got data flow sink: {s}")
            sink.append(s)

    print(f"[flow path] data identifier: {node.attributes['name']}, "
          f"from source: {source if source is not None else 'None'}, "
          f"to sink: {','.join(map(str, sink))}")


def is_parent_var_decl_or_assign_expr(node):
    return isinstance(node.parent, _node.Node) and \
        hasattr(node.parent, "name") and \
        (node.parent.name == "VariableDeclarator" or node.parent.name == "AssignmentExpression")


def check_immediate_data_dep_parent(node):
    # check the data dep parent node is assignment or var decl
    # this check suitable for var_decl -> further usage
    source = None
    source_call_expr = None
    if is_parent_var_decl_or_assign_expr(node):
        # variable declaration or assignment, check the call expr
        if len(node.parent.children) > 1 and isinstance(node.parent.children[1], _node.ValueExpr):
            # obtain callee if parent is call expr
            if hasattr(node.parent.children[1], "name") and node.parent.children[1].name == "CallExpression":
                source = obtain_callee_from_call_expr(node.parent.children[1])
                source_call_expr = node.parent.children[1]

            # obtain callee if parent is var decl
            if source is None:
                source = obtain_var_decl_callee(node.parent.children[1])
                source_call_expr = node.parent.children[1]
            print(f"[taint source] got data flow source: {source}, identifier: {node.attributes['name']}")
    return source, source_call_expr


def is_page_method_parameter(node):
    if not isinstance(node, _node.Identifier):
        return False
    # in AST tree, ident -> FunctionExpr -> Property -> ObjectExpr
    # -> CallExpr <- Ident (Page)
    try:
        if node.parent.parent.parent.parent \
                .children[0].attributes["name"] == "Page":
            return True
    except IndexError:
        return False
    except AttributeError:
        return False
    except KeyError:
        return False


def get_input_name(value):
    return value[value.rindex(".") + 1:] if isinstance(value, str) and "detail.value" in value else None


def handle_page_method_parameter(node, _n):
    # handle double binding values
    if not isinstance(node, _node.Identifier) or not isinstance(_n, _node.Identifier):
        return None
    # key is double_binding_values in ident node
    # omit it since false-negatives
    # if "double_binding_values" not in _n.attributes:
    #     return None
    sources = set()
    # handle form double binding (input)
    # pattern: e.detail.value.[id]
    if isinstance(node.value, dict):
        for i in node.value:
            if isinstance(node.value[i], str) and "detail.value" in node.value[i]:
                input_name = get_input_name(node.value[i])
                if input_name is None or input_name not in _n.attributes["double_binding_values"]:
                    continue
                sources.add((f"[data from double binding: {input_name}, "
                            f"type: {_n.attributes['double_binding_values'][input_name]}]", None))
    elif isinstance(node.value, str) and "detail.value" in node.value:
        input_name = get_input_name(node.value)
        if input_name is not None and input_name in _n.attributes["double_binding_values"]:
            sources.add((f"[data from double binding: {input_name}, "
                        f"type: {_n.attributes['double_binding_values'][input_name]}]", None))

    # if no double binding found, fall back to general resolve
    if len(sources) == 0:
        sources.add((f"[data from page parameter: {node.value}]", None))
    return sources


def handle_data_dep_parents(node):
    """
    @return set of sources
    """
    sources = set()
    # check immediate data dep parent node first
    source, source_call_expr = check_immediate_data_dep_parent(node)
    if source is not None:
        sources.add((source, source_call_expr))
        return sources

    # no source found, fall back to general search
    source_call_expr = find_nearest_call_expr_node(node)
    source = obtain_callee_from_call_expr(source_call_expr)
    if source is not None and source != "":
        sources.add((source, source_call_expr))
        return sources

    # no call expr found, search from provenance parents
    for n in node.provenance_parents_set:
        # check ident
        if isinstance(n, _node.Identifier):
            # check if it's page method parameter first
            if is_page_method_parameter(n):
                # is page method parameter, handle double binding
                # notice here should analyze the original node,
                # not the provenance parent node
                r = handle_page_method_parameter(node, n)
                if r is not None:
                    sources.update(r)
                continue

            # search for source from var decl or assignment expr
            r_call_expr = None
            r = check_immediate_data_dep_parent(n)
            if r is None:
                # no results found, fall back to general search
                r_call_expr = find_nearest_call_expr_node(n)
                r = obtain_callee_from_call_expr(r_call_expr)

            # still no results
            if r is None or r == "" or r_call_expr is None:
                continue
            # found source, add to set
            sources.add((r, r_call_expr))
        # normal node, don't handle it
        if isinstance(n, _node.Node):
            continue
        # value expr, don't handle it
        if isinstance(n, _node.ValueExpr):
            continue
    # end for
    return sources


def resolve_event_emitter(call_expr):
    event_emitter = None
    # try if it's from success property function
    success_property_func_expr = find_success_property_function_expr_node(call_expr)
    if success_property_func_expr is not None:
        # TODO: need to check if it's from 'success' property,
        #       static name check may have FP, need to check
        #       that via data flow
        # such call expr must exist
        event_emitter = obtain_callee_from_call_expr(find_nearest_call_expr_node(success_property_func_expr))
        return event_emitter
    # now, looks like we cannot find it from success property function
    # let's find it from its immediate source
    call_expr_callee_indent = call_expr.children[0].children[0]
    for data_parent in call_expr_callee_indent.provenance_parents_set:
        if hasattr(data_parent, "name") and data_parent.name == "MemberExpression" \
                and hasattr(data_parent, "body") and data_parent.body == "callee":
            tmp_event_emitter = obtain_callee_from_member_expr(data_parent)
            if tmp_event_emitter is not None:
                event_emitter = tmp_event_emitter
                break
    return event_emitter


def handle_event_call_expr(call_expr, method_name, event_type, sources=None, sink=None):
    # test if event call expr
    if len(call_expr.children) != 3:
        return
    elif call_expr.children[1].name != "Literal":
        return

    events = Storage.get_instance().get_events()
    event_name = call_expr.children[1].attributes["value"]
    event_emitter = resolve_event_emitter(call_expr)
    # could not resolve any emitter, return
    if event_emitter is None:
        return
    print(f"[events] got new event in method {method_name}, event name: {event_name}, type: {event_type}"
          f", event emitter: {event_emitter}, data from: {sources}, data to: {sink}")
    events[Storage.get_instance().get_page_path()].append({
        "method_name": method_name,
        "event_type": event_type,
        "event_name": event_name,
        "event_call_expr": call_expr,
        "event_data_source": sources,
        "event_data_sink": sink,
        "event_emitter": event_emitter
    })


def handle_data_child_node(node, method_name):
    if hasattr(node, "data_dep_children") and len(node.data_dep_children) > 0:
        # this node has data dep children (intermediate node), won't handle it
        return

    # no more children, it's the last node of the data flow
    # resolve sink api if the parent node is call expr
    sink_call_expr = find_nearest_call_expr_node(node)
    sink = obtain_callee_from_call_expr(sink_call_expr)
    if sink == "":
        print(f"[taint sink] no sink api resolved, passing...")
        return
    print(f"[taint sink] got data flow sink: {sink}, resolving data flow source")

    # resolve data source
    # annotation, comment for low python version
    # sources: set[tuple[str, _node.Node | None]] = set()
    sources = set()
    data_dep_parent_nodes = node.data_dep_parents
    for n in data_dep_parent_nodes:
        s = handle_data_dep_parents(n.extremity)
        if s is not None:
            sources.update(s)

    if len(sources):
        print(f"[taint source] resolve data sources: {', '.join([s[0] for s in sources])}")
    else:
        print(f"[taint source] no valid source found")

    # flow path
    if len(sources):
        try:
            if sink.endswith("on"):
                handle_event_call_expr(sink_call_expr, method_name, "on", sources=set([s[0] for s in sources]))
            elif sink.endswith("emit"):
                handle_event_call_expr(sink_call_expr, method_name, "emit", sources=set([s[0] for s in sources]))
        except AttributeError as e:
            print(f"[event flow] failed to resolve events: {e}")

        print(f"[flow path] data identifier: {node.attributes['name']}, "
              f"from source: {', '.join([s[0] for s in sources])}, "
              f"to sink: {sink}")
        results = Storage.get_instance().get_results()
        for source in sources:
            source_name = source[0]
            source_call_expr = source[1]
            # if source is same as sink, ignore it
            if source_name == sink:
                continue
            try:
                if source_name.endswith("on"):
                    handle_event_call_expr(source_call_expr, method_name, "on", sink=sink)
                elif source_name.endswith("emit"):
                    handle_event_call_expr(source_call_expr, method_name, "emit", sink=sink)
            except AttributeError as e:
                print(f"[event flow] failed to resolve events: {e}")
            results[Storage.get_instance().get_page_path()].append({
                "method": method_name,
                "ident": node.attributes['name'],
                "source": source_name,
                "sink": sink
            })


def handle_identifier_node(node, method_name):
    # if hasattr(node, "data_dep_children") and len(node.data_dep_children) > 0:
    #     print("[handle ident] got data flow parent node")
    #     handle_data_parent_node(node)

    # search backwards (from children)
    if hasattr(node, "data_dep_parents") and len(node.data_dep_parents) > 0:
        print("[handle ident] got data flow child node")
        # omit backwards search
        handle_data_child_node(node, method_name)


def dfs_visit(node, method_name):
    if not isinstance(node, _node.Identifier):
        # print("normal node, passing")
        return

    handle_identifier_node(node, method_name)


def dfs_search(r, n):
    stack = deque()
    stack.append(r)

    visited = []

    while stack:
        v = stack.pop()
        if v in visited:
            continue

        # node is not visited
        visited.append(v)
        dfs_visit(v, n)

        # visit its children
        children = v.children
        for i in reversed(children):
            if i not in visited:
                stack.append(i)
