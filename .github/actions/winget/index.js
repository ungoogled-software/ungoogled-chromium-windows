const YAML = require('yaml');
const exec = require('@actions/exec');
const core = require("@actions/core");

async function run() {
    const token = core.getInput('token', {
        required: true,
        trimWhitespace: true
    });
    await exec.exec('git', ['clone', `https://x-access-token:${token}@github.com/microsoft/winget-pkgs.git`]);

}

run().catch(err => core.setFailed(err.message));