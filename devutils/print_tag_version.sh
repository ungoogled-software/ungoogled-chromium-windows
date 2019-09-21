#!/bin/bash -eu

_root_dir=$(dirname $(dirname $(readlink -f $0)))
_ungoogled_repo=$_root_dir/ungoogled-chromium

printf '%s-%s.%s' $(cat $_ungoogled_repo/chromium_version.txt) $(cat $_ungoogled_repo/revision.txt) $(cat $_root_dir/revision.txt)
