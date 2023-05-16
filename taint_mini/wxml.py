from lxml.html import parse
from .storage import Storage


def handle_wxml(file):
    try:
        wxml_html_root = parse(file)
        visit_wxml_tree(wxml_html_root)
    except Exception as e:
        print(f"[wxml] got error: {e}")


def find_page_method_node(root, name):
    for child in root.children:
        if child.name == "ExpressionStatement":
            if len(child.children) > 0 \
                    and child.children[0].name == "CallExpression" \
                    and child.children[0].children[0].attributes["name"] == "Page":
                # found page expression
                for method_node in child.children[0].children[1].children:
                    if method_node.attributes["value"]["type"] == "FunctionExpression":
                        # handle node
                        if method_node.children[0].attributes["name"] == name:
                            return method_node


def tag_properties_to_page_method_param_ident_node(node, p):
    # Function [1] -> FunctionExpr [0] -> Ident
    node.children[1].children[0].attributes["double_binding_values"] = p["inputs"]


def handle_form_properties(p):
    root = Storage.get_instance().get_node()
    node = find_page_method_node(root, p["bind_submit"])
    tag_properties_to_page_method_param_ident_node(node, p)


def handle_wxml_form(element):
    visited_elements_in_form = []
    form_properties = dict()
    # mapping: key name -> type
    form_properties["inputs"] = dict()

    for e in element.iter():
        visited_elements_in_form.append(e)

        # handle form bind:submit
        if e.tag == "g-form" or e.tag == "form":
            if hasattr(e, "attrib") and "bind:submit" in e.attrib:
                form_properties["bind_submit"] = e.attrib["bind:submit"]
                continue

        # handle input properties
        if (e.tag == "g-input" or e.tag == "input") and hasattr(e, "attrib") \
                and ("name" in e.attrib or "id" in e.attrib):
            # handle password
            if "password" in e.attrib or ("type" in e.attrib and e.attrib["type"] == "safe-password"):
                form_properties["inputs"][e.attrib["name"] if "name" in e.attrib else e.attrib["id"]] = "password"
                continue
            # handle normal input
            if "type" in e.attrib:
                form_properties["inputs"][e.attrib["name"] if "name" in e.attrib else e.attrib["id"]] = e.attrib["type"]
                continue

    # handle the properties
    if form_properties["bind_submit"] is not None:
        handle_form_properties(form_properties)
    # return the visited elements in this form
    return visited_elements_in_form


def handle_wxml_element(element):
    pass


def visit_wxml_tree(r):
    visited = []

    def visit_node(v):
        visited.append(v)
        # handle form element
        # as a form may have many child input elements
        if hasattr(v, "tag") and (v.tag == "g-form" or v.tag == "form"):
            # multiple elements are visited in handling form element
            visited.extend(handle_wxml_form(v))
            return

        # handle normal xml element
        handle_wxml_element(v)

    # iter all the elements
    for i in r.iter():
        if i not in visited:
            visit_node(i)


