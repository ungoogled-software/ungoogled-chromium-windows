#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2018 The ungoogled-chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""
ungoogled-chromium packaging script for Microsoft Windows
"""

import sys
import argparse
import shutil
from pathlib import Path

import filescfg
from _common import ENCODING, get_chromium_version


BUILD_DIR = Path('build')
SRC_DIR = BUILD_DIR / 'src'
OUT_DIR = SRC_DIR / 'out' / 'Default'

# Filenames
MINI_INSTALLER = 'mini_installer.exe'
MINI_INSTALLER_RC = 'mini_installer_exe_version.rc'
SETUP_EXE = 'setup.exe'
CHROME_PACKED = 'chrome.packed.7z'


def check_python_version():
    """Ensure that Python 3 is being used."""
    if sys.version_info.major < 3:
        raise RuntimeError('Python 3 is required for this script.')


def get_release_revision():
    """Get the ungoogled-chromium release revision."""
    revision_path = Path(__file__).resolve().parent / 'ungoogled-chromium' / 'revision.txt'
    return revision_path.read_text(encoding=ENCODING).strip()


def get_packaging_revision():
    """Get the packaging revision."""
    revision_path = Path(__file__).resolve().parent / 'revision.txt'
    return revision_path.read_text(encoding=ENCODING).strip()


def create_installer():
    """Create the ungoogled-chromium installer."""
    installer_path = BUILD_DIR / 'ungoogled-chromium_{}-{}.{}_installer.exe'.format(
        get_chromium_version(), get_release_revision(), get_packaging_revision())
    shutil.copyfile(str(OUT_DIR / MINI_INSTALLER), str(installer_path))
    os.remove(str(OUT_DIR / MINI_INSTALLER))
    os.remove(str(OUT_DIR / MINI_INSTALLER_RC))
    os.remove(str(OUT_DIR / SETUP_EXE))
    try:
        os.remove(str(OUT_DIR / CHROME_PACKED))
    except FileNotFoundError:
        pass
    return installer_path


def create_archive(installer_path, cpu_arch):
    """Create the ungoogled-chromium archive."""
    output_path = BUILD_DIR / 'ungoogled-chromium_{}-{}.{}_windows.zip'.format(
        get_chromium_version(), get_release_revision(), get_packaging_revision())
    files_generator = filescfg.filescfg_generator(
        SRC_DIR / 'chrome/tools/build/win/FILES.cfg', OUT_DIR, cpu_arch)
    filescfg.create_archive(files_generator, tuple(), OUT_DIR, output_path)
    return output_path


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--cpu-arch',
        metavar='ARCH',
        default=platform.architecture()[0],
        choices=('64bit', '32bit'),
        help=('Filter build outputs by a target CPU. '
              'This is the same as the "arch" key in FILES.cfg. '
              'Default (from platform.architecture()): %(default)s'))
    return parser.parse_args()


def main():
    """Entrypoint"""
    check_python_version()

    args = parse_args()

    installer_path = create_installer()

    archive_path = create_archive(installer_path, args.cpu_arch)

    print(f"Successfully created archive: {archive_path}")


if __name__ == '__main__':
    main()
