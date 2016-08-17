#!/usr/bin/python
__author__ = "Richard Attermeyer"
__copyright__ = "Copyright 2016, Richard Attermeyer"
__credits__ = ["Stephen Ostermiller"]
__email__ = "richard.attermeyer@gmail.com"
__status__ = "Prototype"

import argparse
import subprocess
import re

epilog = ''' This is a short utility to export and import key binding on unity / gnome, tested on 16.04
It is based on a perl script by Stephan Ostermiller, presented on http://askubuntu.com/a/217310.
I have ported it to python, as an exercise and to use it in an ansible setup scenario and I do not want to require
perl.
'''


def write_path(path, name_pattern, customBindings, keybindings):
    cmdpipe = subprocess.Popen(['gsettings', 'list-recursively', path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pattern = re.compile(r"^(?P<path>[^ ]+) (?P<name>[^ ]+)(?: \@[a-z]+)? (?P<value>.*)")
    for row in cmdpipe.stdout.readlines():
        match = re.search(pattern, row.decode("utf-8"))
        if match:
            value = match.group("value")
            if match.group("name") == "custom-keybindings":
                value = re.sub(r'[\[\]\']', '', value)
                customBindings.extend(value.split(','))
            elif name_pattern.search(match.group("name")):
                if re.search(r"^\[|\'", value):
                    if re.search(r"^\[(?:'disabled')\]", value):
                        value = '[]'
                    keybindings.write(match.group("path") + "\t" + match.group("name") + "\t" + value + "\n")
        else:
            print("Could not parse line: " + row)
            raise Exception("could not parse line: " + row)


def export_custom_bindings(customBindings, keybindings):
    for folder in customBindings:
        gsout = subprocess.check_output(['gsettings', 'list-recursively',
                                         "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:" + folder.strip()],
                                        stderr=subprocess.STDOUT).decode("utf-8")
        binding = re.search(r"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding binding (\'[^\n]+\')",
                            gsout).group(1)
        command = re.search(r"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding command (\'[^\n]+\')",
                            gsout).group(1)
        name = re.search(r"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding name (\'[^\n]+\')",
                         gsout).group(1)
        # handling of commands with quotes
        # replace double quotes with quoted
        command = command.replace('"', '\\\"')
        command = re.sub(r"^'(?P<command>.*)'$", "\g<command>", command)
        command = re.sub(r"\'", "\'\\\'\'", command)
        command = "'" + command + "'"
        keybindings.write("custom\t" + name + "\t" + command + "\t" + binding + "\n")


def exportKeybindings(path):
    keybindings = open(path, "w")
    # list to collect discovered custom bindings
    customBindings = []
    write_path('org.gnome.desktop.wm.keybindings', re.compile('.'), customBindings, keybindings)
    write_path('org.gnome.settings-daemon.plugins.power', re.compile('button'), customBindings, keybindings)
    write_path('org.gnome.settings-daemon.plugins.media-keys', re.compile('.'), customBindings, keybindings)
    # now handle custom bindings
    export_custom_bindings(customBindings, keybindings)
    keybindings.close()

def importKeybindings(path):
    keybindings = open(path, "r")
    customcount = 0
    for line in keybindings:
        v = line.rstrip().split("\t")
        if v[0] == "custom":
            print("custom")
            custom,name,command,binding = v
            print("gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom{}/ command \"{}\"".format(customcount, command))
            print("gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom{}/ binding \"{}\"".format(customcount, binding))
            print("gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom{}/ name \"{}\"".format(customcount, name))
            customcount+=1
        else:
            path,name,value = v
            print("gsettings set \"{}\" \"{}\" \"{}\"".format(path,name,value))
    keybindings.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exportiert und Importiert gnome key bindings",
                                     epilog=epilog,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-e", "--export", help="export key bindings")
    parser.add_argument("-i", "--import", dest="imp", help="import key bindings")
    args = parser.parse_args()
    if args.export:
        exportKeybindings(path=args.export)
    elif args.imp:
        importKeybindings(path=args.imp)
    else:
        parser.error("you must specify import or export")

