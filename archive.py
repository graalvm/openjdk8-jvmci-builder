#
# ----------------------------------------------------------------------------------------------------
#
# Copyright (c) 2016, Oracle and/or its affiliates. All rights reserved.
# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER.
#
# This code is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 only, as
# published by the Free Software Foundation.
#
# This code is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# version 2 for more details (a copy is included in the LICENSE file that
# accompanied this code).
#
# You should have received a copy of the GNU General Public License version
# 2 along with this work; if not, write to the Free Software Foundation,
# Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Please contact Oracle, 500 Oracle Parkway, Redwood Shores, CA 94065 USA
# or visit www.oracle.com if you need additional information or have any
# questions.
#
# ----------------------------------------------------------------------------------------------------

import zipfile, tarfile, os, hashlib, subprocess, stat
from os.path import join, exists, dirname, isdir, basename, getsize
from argparse import ArgumentParser

def abort(codeOrMessage):
    raise SystemExit(codeOrMessage)

def create_archive(srcdir, arcpath, prefix, verbose):
    """
    Creates a compressed archive of a given directory.

    :param str srcdir: directory to archive
    :param str arcpath: path of file to contain the archive. The extension of `path`
           specifies the type of archive to create
    :param str prefix: the prefix to apply to each entry in the archive
    :param bool verbose: if true, the name of each entry is printed as it's added to the archive
    """

    def _taradd(arc, filename, arcname):
        arc.add(name=f, arcname=arcname, recursive=False)
    def _zipadd(arc, filename, arcname):
        arc.write(filename, arcname)

    if arcpath.endswith('.zip'):
        arc = zipfile.ZipFile(arcpath, 'w', zipfile.ZIP_DEFLATED)
        add = _zipadd
    elif arcpath.endswith('.tar'):
        arc = tarfile.open(arcpath, 'w')
        add = _taradd
    elif arcpath.endswith('.tgz') or arcpath.endswith('.tar.gz'):
        arc = tarfile.open(arcpath, 'w:gz')
        add = _taradd
    else:
        abort('unsupported archive kind: ' + arcpath)

    for root, _, filenames in os.walk(srcdir):
        for name in filenames:
            f = join(root, name)
            # Make sure files in the image are readable by everyone
            mode = stat.S_IRGRP | stat.S_IROTH | os.stat(f).st_mode
            if isdir(f):
                mode = mode | stat.S_IXGRP | stat.S_IXOTH
            os.chmod(f, mode)
            arcname = prefix + os.path.relpath(f, srcdir)
            if verbose:
                print '{:11,} {}'.format(getsize(f), arcname)
            add(arc, f, arcname)

    arc.close()

def create_sha1(srcpath, dstpath):
    """
    Generates the SHA1 signature of `srcpath` and writes it to `dstpath`.
    """
    with open(srcpath, 'rb') as fp:
        d = hashlib.sha1()
        while True:
            buf = fp.read(4096)
            if not buf:
                break
            d.update(buf)
    with open(dstpath, 'w') as fp:
        fp.write(d.hexdigest())

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true', help='print entry names as they are added to the archive')
    parser.add_argument('prefix', help='root directory in archive')
    parser.add_argument('archive', metavar='<path>', action='store', help='archive to create')
    parser.add_argument('image', metavar='<dir>', action='store', help='directory containing built JDK 9 image')

    opts = parser.parse_args()
    arcpath = opts.archive
    prefix = opts.prefix + '/'
    create_archive(opts.image, arcpath, prefix, opts.verbose)
    sha1path = arcpath + '.sha1'
    create_sha1(arcpath, sha1path)
    os.chmod(arcpath, 0664)
    os.chmod(sha1path, 0664)
    print arcpath
    print sha1path
