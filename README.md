# ungoogled-chromium-windows

Windows packaging for [ungoogled-chromium](//github.com/Eloston/ungoogled-chromium).

## Downloads

[Download binaries from the Contributor Binaries website](//ungoogled-software.github.io/ungoogled-chromium-binaries/).

Or install using `winget install --id=eloston.ungoogled-chromium -e`.

**Source Code**: It is recommended to use a tag via `git checkout` (see building instructions below). You may also use `master`, but it is for development and may not be stable.

## Building

Google only supports [Windows 10 x64 or newer](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/docs/windows_build_instructions.md#system-requirements). These instructions are tested on Windows 10 Pro x64.

NOTE: The default configuration will build 64-bit binaries for maximum security (TODO: Link some explanation). This can be changed to 32-bit by setting `target_cpu` to `"x86"` in `flags.windows.gn` or passing `--x86` as an argument to `build.py`.

### Setting up the build environment

**IMPORTANT**: Please setup only what is referenced below. Do NOT setup other Chromium compilation tools like `depot_tools`, since we have a custom build process which avoids using Google's pre-built binaries.

#### Setting up Visual Studio

[Follow the "Visual Studio" section of the official Windows build instructions](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/docs/windows_build_instructions.md#visual-studio).

* Make sure to read through the entire section and install/configure all the required components.
* If your Visual Studio is installed in a directory other than the default, you'll need to set a few environment variables to point the toolchains to your installation path. (Copied from [instructions for Electron](https://electronjs.org/docs/development/build-instructions-windows))
	* `vs2019_install = DRIVE:\path\to\Microsoft Visual Studio\2019\Community` (replace `2019` and `Community` with your installed versions)
	* `WINDOWSSDKDIR = DRIVE:\path\to\Windows Kits\10`
	* `GYP_MSVS_VERSION = 2019` (replace 2019 with your installed version's year)


#### Other build requirements

**IMPORTANT**: Currently, the `MAX_PATH` path length restriction (which is 260 characters by default) must be lifted in for our Python build scripts. This can be lifted in Windows 10 (v1607 or newer) with the official installer for Python 3.6 or newer (you will see a button at the end of installation to do this). See [Issue #345](https://github.com/Eloston/ungoogled-chromium/issues/345) for other methods for older Windows versions.

1. Setup the following:
    * 7-Zip
    * Python 3.8 or above (see note below for Python 3.12 or later)
		* Can be installed using WinGet or the Microsoft Store.
		* If you don't plan on using the Microsoft Store version of Python:
			* Check "Add python.exe to PATH" before install.
			* At the end of the Python installer, click the button to lift the `MAX_PATH` length restriction.
			* Disable the `python3.exe` and `python.exe` aliases in `Settings > Apps > Advanced app settings > App execution aliases`. They will typically be referred to as "App Installer". See [this question on stackoverflow.com](https://stackoverflow.com/questions/57485491/python-python3-executes-in-command-prompt-but-does-not-run-correctly) to understand why.
			* Ensure that your Python directory either has a copy of Python named "python3.exe" or a symlink linking to the Python executable.
		* The `httplib2` module. This can be installed using `pip install`.
	    * For Python 3.12 and later: the build.py script relies on distutils, which is removed from the standard library in 3.12. It is now provided by the setuptools library. Install it via `pip install setuptools`.
    * Make sure to lift the `MAX_PATH` length restriction, either by clicking the button at the end of the Python installer or by [following these instructions](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation?tabs=registry#:~:text=Enable,Later).
    * Git (to fetch all required ungoogled-chromium scripts)
        * During setup, make sure "Git from the command line and also from 3rd-party software" is selected. This is usually the recommended option.

### Building

Run in `Developer Command Prompt for VS` (as administrator):

```cmd
git clone --recurse-submodules https://github.com/ungoogled-software/ungoogled-chromium-windows.git
cd ungoogled-chromium-windows
# Replace TAG_OR_BRANCH_HERE with a tag or branch name
git checkout --recurse-submodules TAG_OR_BRANCH_HERE
python3 build.py
python3 package.py
```

A zip archive and an installer will be created under `build`.

**NOTE**: If the build fails, you must take additional steps before re-running the build:

* If the build fails while downloading the Chromium source code (which is during `build.py`), it can be fixed by removing `build\download_cache` and re-running the build instructions.
* If the build fails at any other point during `build.py`, it can be fixed by removing everything under `build` other than `build\download_cache` and re-running the build instructions. This will clear out all the code used by the build, and any files generated by the build.

An efficient way to delete large amounts of files is using `Remove-Item PATH -Recurse -Force`. Be careful however, files deleted by that command will be permanently lost.

## Developer info

### First-time setup

1. [Setup MSYS2](http://www.msys2.org/)
2. Run the following in a "MSYS2 MSYS" shell:

```sh
pacman -S quilt python3 vim tar dos2unix
# By default, there doesn't seem to be a vi command for less, quilt edit, etc.
ln -s /usr/bin/vim /usr/bin/vi
```

### Updating patches and pruning list

1. Start `Developer Command Prompt for VS` and `MSYS2 MSYS` shell and navigate to source folder
	1. `Developer Command Prompt for VS`
		* `cd c:\path\to\repo\ungoogled-chromium-windows`
	1. `MSYS2 MSYS`
		* `cd /path/to/repo/ungoogled-chromium-windows`
		* You can use Git Bash to determine the path to this repo
		* Or, you can find it yourself via `/<drive letter>/<path with forward slashes>`
1. Retrieve downloads
	**`Developer Command Prompt for VS`**
	* `mkdir "build\download_cache"`
	* `python3 ungoogled-chromium\utils\downloads.py retrieve -i downloads.ini -c build\download_cache`
1. Clone sources
	**`Developer Command Prompt for VS`**
	* `python3 ungoogled-chromium\utils\clone.py -o build\src`
1. Check for rust version change (see below)
1. Update pruning list
	**`Developer Command Prompt for VS`**
	* `python3 ungoogled-chromium\devutils\update_lists.py -t build\src --domain-regex ungoogled-chromium\domain_regex.list`
1. Unpack downloads
	**`Developer Command Prompt for VS`**
	* `python3 ungoogled-chromium\utils\downloads.py unpack -i downloads.ini -c build\download_cache build\src`
1. Apply ungoogled-chromium patches
	**`Developer Command Prompt for VS`**
	* `python3 ungoogled-chromium\utils\patches.py apply --patch-bin build\src\third_party\git\usr\bin\patch.exe build\src ungoogled-chromium\patches`
1. Update windows patches
	**`MSYS2 MSYS`**
	1. Setup shell to update patches
		* `source devutils/set_quilt_vars.sh`
	1. Go into the source tree
		* `cd build/src`
	1. Fix line breaks of files to patch
		* `grep -r ../../patches/ -e "^+++" | awk '{print substr($2,3)}' | xargs dos2unix`
	1. Use quilt to refresh patches. See ungoogled-chromium's [docs/developing.md](https://github.com/Eloston/ungoogled-chromium/blob/master/docs/developing.md#updating-patches) section "Updating patches" for more details
	1. Go back to repo root
		* `cd ../..`
	1. Sanity checking for consistency in series file
		* `./devutils/check_patch_files.sh`
1. Use Git to add changes and commit

### Update dependencies

**NOTE:** For all steps, update `downloads.ini` accordingly.

1. Check the [LLVM GitHub](https://github.com/llvm/llvm-project/releases/) for the latest version of LLVM.
	1. Download `LLVM-*-win64.exe` file.
	1. Get the SHA-512 checksum using `sha512sum` in **`MSYS2 MSYS`**.
1. Check the esbuild version in file `build/src/third_party/devtools-frontend/src/DEPS` and find the closest release in the [esbuild GitHub](https://github.com/evanw/esbuild/releases) to it.
	* Example: `version:3@0.24.0.chromium.2` should be `0.24.0`
1. Check the ninja version in file `build/src/third_party/devtools-frontend/src/DEPS` and find the closest release in the [ninja GitHub](https://github.com/ninja-build/ninja/releases/) to it.
	1. Download the `ninja-win.zip` file.
	1. Get the SHA-512 checksum using `sha512sum` in **`MSYS2 MSYS`**.
1. Check the [Git GitHub](https://github.com/git-for-windows/git/releases/) for the latest version of Git.
	1. Get the SHA-256 checksum for `PortableGit-<version>-64-bit.7z.exe`.
1. Check for commit hash changes of `src` submodule in `third_party/microsoft_dxheaders` (e.g. using GitHub `https://github.com/chromium/chromium/tree/<version>/third_party/microsoft_dxheaders`).
	1. Replace `version` with the Chromium version in `ungoogled-chromium/chromium_version.txt`.
1. Check the node version changes in `third_party/node/update_node_binaries` (e.g. using GitHub `https://github.com/chromium/chromium/tree/<version>/third_party/node/update_node_binaries`).
	1. Download the "Standalone Binary" version from the [NodeJS website](https://nodejs.org/en/download).
	1. Get the SHA-512 checksum using `sha512sum` in **`MSYS2 MSYS`**.
1. Check for version changes of windows rust crate (`third_party/rust/windows_x86_64_msvc/`).
	1. Download rust crate zip file.
	1. Get the SHA-512 checksum using `sha512sum` in **`MSYS2 MSYS`**.
	1. Update `patches/ungoogled-chromium/windows/windows-fix-building-with-rust.patch` accordingly.

### Update rust
1. Check `RUST_REVISION` constant in file `tools/rust/update_rust.py` in build root.
	* Example: Revision could be `f7b43542838f0a4a6cfdb17fbeadf45002042a77`
1. Get date for nightly rust build from the Rust GitHub page: `https://github.com/rust-lang/rust/commit/f7b43542838f0a4a6cfdb17fbeadf45002042a77`
	1. Replace `RUST_REVISION` with the obtained value
	1. Adapt `downloads.ini` accordingly
	* Example: The above revision corresponds to the nightly build date `2025-03-14` (`YYYY-mm-dd`)
1. Download nightly rust build from: `https://static.rust-lang.org/dist/<build-date>/rust-nightly-x86_64-pc-windows-msvc.tar.gz`
	1. Replace `build-date` with the obtained value
	1. Get the SHA-512 checksum using `sha512sum` in **`MSYS2 MSYS`**.
	1. Extract archive
	1. Execute `rustc\bin\rustc.exe -V` to get rust version string
	1. Adapt `patches\ungoogled-chromium\windows\windows-fix-building-with-rust.patch` accordingly
1. Download nightly rust build from: `https://static.rust-lang.org/dist/<build-date>/rust-nightly-i686-pc-windows-msvc.tar.gz`
	1. Replace `build-date` with the obtained value
	1. Get the SHA-512 checksum using `sha512sum` in **`MSYS2 MSYS`**.
1. Download nightly rust build from: `https://static.rust-lang.org/dist/<build-date>/rust-nightly-aarch64-pc-windows-msvc.tar.gz`
	1. Replace `build-date` with the obtained value
	1. Get the SHA-512 checksum using `sha512sum` in **`MSYS2 MSYS`**.
## License

See [LICENSE](LICENSE)
