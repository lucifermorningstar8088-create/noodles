# Windows Desktop Installer

Noodles uses a small Windows bootstrapper to install a larger, versioned desktop package from this repository's GitHub Releases.

## User installation flow

1. Download `NoodlesSetup.exe` from the latest GitHub Release.
2. Run it on Windows 10/11 x64 with an internet connection.
3. The setup window fetches the latest release metadata, downloads the desktop ZIP and its SHA-256 file, and checks the ZIP before extracting it.
4. Files are installed per-user under `%LOCALAPPDATA%\Programs\Noodles\versions\<release-tag>\`. A desktop shortcut is created.
5. Launch Noodles from the shortcut or the setup window.

The bootstrapper does not need administrator privileges. It downloads only from the release assets named in the official Noodles repository's release metadata. The checksum detects transfer/corruption errors; it is not a substitute for a publisher signature if the GitHub account or release itself is compromised.

## Release process

A Windows x64 release is built by `.github/workflows/release-windows-desktop.yml`.

- Push a version tag such as `v0.2.0` to build and publish the release assets.
- The workflow builds the Python desktop app into a Windows folder bundle, archives it as `noodles-windows-x64.zip`, writes a SHA-256 checksum, and compiles the small WinForms bootstrapper as `NoodlesSetup.exe`.
- `workflow_dispatch` can run the build manually; on a branch, the output is available as a GitHub Actions artifact instead of a Release.

The bootstrapper is a .NET Framework WinForms executable. Windows systems without the required .NET Framework may not run it. The desktop app uses Microsoft's Edge WebView2 runtime; if that runtime is absent, the app currently shows a startup error rather than silently downloading and installing a browser runtime.

## Important scope and current limitations

- The bootstrapper and desktop package require internet access for the first install.
- GGUF model files are deliberately not bundled: they can be several gigabytes and have model-specific licenses.
- This release pipeline packages the current Noodles Python API and UI. It does **not** by itself guarantee that a compatible `llama-cpp-python` native runtime or a GGUF model is installed. Local inference remains unavailable until the required runtime and a model are present.
- The app binds its API to a random loopback port for the embedded window. It does not expose the local API to the network.
- A SHA-256 checksum is used for corruption detection. Code signing and signed-release verification are separate future hardening tasks.
- Release builds must pass the Windows workflow before an installer is considered usable. A source change or successful commit alone is not proof that the generated executable runs correctly on a user's PC.

## Developer smoke test

On Windows with Python 3.12 and uv installed:

```powershell
uv sync --extra desktop
uv run noodles-desktop
```

This starts the local API and opens the Noodles UI in a native WebView window. The packaged release is built in CI by the release workflow.
