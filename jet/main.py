#!/usr/bin/env python
# Copyright 2018 Juniper Networks, Inc.  All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""JetEZ

:Organization: Juniper Networks, Inc.
:Copyright: Copyright (c) 2018, Juniper Networks, Inc. All rights reserved.
:Date: 04/19/2018
:Version: 0.4
"""
from jet import crypto
from jet import utils
import argparse
import datetime
import logging
import shutil
import sys
import os
import yaml

DESCIPTION = """
JetEZ - Easy SDK
----------------

This tool creates a JET install package (.tgz) from source directory using
the parameters from jet.yaml project description file.

"""

# setup logging to stdout
log = logging.getLogger("jet")
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
log.addHandler(ch)

def main():
    parser = utils.FileArgumentParser(description=DESCIPTION, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument_with_check('--source', dest='source', metavar='DIR', required=True, help="source directory")
    parser.add_argument('-v', '--version', dest='version', type=str, help="version string")
    parser.add_argument_with_check('-k', '--key', dest='key', metavar='FILE', required=True, help="path to signing key")
    parser.add_argument_with_check('-c', '--cert', dest='cert', metavar='FILE', required=True, help="path to signing cert")
    parser.add_argument_with_check('-j', '--jet', dest='jet', metavar='FILE', required=False, help="path to project file (default: <source>/jet.yaml)")
    parser.add_argument('-b', '--build', dest='build', default=".build", help="build directory (default: .build)")
    parser.add_argument('-d', '--debug', dest='debug', action='store_true', help="verbose logging")
    args = parser.parse_args()
    if args.debug:
        ch.setLevel(logging.DEBUG)

    version = args.version if args.version else datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    project_file = args.jet if args.jet else os.path.join(args.source, "jet.yaml")
    log.info("load project file %s", project_file)
    with utils.exit_on_error(Exception):
        project = utils.load_project(project_file, version)
    package = "%s-%s-%s-%s" % (project["basename"], project["arch"], project["abi"], version)

    log.info("create temporary build directory %s", args.build)
    if os.path.exists(args.build):
        shutil.rmtree(args.build)
    os.makedirs(args.build)
    os.makedirs('%s/contents' % args.build)
    os.makedirs('%s/scripts' % args.build)
    contents = "%s/contents/contents" % args.build
    scripts = "%s/scripts/activate" % args.build
    os.makedirs(contents)
    contents_pkg = '%s/pkg' % contents
    os.makedirs(contents_pkg)
    content_manifest = """pkg/manifest uid=0 gid=0 mode=444
pkg/manifest.sha1 uid=0 gid=0 mode=444
pkg/manifest.sig uid=0 gid=0 mode=444
pkg/manifest.certs uid=0 gid=0 mode=444
/set package_id=%s role=%s
""" % (project["package_id"], project["role"])
    contents_symlink =""
    mount_dir = "/packages/mnt/%s" % project["basename"]
    for f in project["files"]:
        destination = os.path.join(contents, *f['destination'].split("/"))
        log.info("copy file %s to %s", f['source'], destination)
        # create target directory
        _d = f['destination'].split("/")[1:]
        for d in  _d[:1] if len(_d) == 2 else ["/".join(_d[:x]) for x in range(2, len(_d))]:
            _d = os.path.join(contents, d)
            if not os.path.exists(_d):
                os.makedirs(_d)
        # copy file
        shutil.copy(os.path.join(args.source, f['source']), destination)
        # add file to manifest
        sha1 = crypto.generate_sha1(destination)
        content_manifest += "%s sha1=%s uid=%s gid=%s mode=%s program_id=%s\n" % \
            (f["destination"][1:] if f["destination"][0] == "/" else f["destination"],
             sha1, f["uid"], f["gid"], f["mode"], f["program_id"])
        if f["symlink"]:
            contents_symlink += "%s%s %s\n" % (mount_dir, f["destination"], f["destination"])

    content_manifest_file = '%s/manifest' % contents_pkg
    log.info("create manifest file %s", content_manifest_file)
    with open(content_manifest_file, "w") as f:
        f.write(content_manifest)

    content_manifest_sha_file = '%s/manifest.sha1' % contents_pkg
    with open(content_manifest_sha_file, "w") as f:
        f.write("%s\n" % crypto.generate_sha1(content_manifest_file))

    contents_symlink_file = '%s.symlinks' % contents
    log.info("create symlink file %s", contents_symlink_file)
    with open(contents_symlink_file, "w") as f:
        f.write(contents_symlink)

    given_scripts_file = os.path.join(args.source, "scripts/activate.sh")
    init_content = ""
    with open(given_scripts_file, 'r') as file:
        init_content = file.read()

    scripts_file = '%s.sh' % scripts
    log.info("create symlink file %s", scripts_file)
    with open(scripts_file, "w") as f:
        f.write(init_content)
    os.chmod(scripts_file, 0o755)

    log.info("sign manifest file %s" % content_manifest_file)
    crypto.sign(content_manifest_file, "%s.sig" % content_manifest_file, args.key, args.cert)

    for f in os.listdir(contents_pkg):
        os.chmod(os.path.join(contents_pkg, f), 0o444)

    log.info("create contents.iso")
    utils.create_contents_iso(contents, "%s.iso" % contents)
    shutil.rmtree(contents)

    log.info("create package.xml")
    utils.create_package_xml(project, version, package, args.build)

    package_manifest = "/set package_id=31 role=Provider_Daemon\n"
    package_manifest_files = ["contents/contents.iso", "contents/contents.symlinks", "scripts/activate.sh", "package.xml"]

    for f in package_manifest_files:
        if "scripts" not in f:
            package_manifest += "%s sha1=%s\n" % (f, crypto.generate_sha1(os.path.join(args.build, f)))
        else:
            package_manifest += "%s sha1=%s program_id=1\n" % (f, crypto.generate_sha1(os.path.join(args.build, f)))

    package_manifest_file = os.path.join(args.build, "manifest")
    log.info("create manifest file %s", package_manifest_file)
    with open(package_manifest_file, "w") as f:
        f.write(package_manifest)

    log.info("sign manifest file %s" % package_manifest_file)
    crypto.sign(package_manifest_file, "%s.sig" % package_manifest_file, args.key, args.cert)

    log.info("create %s.tgz" % package)
    utils.create_tgz(package, args.build)

    log.info("package successfully created")

if __name__ == "__main__":
    main()
