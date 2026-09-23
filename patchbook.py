#!/usr/bin/env python3
"""
PATCHBOOK MARKUP LANGUAGE & PARSER
CREATED BY SPEKTRO AUDIO
http://spektroaudio.com/
"""

import sys
import re
import os
import argparse
import json

# Parser INFO
parserVersion = "b3"

# Reset main dictionary
mainDict = {
    "info": {"patchbook_version": parserVersion},
    "modules": {},
    "comments": []
}

# Available connection types
connectionTypes = {
    "->": "audio",
    ">>": "cv",
    "p>": "pitch",
    "g>": "gate",
    "t>": "trigger",
    "c>": "clock"
}

graphVizRemoveChars = "[- /]"

# Reset global variables
lastModuleProcessed = ""
lastVoiceProcessed = ""

# Parse script arguments
parser = argparse.ArgumentParser()
parser.add_argument("-file", type=str, default="",
                    help="Name of the text file that will be parsed (including extension)")
parser.add_argument("-debug", type=int, default=0,
                    help="Enable Debugging Mode")
parser.add_argument("-dir", type=str, default="LR",
                    help="Graph direction: LR (left-to-right) or DN (top-to-bottom)")
parser.add_argument("-modules", action="store_const", const="modules", dest="command",
                    help="Print all modules")
parser.add_argument("-print", action="store_const", const="print", dest="command",
                    help="Print data structure")
parser.add_argument("-export", action="store_const", const="export", dest="command",
                    help="Print JSON")
parser.add_argument("-connections", action="store_const", const="connections", dest="command",
                    help="Print connections")
parser.add_argument("-graph", action="store_const", const="graph", dest="command",
                    help="Print dot code for graph")
parser.add_argument("-d2", action="store_const", const="d2", dest="command",
                    help="Print D2 code for diagram")
args = parser.parse_args()
filename = args.file
debugMode = args.debug
direction = args.dir
if args.command:
    one_shot_command = args.command
    quiet = True
else:
    one_shot_command = None
    quiet = False

connectionID = 0

# Set up debugMode
if args.debug == 1:
    debugMode = True
else:
    debugMode = False


def initial_print():
    global quiet
    if not quiet:
        print()
        print("██████████████████████████████")
        print("       PATCHBOOK PARSER       ")
        print("   Created by Spektro Audio   ")
        print("██████████████████████████████")
        print()
        print("Version " + parserVersion)
        print()


def get_script_path():
    # Get path to python script
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def getFilePath(filename):
    try:
        # Append script path to the filename
        base_dir = get_script_path()
        filepath = os.path.join(base_dir, filename)
        if debugMode:
            print("File path: " + filepath)
        return filepath
    except IndexError:
        pass


def parseFile(filename):
    # This function reads the txt file and process each line.
    global quiet
    try:
        if not quiet: print("Loading file: " + filename)
        with open(filename, "r") as file:
            for l in file:
                if not l.endswith("\n"):
                    l += "\n"
                regexLine(l)
    except TypeError:
        print("ERROR. Please add text file path after the script.")
    except FileNotFoundError:
        print("ERROR. File not found.")
    if not quiet:
        print("File successfully processed.")
        print()


def regexLine(line):
    global lastModuleProcessed
    global lastVoiceProcessed

    if debugMode:
        print()
    if debugMode:
        print("Processing: " + line)

    # CHECK FOR COMMENTS
    if debugMode:
        print("Checking input for comments...")
    re_filter = re.compile(r"^\/\/\s?(.+)$")  # Regex for "// Comments"
    re_results = re_filter.search(line.strip())
    try:
        comment = re_results.group(1).strip()
        if debugMode:
            print("New comment found: " + comment)
        addComment(comment)
        return
    except AttributeError:
        pass

    # CHECK FOR VOICES
    if debugMode:
        print("Cheking input for voices...")
    re_filter = re.compile(r"^(.+)\:$")  # Regex for "VOICE 1:"
    re_results = re_filter.search(line.strip())
    try:
        # For some reason the Regex filter was still detecting parameter declarations as voices,
        # so I'm also running the results through an if statement.
        results = re_results.group().replace(":", "")
        if "*" not in results and "-" not in results and "|" not in results:
            if debugMode:
                print("New voice found: " + results.upper())
            lastVoiceProcessed = results.upper()
            return
    except AttributeError:
        pass

    # CHECK FOR CONNECTIONS
    if debugMode:
        print("Cheking input for connections...")
    re_filter = re.compile(
        r"\-\s(.+)[(](.+)[)]\s(\>\>|\-\>|[a-z]\>)\s(.+)[(](.+)[)]\s(\[.+\])?$")
    re_results = re_filter.search(line)
    try:
        results = re_results.groups()
        voice = lastVoiceProcessed
        if len(results) == 6:
            if debugMode:
                print("New connection found, parsing info...")
            # args = parseArguments(results[5])
            # results = results[:5]
            addConnection(results, voice)
            return
    except AttributeError:
        pass

    # CHECK PARAMETERS
    if debugMode:
        print("Checking for parameters...")
    # If single-line parameter declaration:
    re_filter = re.compile(r"^\*\s(.+)\:\s?(.+)?$")
    re_results = re_filter.search(line.strip())
    try:
        # Get module name
        results = re_results.groups()
        module = results[0].strip().lower()
        if debugMode:
            print("New module found: " + module)
        if results[1] != None:
            # If parameters are also declared
            parameters = results[1].split(" | ")
            for p in parameters:
                p = p.split(" = ")
                addParameter(module, p[0].strip().lower(), p[1].strip())
            return
        elif results[1] == None:
            if debugMode:
                print("No parameters found. Storing module as global variable...")
            lastModuleProcessed = module
            return
    except AttributeError:
        pass

    # If multi-line parameter declaration:
    if "|" in line and "=" in line and "*" not in line:
        module = lastModuleProcessed.lower()
        if debugMode:
            print("Using global variable: " + module)
        parameter = line.split(" = ")[0].replace("|", "").strip().lower()
        value = line.split(" = ")[1].strip()
        addParameter(module, parameter, value)
        return


def parseArguments(args):
    # This method takes an arguments string like "[color = blue]" and converts it to a dictionary
    args_string = args.replace("[", "").replace("]", "")
    args_array = args_string.split(",")
    args_dict = {}

    if debugMode:
        print("Parsing arguments: " + args)

    for item in args_array:
        item = item.split("=")
        name = item[0].strip()
        value = item[1].strip()
        args_dict[name] = value
        if debugMode:
            print(name + " = " + value)

    if debugMode:
        print("All arguments processes.")

    return args_dict


def addConnection(list, voice="none"):
    global mainDict
    global connectionTypes
    global connectionID

    connectionID += 1

    if debugMode:
        print("Adding new connection...")
        print("-----")

    output_module = list[0].lower().strip()
    output_port = list[1].lower().strip()

    if debugMode:
        print("Output module: " + output_module)
        print("Output port: " + output_port)

    try:
        connection_type = connectionTypes[list[2].lower()]
        if debugMode:
            print("Matched connection type: " + connection_type)
    except KeyError:
        print("Invalid connection: " + list[2])
        connection_type = "cv"

    input_module = list[3].lower().strip()
    input_port = list[4].lower().strip()

    if list[5] is not None:
        arguments = parseArguments(list[5])
    else:
        arguments = {}

    if debugMode:
        print("Input module: " + input_module)
        print("Input port: " + output_port)

    checkModuleExistance(output_module, output_port, "out")
    checkModuleExistance(input_module, input_port, "in")

    if debugMode:
        print("Appending output and input connections to mainDict...")

    output_dict = {
        "input_module": input_module,
        "input_port": input_port,
        "connection_type": connection_type,
        "voice": voice,
        "id": connectionID}

    input_dict = {
        "output_module": output_module,
        "output_port": output_port,
        "connection_type": connection_type,
        "voice": voice,
        "id": connectionID}

    for key in arguments:
        output_dict[key] = arguments[key]
        input_dict[key] = arguments[key]

    mainDict["modules"][output_module]["connections"]["out"][output_port].append(
        output_dict)
    mainDict["modules"][input_module]["connections"]["in"][input_port] = input_dict
    if debugMode:
        print("-----")


def checkModuleExistance(module, port="port", direction=""):
    global mainDict

    if debugMode:
        print("Checking if module already existing in main dictionary: " + module)

    # Check if module exists in main dictionary
    if module not in mainDict["modules"]:
        mainDict["modules"][module] = {
            "parameters": {},
            "connections": {"out": {}, "in": {}}
        }

    # If it exists, check if the port exists
    if direction == "in":
        if port not in mainDict["modules"][module]["connections"]["in"]:
            mainDict["modules"][module]["connections"]["in"][port] = []

    if direction == "out":
        if port not in mainDict["modules"][module]["connections"]["out"]:
            mainDict["modules"][module]["connections"]["out"][port] = []


def addParameter(module, name, value):
    checkModuleExistance(module)
    # Add parameter to mainDict
    if debugMode:
        print("Adding parameter: " + module + " - " + name + " - " + value)
    mainDict["modules"][module]["parameters"][name] = value


def addComment(value):
    mainDict["comments"].append(value)


def askCommand(command=None):
    global one_shot_command
    if one_shot_command:
        command = one_shot_command
    if not command:
        command = input("> ").lower().strip()

    if command == "module":
        detailModule()
    elif command == "modules":
        detailModule(all=True)
    elif command == "print":
        printDict()
    elif command == "export":
        exportJSON()
    elif command == "connections":
        printConnections()
    elif command == "graph":
        graphviz()
    elif command == "d2":
        d2()
    else:
        print("Invalid command, please try again.")

    if one_shot_command:
        return
    askCommand()

def _print_module(module):
    global mainDict, quiet
    print("-------")
    print("Showing information for module: " + module.upper())
    print()
    print("Inputs:")
    for c in mainDict["modules"][module]["connections"]["in"]:
        keyvalue = mainDict["modules"][module]["connections"]["in"][c]
        print(keyvalue["output_module"].title() + " (" + keyvalue["output_port"].title(
        ) + ") > " + c.title() + " - " + keyvalue["connection_type"].title())
    print()

    print("Outputs:")
    for x in mainDict["modules"][module]["connections"]["out"]:
        port = mainDict["modules"][module]["connections"]["out"][x]
        for c in port:
            keyvalue = c
            print(x.title() + " > " + keyvalue["input_module"].title() + " (" + keyvalue["input_port"].title(
            ) + ") " + " - " + keyvalue["connection_type"].title() + " - " + keyvalue["voice"])
    print()

    print("Parameters:")
    for p in mainDict["modules"][module]["parameters"]:
        value = mainDict["modules"][module]["parameters"][p]
        print(p.title() + " = " + value)
    print()

    if not quiet: print("-------")

def detailModule(all=False):
    global mainDict
    if not all:
        module = input("Enter module name: ").lower()
        if module in mainDict["modules"]:
            _print_module(module)
    else:
        for module in mainDict["modules"]:
            _print_module(module)


def printConnections():
    print()
    print("Printing all connections by type...")
    print()

    for ctype in connectionTypes:
        ctype_name = connectionTypes[ctype]
        print("Connection type: " + ctype_name)
        # For each module
        for module in mainDict["modules"]:
            # Get all outgoing connections:
            connections = mainDict["modules"][module]["connections"]["out"]
            for c in connections:
                connection = connections[c]
                for subc in connection:
                    # print(connection)
                    if subc["connection_type"] == ctype_name:
                        print(module.title(
                        ) + " > " + subc["input_module"].title() + " (" + subc["input_port"].title() + ") ")
        print()


def exportJSON():
    # Exports mainDict as json file
    # name = filename.split(".")[0]
    # filepath = getFilePath(name + '.json')
    # print("Exporting dictionary as file: " + filepath)
    # with open(filepath, 'w') as fp:
    #     json.dump(mainDict, fp)
    print(json.dumps(mainDict))


def graphviz():
    global quiet, direction
    linetypes = {
        "audio": {"style": "bold"},
        "cv": {"color": "gray"},
        "gate": {"color": "red", "style": "dashed"},
        "trigger": {"color": "orange", "style": "dashed"},
        "pitch": {"color": "blue"},
        "clock": {"color": "purple", "style": "dashed"}
    }
    if direction == "DN":
        rank_dir_token = "rankdir = BT;\n"
        from_token = ":s  -> "
        to_token = ":n  "
    else:
        rank_dir_token = "rankdir = LR;\n"
        from_token = ":e  -> "
        to_token = ":w  "
    if not quiet:
        print("Generating signal flow code for GraphViz.")
        print("Copy the code between the line break and paste it into https://dreampuf.github.io/GraphvizOnline/ to download a SVG / PNG chart.")
    conn = []
    total_string = ""
    if not quiet: print("-------------------------")
    print("digraph G{\n" + rank_dir_token + "splines = polyline;\nordering=out;")
    total_string += "digraph G{\n" + rank_dir_token + "splines = polyline;\nordering=out;\n"
    for module in sorted(mainDict["modules"]):
        # Get all outgoing connections:
        outputs = mainDict["modules"][module]["connections"]["out"]
        module_outputs = ""
        out_count = 0
        for out in sorted(outputs):
            out_count += 1
            out_formatted = "_" + re.sub('[^A-Za-z0-9]+', '', out)
            module_outputs += "<" + out_formatted + "> " + out.upper()
            if out_count < len(outputs.keys()):
                module_outputs += " | "
            connections = outputs[out]
            for c in connections:
                line_style_array = []
                graphviz_parameters = [
                    "color", "weight", "style", "arrowtail", "dir"]
                for param in graphviz_parameters:
                    if param in c:
                        line_style_array.append(param + "=" + c[param])
                    elif param in linetypes[c["connection_type"]]:
                        line_style_array.append(
                            param + "=" + linetypes[c["connection_type"]][param])
                if len(line_style_array) > 0:
                    line_style = "[" + ', '.join(line_style_array) + "]"
                else:
                    line_style = ""
                in_formatted = "_" + \
                    re.sub('[^A-Za-z0-9]+', '', c["input_port"])
                connection_line = re.sub(graphVizRemoveChars, "", module) + ":" + out_formatted + from_token + \
                    re.sub(graphVizRemoveChars, "", c["input_module"]) + \
                    ":" + in_formatted + to_token + line_style
                conn.append([c["input_port"], connection_line])

        # Get all incoming connections:
        inputs = mainDict["modules"][module]["connections"]["in"]
        module_inputs = ""
        in_count = 0
        for inp in sorted(inputs):
            inp_formatted = "_" + re.sub('[^A-Za-z0-9]+', '', inp)
            in_count += 1
            module_inputs += "<" + inp_formatted + "> " + inp.upper()
            if in_count < len(inputs.keys()):
                module_inputs += " | "

        # Get all parameters:
        params = mainDict["modules"][module]["parameters"]
        module_params = ""
        param_count = 0
        for par in sorted(params):
            param_count += 1
            module_params += par.title() + " = " + params[par]
            if param_count < len(params.keys()):
                module_params += r'\n'

        # If module contains parameters
        if module_params != "":
            # Add them below module name
            middle = "{{" + module.upper() + "}|{" + module_params + "}}"
        else:
            # Otherwise just display module name
            middle = module.upper()

        final_box = re.sub(graphVizRemoveChars, "", module) + \
            "[label=\"{ {" + module_inputs + "}|" + middle + "| {" + module_outputs + "}}\"  shape=Mrecord]"
        print(final_box)
        total_string += final_box + "; "

    # Print Connections
    for c in sorted(conn):
        print(c[1])
        total_string += c[1] + "; "

    if len(mainDict["comments"]) != 0:
        format_comments = ""
        comments_count = 0
        for comment in mainDict["comments"]:
            comments_count += 1
            format_comments += "{" + comment + "}"
            if comments_count < len(mainDict["comments"]):
                format_comments += "|"
        format_comments = "comments[label=<{{{<b>PATCH COMMENTS</b>}|" + format_comments + "}}>  shape=Mrecord]"
        print(format_comments)

    print("}")
    total_string += "}"

    if not quiet:
        print("-------------------------")
        print()
    return total_string


def topological_sort(modules):
    """Sort modules so that sources come first and sinks come last.
    Falls back gracefully on cycles by breaking the least-recently-added edge."""
    # Build adjacency list from connections
    successors = {m: set() for m in modules}
    predecessors = {m: set() for m in modules}
    for module in modules:
        outputs = modules[module]["connections"]["out"]
        for port in outputs:
            for c in outputs[port]:
                target = c["input_module"]
                if target in modules:
                    successors[module].add(target)
                    predecessors[target].add(module)

    # Kahn's algorithm
    in_degree = {m: len(predecessors[m]) for m in modules}
    queue = [m for m in modules if in_degree[m] == 0]
    # Sort the initial queue by first appearance (lowest connection ID touching the module)
    def first_id(m):
        ids = []
        for port in modules[m]["connections"]["out"]:
            for c in modules[m]["connections"]["out"][port]:
                ids.append(c["id"])
        for port in modules[m]["connections"]["in"]:
            ids.append(modules[m]["connections"]["in"][port]["id"])
        return min(ids) if ids else 0
    queue.sort(key=first_id)
    result = []
    while queue:
        node = queue.pop(0)
        result.append(node)
        for succ in sorted(successors[node], key=first_id):
            in_degree[succ] -= 1
            if in_degree[succ] == 0:
                queue.append(succ)
    # If there are remaining nodes (cycles), append them sorted by first_id
    remaining = [m for m in modules if m not in result]
    remaining.sort(key=first_id)
    result.extend(remaining)
    return result


def d2():
    global quiet, direction
    # D2 uses named colors or hex codes; "thick" is replaced with stroke-width and a color
    linetypes = {
        "audio": {"color": "#c5c2b8", "width": 3},
        "cv": {"color": "#4CAF50"},
        "gate": {"color": "#E57373"},
        "trigger": {"color": "#FFB74D"},
        "pitch": {"color": "#64B5F6"},
        "clock": {"color": "#CE93D8"}
    }

    if not quiet:
        print("Generating signal flow code for D2.")
        print("Copy the code between the line breaks and paste it into https://play.d2lang.com/ to visualize.")

    total_string = ""

    if not quiet: print("-------------------------")

    # D2 direction: auto-select based on complexity
    # Complex patches (>=10 modules) flow top-to-bottom to avoid extreme width
    # Simple patches (<10 modules) flow left-to-right
    module_count = len(mainDict["modules"])
    if direction == "DN":
        direction_str = "down"
    elif direction == "LR":
        direction_str = "down" if module_count >= 10 else "right"
    else:
        direction_str = "right"
    print(f"direction: {direction_str}")
    total_string += f"direction: {direction_str}\n"

    # Transparent background so diagrams blend with the page
    print("style: {\n  fill: transparent\n}")
    total_string += "style: {\n  fill: transparent\n}\n"

    modules = mainDict["modules"]

    # Sort modules in signal-flow order (sources first, sinks last)
    sorted_modules = topological_sort(modules)

    # Build a D2-safe identifier for each module
    def node_id(module):
        return re.sub(r'[^A-Za-z0-9_]', "", module)

    # Build a module's label (uppercase name + parameters)
    def module_label(module):
        label = module.upper()
        params = modules[module]["parameters"]
        if params:
            param_str = "\\n" + "\\n".join([f"{par}: {params[par]}" for par in sorted(params)])
            label += param_str
        return label

    # Emit modules in topological order
    for module in sorted_modules:
        node_def = f'{node_id(module)}: "{module_label(module)}"'
        print(node_def)
        total_string += node_def + "\n"

    # Collect all connections with their original IDs for ordering
    conn = []
    for module in modules:
        outputs = modules[module]["connections"]["out"]
        for out in outputs:
            for c in outputs[out]:
                # Build connection style
                style_parts = []
                conn_type_style = linetypes.get(c["connection_type"], {"color": "black"})
                color = conn_type_style.get("color", "black")
                style_parts.append(f'style.stroke: "{color}"')
                if "width" in conn_type_style:
                    style_parts.append(f"style.stroke-width: {conn_type_style['width']}")
                if "style" in c:
                    style_parts.append(f"style.{c['style']}")

                from_node = node_id(module)
                to_node = node_id(c["input_module"])

                style_str = ""
                if style_parts:
                    style_str = "\n    " + "\n    ".join(style_parts)

                connection_line = f"{from_node} -> {to_node} {{\n    source-arrowhead.label: {out}\n    target-arrowhead.label: {c['input_port']}{style_str}\n  }}"
                conn.append((c["id"], connection_line))

    # Sort connections by their original ID (source file order)
    conn.sort(key=lambda x: x[0])
    for _, c in conn:
        print(c)
        total_string += c + "\n"

    # Add comments if any, as a single node. A line break inside a D2 label is
    # the two-character escape "\n", not a real newline -- same as module_label.
    if len(mainDict["comments"]) != 0:
        escaped = [c.replace("\\", "\\\\").replace('"', '\\"')
                   for c in mainDict["comments"]]
        comment_lines = "\\n".join(escaped)
        comments_block = f'comments: "PATCH COMMENTS\\n\\n{comment_lines}"'
        print(comments_block)
        total_string += comments_block + "\n"

    if not quiet:
        print("-------------------------")
        print()

    return total_string


def printDict():
    global mainDict
    for key in mainDict["modules"]:
        print(key.title() + ": " + str(mainDict["modules"][key]))


if __name__ == "__main__":
    initial_print()
    parseFile(filename)
    askCommand()
