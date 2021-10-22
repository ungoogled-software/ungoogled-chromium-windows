#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2019 The ungoogled-chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""
ungoogled-chromium build script for Microsoft Windows
"""

import sys
if sys.version_info.major < 3 or sys.version_info.minor < 6:
    raise RuntimeError('Python 3.6+ is required for this script. You have: {}.{}'.format(
        sys.version_info.major, sys.version_info.minor))

import argparse
import os
import re
import shutil
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'ungoogled-chromium' / 'utils'))
import downloads
import domain_substitution
import prune_binaries
import patches
from _common import ENCODING, USE_REGISTRY, ExtractorEnum, get_logger
sys.path.pop(0)

_ROOT_DIR = Path(__file__).resolve().parent
_PATCH_BIN_RELPATH = Path('third_party/git/usr/bin/patch.exe')


def _get_vcvars_path(name='64'):
    """
    Returns the path to the corresponding vcvars*.bat path

    As of VS 2017, name can be one of: 32, 64, all, amd64_x86, x86_amd64
    """
    vswhere_exe = '%ProgramFiles(x86)%\\Microsoft Visual Studio\\Installer\\vswhere.exe'
    result = subprocess.run(
        '"{}" -prerelease -latest -property installationPath'.format(vswhere_exe),
        shell=True,
        check=True,
        stdout=subprocess.PIPE,
        universal_newlines=True)
    vcvars_path = Path(result.stdout.strip(), 'VC/Auxiliary/Build/vcvars{}.bat'.format(name))
    if not vcvars_path.exists():
        raise RuntimeError(
            'Could not find vcvars batch script in expected location: {}'.format(vcvars_path))
    return vcvars_path


def _run_build_process(*args, **kwargs):
    """
    Runs the subprocess with the correct environment variables for building
    """
    # Add call to set VC variables
    cmd_input = ['call "%s" >nul' % _get_vcvars_path()]
    cmd_input.append('set DEPOT_TOOLS_WIN_TOOLCHAIN=0')
    cmd_input.append(' '.join(map('"{}"'.format, args)))
    cmd_input.append('exit\n')
    subprocess.run(('cmd.exe', '/k'),
                   input='\n'.join(cmd_input),
                   check=True,
                   encoding=ENCODING,
                   **kwargs)


def _make_tmp_paths():
    """Creates TMP and TEMP variable dirs so ninja won't fail"""
    tmp_path = Path(os.environ['TMP'])
    if not tmp_path.exists():
        tmp_path.mkdir()
    tmp_path = Path(os.environ['TEMP'])
    if not tmp_path.exists():
        tmp_path.mkdir()


def main():
    """CLI Entrypoint"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--disable-ssl-verification',
        action='store_true',
        help='Disables SSL verification for downloading')
    parser.add_argument(
        '--7z-path',
        dest='sevenz_path',
        default=USE_REGISTRY,
        help=('Command or path to 7-Zip\'s "7z" binary. If "_use_registry" is '
              'specified, determine the path from the registry. Default: %(default)s'))
    parser.add_argument(
        '--winrar-path',
        dest='winrar_path',
        default=USE_REGISTRY,
        help=('Command or path to WinRAR\'s "winrar.exe" binary. If "_use_registry" is '
              'specified, determine the path from the registry. Default: %(default)s'))
    args = parser.parse_args()

    # Set common variables
    source_tree = _ROOT_DIR / 'build' / 'src'
    downloads_cache = _ROOT_DIR / 'build' / 'downloads_cache'
    domsubcache = _ROOT_DIR / 'build' / 'domsubcache.tar.gz'

    # Setup environment
    source_tree.mkdir(parents=True, exist_ok=True)
    downloads_cache.mkdir(parents=True, exist_ok=True)
    _make_tmp_paths()

    # Get download metadata (DownloadInfo)
    download_info = downloads.DownloadInfo([
        _ROOT_DIR / 'downloads.ini',
        _ROOT_DIR / 'ungoogled-chromium' / 'downloads.ini',
    ])

    # Retrieve downloads
    get_logger().info('Downloading required files...')
    downloads.retrieve_downloads(download_info, downloads_cache, True,
                                          args.disable_ssl_verification)
    try:
        downloads.check_downloads(download_info, downloads_cache)
    except downloads.HashMismatchError as exc:
        get_logger().error('File checksum does not match: %s', exc)
        exit(1)

    # Unpack downloads
    extractors = {
        ExtractorEnum.SEVENZIP: args.sevenz_path,
        ExtractorEnum.WINRAR: args.winrar_path,
    }
    get_logger().info('Unpacking downloads...')
    downloads.unpack_downloads(download_info, downloads_cache, source_tree, extractors)

    # Prune binaries
    unremovable_files = prune_binaries.prune_dir(
        source_tree,
        (_ROOT_DIR / 'ungoogled-chromium' / 'pruning.list').read_text(encoding=ENCODING).splitlines()
    )
    if unremovable_files:
        get_logger().error('Files could not be pruned: %s', unremovable_files)
        parser.exit(1)

    # Apply patches
    # First, ungoogled-chromium-patches
    patches.apply_patches(
        patches.generate_patches_from_series(_ROOT_DIR / 'ungoogled-chromium' / 'patches', resolve=True),
        source_tree,
        patch_bin_path=(source_tree / _PATCH_BIN_RELPATH)
    )
    # Then Windows-specific patches
    patches.apply_patches(
        patches.generate_patches_from_series(_ROOT_DIR / 'patches', resolve=True),
        source_tree,
        patch_bin_path=(source_tree / _PATCH_BIN_RELPATH)
    )

    # Substitute domains
    domain_substitution.apply_substitution(
        _ROOT_DIR / 'ungoogled-chromium' / 'domain_regex.list',
        _ROOT_DIR / 'ungoogled-chromium' / 'domain_substitution.list',
        source_tree,
        domsubcache
    )

    # Output args.gn
    (source_tree / 'out/Default').mkdir(parents=True)
    gn_flags = (_ROOT_DIR / 'ungoogled-chromium' / 'flags.gn').read_text(encoding=ENCODING)
    gn_flags += '\n'
    gn_flags += (_ROOT_DIR / 'flags.windows.gn').read_text(encoding=ENCODING)
    (source_tree / 'out/Default/args.gn').write_text(gn_flags, encoding=ENCODING)

    # Enter source tree to run build commands
    os.chdir(source_tree)

    # Run GN bootstrap
    _run_build_process(
        sys.executable, 'tools\\gn\\bootstrap\\bootstrap.py', '-o', 'out\\Default\\gn.exe',
        '--skip-generate-buildfiles')

    # Run gn gen
    _run_build_process('out\\Default\\gn.exe', 'gen', 'out\\Default', '--fail-on-unused-args')

    # Run ninja
    _run_build_process('third_party\\ninja\\ninja.exe', '-C', 'out\\Default', 'chrome',
                       'chromedriver', 'mini_installer')


if __name__ == '__main__':
    main()
