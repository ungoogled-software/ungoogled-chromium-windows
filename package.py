#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2018 The ungoogled-chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""
ungoogled-chromium packaging script for Microsoft Windows
"""

import sys
if sys.version_info.major < 3:
    raise RuntimeError('Python 3 is required for this script.')

import argparse
import os
import platform
from pathlib import Path
import shutil

sys.path.insert(0, str(Path(__file__).resolve().parent / 'ungoogled-chromium' / 'utils'))
import filescfg
from _common import ENCODING, get_chromium_version
sys.path.pop(0)

def _get_release_revision():
    revision_path = Path(__file__).resolve().parent / 'ungoogled-chromium' / 'revision.txt'
    return revision_path.read_text(encoding=ENCODING).strip()

def _get_packaging_revision():
    revision_path = Path(__file__).resolve().parent / 'revision.txt'
    return revision_path.read_text(encoding=ENCODING).strip()

def main():
    """Entrypoint"""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--cpu-arch',
        metavar='ARCH',
        default=platform.architecture()[0],
        choices=('64bit', '32bit'),
        help=('Filter build outputs by a target CPU. '
              'This is the same as the "arch" key in FILES.cfg. '
              'Default (from platform.architecture()): %(default)s'))
    args = parser.parse_args()

    shutil.copyfile('build/src/out/Default/mini_installer.exe',
        'build/ungoogled-chromium_{}-{}.{}_installer.exe'.format(
            get_chromium_version(), _get_release_revision(), _get_packaging_revision()))

    # We need to remove these files, or they'll end up in the zip files that will be generated.
    os.remove('build/src/out/Default/mini_installer.exe')
    os.remove('build/src/out/Default/mini_installer_exe_version.rc')
    os.remove('build/src/out/Default/setup.exe')
    try:
        os.remove('build/src/out/Default/chrome.packed.7z')
    except FileNotFoundError:
        pass

    build_outputs = Path('build/src/out/Default')
    output = Path('build/ungoogled-chromium_{}-{}.{}_windows.zip'.format(
        get_chromium_version(), _get_release_revision(), _get_packaging_revision()))

    files_generator = filescfg.filescfg_generator(
        Path('build/src/chrome/tools/build/win/FILES.cfg'), build_outputs, args.cpu_arch)
    filescfg.create_archive(files_generator, tuple(), build_outputs, output)

if __name__ == '__main__':
    main()
