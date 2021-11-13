#! /usr/bin/env python3
# Downloads and updates Stardew Valley mods, using mods.yaml as a manifest.
# Types of mods:
# - githubMods: Mods whose code is on GitHub and that use GitHub releases to
#               release their code.  Pulls down the latest version of the mod.

import yaml
import os
import shutil
import urllib.request
import json
import tempfile
import zipfile
import subprocess

MODS_MANIFEST_FILENAME = "mods.yaml"
MODS_BASE_DIRECTORY = os.path.expanduser(
    "~/.local/share/Steam/steamapps/common/Stardew Valley/Mods"
)
MODS_MANAGED_DIRNAME = "GitMods"

MODS_DIR = os.path.join(MODS_BASE_DIRECTORY, MODS_MANAGED_DIRNAME)


def loadConfig():
    with open(
        os.path.join(MODS_BASE_DIRECTORY, MODS_MANIFEST_FILENAME), "r"
    ) as manifest:
        return yaml.safe_load(manifest.read())


def log(modName, str):
    print(f"[{modName}]: {str}")


def installFromZipUrl(modName, zipUrl):
    log(modName, "Downloading mod...")

    with tempfile.TemporaryDirectory() as tmpDirName:
        downloadedZip = os.path.join(tmpDirName, f"{modName}.zip")
        try:
            urllib.request.urlretrieve(zipUrl, downloadedZip)
        except urllib.error.HTTPError:
            log(modName, "Unable to download mod zip")

        try:
            with zipfile.ZipFile(downloadedZip, "r") as zipFile:
                zipFile.extractall(os.path.join(MODS_DIR, modName))
        except:
            log(modName, "Unable to extract mod zip")
            return

    log(modName, "Installation complete.")


def installLatestGitHubRelease(modName, modRepo):
    releaseUrl = f"https://api.github.com/repos/{modRepo}/releases/latest"
    try:
        with urllib.request.urlopen(releaseUrl) as url:
            releases = json.loads(url.read().decode())
    except urllib.error.HTTPError as error:
        if error.code == 404:
            log(modName, "Repo is no longer hosting releases.")
        else:
            log(modName, "Unable to reach GitHub")

        return

    assetUrl = None

    # Valid mod names  are {modName}.zip and {modName}.(.*).zip
    for asset in releases["assets"]:
        name = asset["name"]

        isExactAssetName = name == f"{modName}.zip"
        isAssetNameWithVersion = name.startswith(f"{modName}.") and name.endswith(
            ".zip"
        )

        if isExactAssetName or isAssetNameWithVersion:
            assetUrl = asset["browser_download_url"]

    if assetUrl is None:
        log(modName, "Assets do not contain expected zip file.")
        return

    installFromZipUrl(modName, assetUrl)


def main():
    config = loadConfig()

    completeModList = list(config["githubReleaseMods"].keys()) + list(
        config["mirrorMods"].keys()
    )

    print("Detecting the following mods: ", ", ".join(completeModList))

    # Clean out the Mods Directory
    if os.path.exists(MODS_DIR):
        shutil.rmtree(MODS_DIR)
    os.makedirs(MODS_DIR)

    # GitHub Mods that use releases
    for modName in config["githubReleaseMods"]:
        modRepo = config["githubReleaseMods"][modName]
        installLatestGitHubRelease(modName, modRepo)

    # GitHub Mods that use a static file mirror
    for modName in config["mirrorMods"]:
        modUrl = config["mirrorMods"][modName]
        installFromZipUrl(modName, modUrl)


if __name__ == "__main__":
    main()
