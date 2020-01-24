# Copyright 2018 Juniper Networks, Inc. All rights reserved
#
# Licensed under the Juniper Networks Script Software License (the "License").
# You may not use this script file except in compliance with the License, which is located at
# http://www.juniper.net/support/legal/scriptlicense/
# Unless required by applicable law or otherwise agreed to in writing by the parties,
# software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
# OR CONDITIONS OF ANY KIND, either express or implied.
"""JetEZ Library

:Organization: Juniper Networks, Inc.
:Copyright: Copyright (c) 2018, Juniper Networks, Inc. All rights reserved.
:Date: 05/23/2018
:Version: 0.4
"""
from contextlib import contextmanager
from jet import crypto
from lxml import etree
from yaml.error import YAMLError
import argparse
import binascii
import datetime
import logging
import os
import subprocess
import shutil
import yaml
import sys

try:
    FileNotFoundError
except NameError:
    # python 2 compatibility
    FileNotFoundError = IOError

log = logging.getLogger("jet")


@contextmanager
def exit_on_error(*exceptions):
    """log exception and exit

    :param exceptions: exceptions
    :type exceptions: Exception
    """
    try:
        yield
    except YAMLError as error:
        log.error("failed to parse yaml file\n %s", error)
        sys.exit(1)
    except FileNotFoundError as error:
        log.error("no such file or directory: %s", error.filename)
        sys.exit(1)
    except Exception as error:
        log.error(str(error))
        sys.exit(1)


class FileArgumentParser(argparse.ArgumentParser):

    def __file_error(self, metavar, arg, args):
        self.error("argument %s: %s %s not found" % ("/".join(args), metavar, arg))

    def __is_valid_file(self, arg, args):
        if not os.path.isfile(arg):
            self.__file_error("file", arg, args)
        else:
            # File exists so return the filename
            return arg

    def __is_valid_directory(self, arg, args):
        if not os.path.isdir(arg):
            self.__file_error("directory", arg, args)
        else:
            # File exists so return the directory
            return arg

    def add_argument_with_check(self, *args, **kwargs):
        # Look for your FILE or DIR settings
        if 'metavar' in kwargs and 'type' not in kwargs:
            if kwargs['metavar'] is 'FILE':
                type=lambda x: self.__is_valid_file(x, args)
                kwargs['type'] = type
            elif kwargs['metavar'] is 'DIR':
                type=lambda x: self.__is_valid_directory(x, args)
                kwargs['type'] = type
        self.add_argument(*args, **kwargs)


def load_project(project_file, version):
    """load jet project from yaml file

    :param project_file: path to input file
    :type project_file: str
    :return: jet project
    :rtype: dict
    """
    with open(project_file , 'r') as f:
        project_yaml = yaml.load(f)

    def required(d, k):
        if k in d:
            return d[k]
        else:
            raise ValueError("missing attribute %s" % k)

    timestamp = datetime.datetime.now()
    project = {
        "basename": required(project_yaml, "basename"),
        "files": [],
        "comment": project_yaml.get("comment", "JET app %s" % project_yaml["basename"]),
        "arch": project_yaml.get("arch", "x86"),
        "abi": project_yaml.get("abi", "32"),
        "copyright": project_yaml.get("copyright", "Copyright %s, Juniper Networks, Inc." % timestamp.year),
        "package_id": project_yaml.get("package_id", 31),
        "role": project_yaml.get("role", "Provider_Daemon"),
        "date": timestamp.strftime("%Y%m%d"),
        "time": timestamp.strftime("%H%M%S"),
        "schema": project_yaml.get("schema", False),
        "config-validate": project_yaml.get("config-validate", False),
        "veriexec-ext": project_yaml.get("veriexec-ext", False),
    }
    project_yaml_files = required(project_yaml, "files")
    for file in project_yaml_files:
        project["files"].append({
            "source": required(file, "source"),
            "destination": required(file, "destination"),
            "uid": file.get("uid", 0),
            "gid": file.get("gid", 0),
            "mode": file.get("mode", 555),
            "program_id": file.get("program_id", 1),
            "symlink": file.get("symlink", True),
        })
    return project


def create_contents_iso(input, output):
    """create iso file

    :param input: path to input file
    :type input: str
    :param output: path to output file
    :type output: str
    """
    subprocess.check_output("mkisofs --rock -sysid JUNOS -o %s %s" % (output, input), shell=True)


def create_tgz(package, path):
    """create tgz archive

    :param package: package name
    :type package: str
    :param path: path to build directory
    :type path: str
    """
    files = " ".join(os.listdir(path))
    subprocess.check_output("tar -C %s -czf %s.tgz %s" % (path, package, files), shell=True)


def create_package_xml(project, version, package, path):
    """create package.xml file

    :param project: jet project
    :type project: dict
    :param version: version string
    :type version: str
    :param package: package name
    :type package: str
    :param path: path to build directory
    :type path: str
    """
    def package_xml_file(filename):
        filename = os.path.join(path, filename)
        _file = etree.SubElement(dir, "file", name=os.path.basename(filename))
        etree.SubElement(_file, "size").text = str(os.path.getsize(filename))
        etree.SubElement(_file, "sha256").text = str(crypto.generate_sha256(filename))

    package_xml = etree.Element("package", name=package)
    etree.SubElement(package_xml, "abi").text = project["abi"]
    etree.SubElement(package_xml, "arch").text = project["arch"]
    etree.SubElement(package_xml, "basename").text = project["basename"]
    etree.SubElement(package_xml, "comment").text = "%s [%s]" % (project["comment"], version)
    etree.SubElement(package_xml, "copyright").text = project["copyright"]
    etree.SubElement(package_xml, "description").text = project["basename"]
    etree.SubElement(package_xml, "mntname").text = "%s%s-%s" % (project["basename"], project["abi"], binascii.b2a_hex(os.urandom(4)).decode())
    etree.SubElement(package_xml, "require").text = "junos-runtime32"
    etree.SubElement(package_xml, "version").text = project["date"]
    etree.SubElement(package_xml, "spin").text = project["time"]
    etree.SubElement(package_xml, "sb-location").text = "JetEZ"

    # XMLPKG_TOGGLE_LIST
    for p in ("schema", "config-validate", "veriexec-ext"):
        if project[p]:
            etree.SubElement(package_xml, p)

    dir = etree.SubElement(package_xml, "dir", name="contents")
    package_xml_file("contents/contents.iso")
    package_xml_file("contents/contents.symlinks")
    with open("%s/package.xml" % path, "w+") as f:
        f.write(etree.tostring(package_xml, pretty_print=True).decode("utf8"))
