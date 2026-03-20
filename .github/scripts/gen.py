import datetime
import hashlib
import os

import requests

tag = os.environ['GITHUB_REF_NAME']
config = [
    ('32bit', 'x86'),
    ('64bit', 'x64'),
    ('arm64', 'arm64'),
]
endings = [
    ('installer', 'exe'),
    ('windows', 'zip'),
]
hashes = (('md5', hashlib.md5), ('sha1', hashlib.sha1), ('sha256', hashlib.sha256))
for c_path, c_name in config:
    lines = []
    lines.append('[_metadata]')
    lines.append(f'publication_time = {datetime.datetime.now().isoformat()}')
    lines.append('github_author = github-actions')
    lines.append('# Add a `note` field here for additional information. Markdown is supported')

    for ending in endings:
        lines.append('')
        filename_tag = tag[:-1] + '1'
        name = f'ungoogled-chromium_{filename_tag}_{ending[0]}_{c_name}.{ending[1]}'
        lines.append(f'[{name}]')
        lines.append(f'url = https://github.com/ungoogled-software/ungoogled-chromium-windows/releases/download/{tag}/{name}')

        with requests.get(f'https://github.com/ungoogled-software/ungoogled-chromium-windows/releases/download/{tag}/{name}', stream=True) as r:
            r.raise_for_status()
            hash_instances = [(h_name, h()) for h_name, h in hashes]
            for chunk in r.iter_content(65536):
                for _, h in hash_instances:
                    h.update(chunk)
        for h_name, h in hash_instances:
            h = h.hexdigest()
            lines.append(f'{h_name} = {h}')
    with open(f'config/platforms/windows/{c_path}/{tag[:-2]}.ini', 'w') as f:
        f.write('\n'.join(lines))
