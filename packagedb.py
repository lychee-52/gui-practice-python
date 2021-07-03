#! /usr/bin/env python3

import argparse
import re
import apt_pkg
import pywebio

def load_packages(infile, packages):
    def register(package):
        if package and 'Package' in package:
            name = package['Package']
            if not 'Source' in package:
                package['Source'] = name
            if name in packages:
                if apt_pkg.version_compare(package['Version'], packages[name]['Version']) > 0:
                    packages[name] = package
            else:
                packages[name] = package

    with open(infile) as fin:
        package = {}
        key = ""
        for line in fin:
            m = re.match(r'^(\S+):\s*(\S.*\S|\S)\s*$', line)
            if m:
                key = m.group(1)
                package[key] = m.group(2)
            elif key:
                m = re.match(r'^\s+(\S.*\S|\S)\s*$', line)
                if m:
                    package[key] += "\n" + m.group(1)
                elif re.match(r'^\s*$', line):
                    register(package)
                    package = {}
        register(package)

def packages_search(packages, cmd, regex, ptn):
    if regex:
        pattern = re.compile("^.*" + ptn + ".*$")
    else:
        pattern = re.compile("^" + ptn + "$")

    result = []
    for name in packages:
        package = packages[name]
        if cmd in package and pattern.match(package[cmd]):
            result.append(name)

    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = "Debian apt repository Packages parser")
    parser.add_argument("file", help = "Packages file")
    args = parser.parse_args()

    packages = {}
    load_packages(args.file, packages)

    while True:
        webinputs = pywebio.input.input_group("Package query (regex)", [
            pywebio.input.input("Function", name = "function"),
            pywebio.input.input("Pattern", name = "pattern")
        ])
        if webinputs['function'] == "end":
            break
        cmd = webinputs['function']
        regex = False
        if cmd.startswith('*'):
            regex = True
            cmd = cmd[1:]
        result = packages_search(packages, cmd, regex, webinputs['pattern'])

        pywebio.output.clear()
        if result:
            mdstr = "# Result {} matches\n".format(len(result))
            sections = {}
            for r in result:
                s = packages[r]['Section']
                if s in sections:
                    sections[s].append(r)
                else:
                    sections[s] = [ r ]
            for s in sections:
                mdstr += "\n## {} {} matches\n\n".format(s, len(sections[s]))
                for r in sections[s]:
                    mdstr += " - {} : {} = {}\n".format(r, cmd, packages[r][cmd])
        else:
            mdstr = "# No matches\n"
        pywebio.output.put_markdown(mdstr)

    pywebio.output.clear()