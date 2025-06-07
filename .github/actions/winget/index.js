const yaml = require('js-yaml');
const exec = require('@actions/exec');
const core = require('@actions/core');
const path = require('path');
const fs = require('fs/promises');
const fsSync = require('fs');
const { https } = require('follow-redirects');

function getInstallers(assets) {
    const installers = []
    for (const asset of assets) {
        const installerUrl = asset.browser_download_url;
        const installerSha256 = asset.digest.slice(7).toLocaleUpperCase();

        const isExe = asset.name.endsWith('.exe');
        const isZip = !isExe && asset.name.endsWith('.zip');
        if (!isExe && !isZip) {
            continue;
        }

        let architecture;
        if (asset.name.includes('x86')) {
            architecture = 'x86';
        } else if (asset.name.includes('x64')) {
            architecture = 'x64';
        } else if (asset.name.includes('arm64')) {
            architecture = 'arm64';
        } else {
            continue;
        }

        if (isExe) {
            installers.push({
                'Architecture': architecture,
                'InstallerType': 'exe',
                'Scope': 'machine',
                'InstallerUrl': installerUrl,
                'InstallerSha256': installerSha256,
                'InstallerSwitches': {
                    'Silent': '/silent /install',
                    'SilentWithProgress': '/silent /install',
                    'Custom': '--system-level'
                }
            }, {
                'Architecture': architecture,
                'InstallerType': 'exe',
                'Scope': 'user',
                'InstallerUrl': installerUrl,
                'InstallerSha256': installerSha256,
                'InstallerSwitches': {
                    'Silent': '/silent /install',
                    'SilentWithProgress': '/silent /install'
                }
            });
        } else {
            const folderName = asset.name.slice(0, -4);
            installers.push({
                'Architecture': architecture,
                'InstallerType': 'zip',
                'NestedInstallerType': 'portable',
                'NestedInstallerFiles': [
                    {
                        'RelativeFilePath': `${folderName}\\chrome.exe`,
                        'PortableCommandAlias': 'chrome'
                    }
                ],
                'InstallerUrl': installerUrl,
                'InstallerSha256': installerSha256,
                'ArchiveBinariesDependOnPath': true
            });
        }
    }
    return installers;
}

async function run() {
    const token = core.getInput('token', {
        required: true,
        trimWhitespace: true
    });
    let version = core.getInput('version', {
        required: true,
        trimWhitespace: true
    });
    const idx = version.lastIndexOf('-');
    if (idx !== -1)
        version = version.substr(0, idx);

    const assets = JSON.parse(core.getInput('assets', {
        required: true,
    }));
    const installers = getInstallers(assets);

    const manifestPath = path.resolve('./manifest');
    await fs.mkdir(manifestPath);

    const releaseDate = new Date().toLocaleDateString('en-CA');
    const installerManifest = yaml.dump({
        'PackageIdentifier': 'eloston.ungoogled-chromium',
        'PackageVersion': version,
        'InstallerLocale': 'en-US',
        'MinimumOSVersion': '10.0.0.0',
        'UpgradeBehavior': 'install',
        'Protocols': ['http', 'https'],
        'FileExtensions': ['crx', 'htm', 'html', 'pdf', 'url'],
        'Installers': installers,
        'ManifestType': 'installer',
        'ManifestVersion': '1.9.0',
        'ReleaseDate': releaseDate
    }, { noRefs: true });
    await fs.writeFile(path.join(manifestPath, 'eloston.ungoogled-chromium.installer.yaml'), installerManifest, { encoding: 'utf-8' });
    const defaultLocaleManifest = yaml.dump({
        'PackageIdentifier': 'eloston.ungoogled-chromium',
        'PackageVersion': version,
        'PackageLocale': 'en-US',
        'Publisher': 'The Chromium Authors',
        'PublisherUrl': 'https://github.com/ungoogled-software/ungoogled-chromium-windows',
        'PublisherSupportUrl': 'https://github.com/ungoogled-software/ungoogled-chromium-windows/issues',
        'Author': 'Eloston',
        'PackageName': 'Chromium',
        'PackageUrl': 'https://github.com/ungoogled-software/ungoogled-chromium-windows/releases',
        'License': 'BSD 3-Clause License',
        'LicenseUrl': 'https://github.com/ungoogled-software/ungoogled-chromium-windows/blob/master/LICENSE',
        'Copyright': 'Copyright 2022 The ungoogled-chromium Authors',
        'CopyrightUrl': 'https://github.com/ungoogled-software/ungoogled-chromium-windows/blob/master/LICENSE',
        'ShortDescription': 'ungoogled-chromium is Google Chromium without dependency on Google web services.',
        'Description': "ungoogled-chromium is a set of configuration flags, patches, and custom scripts.\n\nThese components altogether strive to accomplish the following\n* Disable or remove offending services and features that communicate with Google or weaken privacy\n* Strip binaries from the source tree, and use those provided by the system or build them from source\n* Add, modify, or disable features that inhibit control and transparency (these changes are minor and do not have significant impacts on the general user experience)\n\nungoogled-chromium should not be considered a fork of Chromium.\nThe main reason for this is that a fork is associated with more significant deviations from the Chromium, such as branding, configuration formats, file locations, and other interface changes.\nungoogled-chromium will not modify the Chromium browser outside of the project's goals.\nSince these goals and requirements are not precise, unclear situations are discussed and decided on a case-by-case basis.",
        'Moniker': 'ungoogled-chromium',
        'Tags': ['browser', 'chromium', 'ungoogled'],
        'ManifestType': 'defaultLocale',
        'ManifestVersion': '1.9.0'
    }, { noRefs: true });
    await fs.writeFile(path.join(manifestPath, 'eloston.ungoogled-chromium.locale.en-US.yaml'), defaultLocaleManifest, { encoding: 'utf-8' });
    const versionManifest = yaml.dump({
        'PackageIdentifier': 'eloston.ungoogled-chromium',
        'PackageVersion': version,
        'DefaultLocale': 'en-US',
        'ManifestType': 'version',
        'ManifestVersion': '1.9.0'
    }, { noRefs: true });
    await fs.writeFile(path.join(manifestPath, 'eloston.ungoogled-chromium.yaml'), versionManifest, { encoding: 'utf-8' });

    await new Promise((resolve, reject) => {
        const file = fsSync.createWriteStream('wingetcreate.exe');
        https.get('https://aka.ms/wingetcreate/latest', resp => {
            resp.pipe(file);
            file.on('finish', () => {
                file.close();
                resolve();
            });
        }).on('error', reject);
    });
    await exec.exec('.\\wingetcreate.exe', ['submit', '-t', token, manifestPath]);
}

run().catch(err => core.setFailed(err.message));