const yaml = require('js-yaml');
const exec = require('@actions/exec');
const core = require("@actions/core");
const glob = require('@actions/glob');
const path = require('path');
const compareVersions = require('compare-versions').compareVersions;
const fs = require('fs/promises');
const fsSync = require('fs');
const io = require('@actions/io');
const crypto = require('crypto');
const { https } = require('follow-redirects');

async function run() {
    const token = core.getInput('token', {
        required: true,
        trimWhitespace: true
    });
    let newVersion = core.getInput('version', {
        required: true,
        trimWhitespace: true
    });
    const idx = newVersion.lastIndexOf('-');
    if (idx !== -1)
        newVersion = newVersion.substring(0, idx);
    const assets = JSON.parse(core.getInput('assets', {
        required: true,
    }));
    const typeToUrl = new Map();
    for (const data of assets) {
        const type = data.name.split('_').pop();
        typeToUrl.set(type, {
            url: data.browser_download_url,
            digest: data.digest,
        });
    }

    await syncRepo(token);
    const globber = await glob.create('.\\winget-pkgs\\manifests\\e\\eloston\\ungoogled-chromium\\*', {matchDirectories: true, implicitDescendants: false});
    const pathList = await globber.glob();
    const ucPath = path.dirname(pathList[0]);
    const versionList = pathList.map(x => path.basename(x));
    versionList.sort(compareVersions);
    const latestVersion = versionList[versionList.length - 1];
    const latestVersionPath = path.join(ucPath, latestVersion);
    const newVersionPath = path.join(ucPath, newVersion);
    try {
        await io.mkdirP(newVersionPath);
    } catch (e) {
    }

    await updateInstaller(latestVersionPath, newVersionPath, latestVersion, newVersion, typeToUrl);
    await replaceContent(latestVersionPath, newVersionPath, latestVersion, newVersion, 'eloston.ungoogled-chromium.locale.en-US.yaml');
    await replaceContent(latestVersionPath, newVersionPath, latestVersion, newVersion, 'eloston.ungoogled-chromium.yaml');

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
    await exec.exec('.\\wingetcreate.exe', ['submit', '-t', token, newVersionPath]);
}

async function replaceContent(latestVersionPath, newVersionPath, latestVersion, newVersion, fileName) {
    const content = await fs.readFile(path.join(latestVersionPath, fileName), {encoding: 'utf-8'});
    const newContent = content.replaceAll(latestVersion, newVersion);
    await fs.writeFile(path.join(newVersionPath, fileName), newContent, {encoding: 'utf-8'});
}

async function updateInstaller(latestVersionPath, newVersionPath, latestVersion, newVersion, typeToUrl) {
    const content = await fs.readFile(path.join(latestVersionPath, 'eloston.ungoogled-chromium.installer.yaml'), {encoding: 'utf-8'});
    const data = yaml.load(content);
    data.PackageVersion = newVersion;
    data.ReleaseDate = new Date().toLocaleDateString('en-CA');
    for (const installer of data.Installers) {
        const type = `${installer.Architecture}.${installer.InstallerType}`;
        const {url, digest} = typeToUrl.get(type);
        installer.InstallerUrl = url;
        let sha256 = '';
        if (digest.startsWith('sha256:')) {
            sha256 = digest.slice(7).toUpperCase();
        } else {
            sha256 = await calculateSHA256(url);
        }
        installer.InstallerSha256 = sha256;
    }

    // Update verions in RelativeFilePath
    const newContent = yaml.dump(data, {noRefs: true}).replaceAll(latestVersion, newVersion);
    await fs.writeFile(path.join(newVersionPath, 'eloston.ungoogled-chromium.installer.yaml'), newContent, {encoding: 'utf-8'});
}

function calculateSHA256(url) {
    const hash = crypto.createHash('sha256');
    return new Promise((resolve, reject) => {
        https.get(url, resp => {
            resp.on('data', chunk => hash.update(chunk));
            resp.on('end', () => resolve(hash.digest('hex').toUpperCase()));
        }).on('error', reject);
    });
}

async function syncRepo(token) {
    await exec.exec('git', ['clone', `https://x-access-token:${token}@github.com/Nifury/winget-pkgs.git`]);
    await exec.exec('git', ['remote', 'add', 'upstream', 'https://github.com/microsoft/winget-pkgs.git'], {cwd: '.\\winget-pkgs'});
    await exec.exec('git', ['fetch', 'upstream', 'master'], {cwd: '.\\winget-pkgs'});
    await exec.exec('git', ['reset', '--hard', 'upstream/master'], {cwd: '.\\winget-pkgs'});
    await exec.exec('git', ['push', 'origin', 'master', '--force'], {cwd: '.\\winget-pkgs'});
}

run().catch(err => core.setFailed(err.message));