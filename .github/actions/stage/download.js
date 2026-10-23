import { DefaultArtifactClient } from '@actions/artifact';

// Runs in a separate process so file handles leaked by failed download retries
// in @actions/artifact are released before the downloaded archive is extracted.
async function run() {
    const [artifactName, path] = process.argv.slice(2);
    const artifact = new DefaultArtifactClient();
    const artifactInfo = await artifact.getArtifact(artifactName);
    await artifact.downloadArtifact(artifactInfo.artifact.id, {path});
}

run().catch(err => {
    console.error(err);
    process.exit(1);
});
