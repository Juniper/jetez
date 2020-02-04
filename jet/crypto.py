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
"""JetEZ Library

:Organization: Juniper Networks, Inc.
:Copyright: Copyright (c) 2018, Juniper Networks, Inc. All rights reserved.
:Date: 04/12/2018
:Version: 0.4
"""
import base64
import logging
import hashlib
import os
import subprocess

FILE_BUF_SIZE=65536

log = logging.getLogger("jet")


def generate_sha256(filename):
    """generate sha256 hash of file

    :param filename: filename
    :type filename: str
    :return: sha256 hash of file
    :rtype: str
    """
    hash = hashlib.sha256()
    with open(filename, 'rb') as f:
        while True:
            data = f.read(FILE_BUF_SIZE)
            if not data:
                break
            hash.update(data)
    return hash.hexdigest()


def generate_sha1(filename):
    """generate sha1 hash of file

    :param filename: filename
    :type filename: str
    :return: sha1 hash of file
    :rtype: str
    """
    hash = hashlib.sha1()
    with open(filename, 'rb') as f:
        while True:
            data = f.read(FILE_BUF_SIZE)
            if not data:
                break
            hash.update(data)
    return hash.hexdigest()


def sign(input, output, key, cert):
    """sign file

    :param input: path to input file
    :type input: str
    :param output: path to output file
    :type output: str
    :param key: path to private key
    :type key: str
    :param cert: path to public key/cert
    :type cert: str
    """
    # get subject from certificate
    _subject = subprocess.check_output("openssl x509 -in %s -noout -subject" % cert, shell=True)
    subject = _subject.decode("utf8").split(" ", 1)[1].strip()
    # create signature
    signature = subprocess.check_output("openssl dgst -sha1 -sign %s %s" % (key, input), shell=True)
    # create base64 from signature
    signature64 = base64.b64encode(signature).decode("utf8")
    # format signature file
    signature_file="""%s
-----BEGIN JUNOS SIGNATURE-----
%s
-----END JUNOS SIGNATURE-----
""" % (subject, "\n".join([signature64[x:x+64] for x in range(0, len(signature64), 64)]))
    # write signature file
    with open(output, "w+") as f:
        f.write(signature_file)
    # create certificate chain
    with open("%s/manifest.certs" % os.path.dirname(__file__), "r") as f:
        cert_chain = f.read()
    with open(cert, "r") as f:
        cert_file = f.read()
    with open("%s/manifest.certs" % os.path.dirname(output), "w+") as f:
        f.write(cert_file)
        f.write(cert_chain)
