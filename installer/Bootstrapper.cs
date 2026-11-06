using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

internal sealed class BootstrapperForm : Form
{
    private const string Repository = "lucifermorningstar8088-create/noodles";
    private const string PackageName = "noodles-windows-x64.zip";
    private const string ChecksumName = "noodles-windows-x64.zip.sha256";
    private readonly Label status = new Label();
    private readonly ProgressBar progress = new ProgressBar();
    private readonly Button retry = new Button();
    private readonly Button launch = new Button();
    private string installedExe = "";

    public BootstrapperForm()
    {
        Text = "Noodles Setup";
        StartPosition = FormStartPosition.CenterScreen;
        ClientSize = new Size(500, 190);
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        MinimizeBox = true;
        BackColor = Color.White;

        var title = new Label
        {
            Text = "Noodles Desktop",
            Font = new Font("Segoe UI", 16, FontStyle.Bold),
            AutoSize = true,
            Location = new Point(24, 18)
        };
        status.Text = "Connecting to the official GitHub release...";
        status.Font = new Font("Segoe UI", 9);
        status.AutoEllipsis = true;
        status.SetBounds(26, 62, 448, 34);

        progress.SetBounds(26, 102, 448, 18);
        progress.Style = ProgressBarStyle.Marquee;
        progress.MarqueeAnimationSpeed = 25;

        retry.Text = "Retry";
        retry.SetBounds(276, 140, 90, 30);
        retry.Enabled = false;
        retry.Click += async delegate { await InstallAsync(); };

        launch.Text = "Launch Noodles";
        launch.SetBounds(374, 140, 100, 30);
        launch.Enabled = false;
        launch.Click += delegate
        {
            try
            {
                Process.Start(new ProcessStartInfo(installedExe) { UseShellExecute = true });
                Close();
            }
            catch (Exception ex)
            {
                ShowFailure("Noodles is installed, but could not be launched: " + ex.Message);
            }
        };

        Controls.Add(title);
        Controls.Add(status);
        Controls.Add(progress);
        Controls.Add(retry);
        Controls.Add(launch);
        Shown += async delegate { await InstallAsync(); };
    }

    private async Task InstallAsync()
    {
        retry.Enabled = false;
        launch.Enabled = false;
        progress.Style = ProgressBarStyle.Marquee;
        status.Text = "Checking the latest official release...";
        string tempRoot = Path.Combine(Path.GetTempPath(), "NoodlesSetup-" + Guid.NewGuid().ToString("N"));
        try
        {
            Directory.CreateDirectory(tempRoot);
            using (var client = new HttpClient())
            {
                client.Timeout = TimeSpan.FromMinutes(15);
                client.DefaultRequestHeaders.UserAgent.ParseAdd("Noodles-Windows-Bootstrapper/1.0");
                client.DefaultRequestHeaders.Accept.ParseAdd("application/vnd.github+json");

                string releaseJson = await client.GetStringAsync(
                    "https://api.github.com/repos/" + Repository + "/releases/latest");
                var serializer = new System.Web.Script.Serialization.JavaScriptSerializer();
                var release = serializer.DeserializeObject(releaseJson) as Dictionary<string, object>;
                if (release == null || !release.ContainsKey("tag_name") || !release.ContainsKey("assets"))
                    throw new InvalidDataException("GitHub returned an invalid release response.");

                string tag = Convert.ToString(release["tag_name"]);
                var assets = release["assets"] as object[];
                string packageUrl = FindAsset(assets, PackageName);
                string checksumUrl = FindAsset(assets, ChecksumName);
                if (String.IsNullOrWhiteSpace(tag) || String.IsNullOrWhiteSpace(packageUrl) ||
                    String.IsNullOrWhiteSpace(checksumUrl))
                    throw new InvalidDataException("The latest release is missing the Windows package or checksum.");

                string zipPath = Path.Combine(tempRoot, PackageName);
                string checksumPath = Path.Combine(tempRoot, ChecksumName);
                status.Text = "Downloading Noodles " + tag + "...";
                await DownloadToFileAsync(client, packageUrl, zipPath);
                status.Text = "Verifying package integrity...";
                await DownloadToFileAsync(client, checksumUrl, checksumPath);
                string expected = File.ReadAllText(checksumPath).Trim().Split(new[] { ' ', '\t', '\r', '\n' },
                    StringSplitOptions.RemoveEmptyEntries)[0];
                if (expected.Length != 64 || !IsHex(expected))
                    throw new InvalidDataException("The release checksum file is invalid.");
                string actual;
                using (var sha = SHA256.Create())
                using (var stream = File.OpenRead(zipPath))
                    actual = BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", "").ToLowerInvariant();
                if (!String.Equals(actual, expected, StringComparison.OrdinalIgnoreCase))
                    throw new InvalidDataException("Checksum verification failed. The package was not installed.");

                string versionRoot = Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                    "Programs", "Noodles", "versions", SafeTag(tag));
                if (!File.Exists(Path.Combine(versionRoot, "Noodles.exe")))
                {
                    status.Text = "Installing application files...";
                    string staging = versionRoot + ".staging-" + Guid.NewGuid().ToString("N");
                    Directory.CreateDirectory(staging);
                    try
                    {
                        ExtractSafely(zipPath, staging);
                        if (!File.Exists(Path.Combine(staging, "Noodles.exe")))
                            throw new InvalidDataException("The release package does not contain Noodles.exe.");
                        Directory.CreateDirectory(Path.GetDirectoryName(versionRoot));
                        if (Directory.Exists(versionRoot))
                            Directory.Delete(versionRoot, true);
                        Directory.Move(staging, versionRoot);
                    }
                    catch
                    {
                        if (Directory.Exists(staging))
                            Directory.Delete(staging, true);
                        throw;
                    }
                }

                installedExe = Path.Combine(versionRoot, "Noodles.exe");
                CreateShortcut(installedExe, versionRoot);
                status.Text = "Installation complete. You can now launch Noodles.";
                progress.Style = ProgressBarStyle.Continuous;
                progress.Value = 100;
                launch.Enabled = true;
                retry.Enabled = false;
            }
        }
        catch (Exception ex)
        {
            ShowFailure("Setup could not finish: " + ex.Message);
        }
        finally
        {
            try { if (Directory.Exists(tempRoot)) Directory.Delete(tempRoot, true); }
            catch (IOException) { }
            catch (UnauthorizedAccessException) { }
        }
    }

    private void ShowFailure(string message)
    {
        status.Text = message.Length > 115 ? message.Substring(0, 112) + "..." : message;
        status.ForeColor = Color.DarkRed;
        progress.Style = ProgressBarStyle.Continuous;
        progress.Value = 0;
        retry.Enabled = true;
        MessageBox.Show(this, message, "Noodles Setup", MessageBoxButtons.OK, MessageBoxIcon.Error);
    }

    private static string FindAsset(object[] assets, string name)
    {
        if (assets == null) return "";
        foreach (object item in assets)
        {
            var asset = item as Dictionary<string, object>;
            if (asset == null) continue;
            if (String.Equals(Convert.ToString(asset.ContainsKey("name") ? asset["name"] : ""),
                name, StringComparison.OrdinalIgnoreCase))
            {
                string url = Convert.ToString(
                    asset.ContainsKey("browser_download_url") ? asset["browser_download_url"] : "");
                Uri parsed;
                string expectedPrefix = "/" + Repository + "/releases/download/";
                if (!Uri.TryCreate(url, UriKind.Absolute, out parsed) ||
                    !String.Equals(parsed.Scheme, Uri.UriSchemeHttps, StringComparison.OrdinalIgnoreCase) ||
                    !String.Equals(parsed.Host, "github.com", StringComparison.OrdinalIgnoreCase) ||
                    !parsed.AbsolutePath.StartsWith(expectedPrefix, StringComparison.OrdinalIgnoreCase))
                    throw new InvalidDataException("A release asset URL failed validation.");
                return url;
            }
        }
        return "";
    }

    private static async Task DownloadToFileAsync(HttpClient client, string url, string path)
    {
        using (var response = await client.GetAsync(url, HttpCompletionOption.ResponseHeadersRead))
        {
            response.EnsureSuccessStatusCode();
            if (response.Content.Headers.ContentLength.HasValue &&
                response.Content.Headers.ContentLength.Value > 1500L * 1024L * 1024L)
                throw new InvalidDataException("The release asset is larger than the 1.5 GB safety limit.");
            using (var input = await response.Content.ReadAsStreamAsync())
            using (var output = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.None))
                await input.CopyToAsync(output);
        }
    }

    private static void ExtractSafely(string zipPath, string destination)
    {
        string root = Path.GetFullPath(destination).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        using (var archive = ZipFile.OpenRead(zipPath))
        {
            if (archive.Entries.Count > 50000)
                throw new InvalidDataException("The release archive contains too many entries.");
            long totalBytes = 0;
            foreach (ZipArchiveEntry entry in archive.Entries)
            {
                totalBytes += entry.Length;
                if (totalBytes > 2L * 1024L * 1024L * 1024L)
                    throw new InvalidDataException("The extracted package exceeds the 2 GB safety limit.");
                string target = Path.GetFullPath(Path.Combine(destination,
                    entry.FullName.Replace('/', Path.DirectorySeparatorChar).Replace('\\', Path.DirectorySeparatorChar)));
                if (!target.StartsWith(root, StringComparison.OrdinalIgnoreCase))
                    throw new InvalidDataException("The archive contains an unsafe file path.");
                if (entry.FullName.EndsWith("/", StringComparison.Ordinal) ||
                    entry.FullName.EndsWith("\\", StringComparison.Ordinal))
                {
                    Directory.CreateDirectory(target);
                    continue;
                }
                string parent = Path.GetDirectoryName(target);
                if (String.IsNullOrEmpty(parent)) throw new InvalidDataException("Invalid archive path.");
                Directory.CreateDirectory(parent);
                using (var input = entry.Open())
                using (var output = new FileStream(target, FileMode.CreateNew, FileAccess.Write, FileShare.None))
                    input.CopyTo(output);
            }
        }
    }

    private static bool IsHex(string value)
    {
        foreach (char c in value)
            if (!Uri.IsHexDigit(c)) return false;
        return true;
    }

    private static string SafeTag(string tag)
    {
        var builder = new StringBuilder();
        foreach (char c in tag)
            builder.Append(Char.IsLetterOrDigit(c) || c == '.' || c == '-' || c == '_' ? c : '_');
        if (builder.Length == 0) throw new InvalidDataException("Release tag is empty.");
        return builder.ToString();
    }

    private static void CreateShortcut(string exePath, string workingDirectory)
    {
        string desktop = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory);
        string shortcutPath = Path.Combine(desktop, "Noodles.lnk");
        Type shellType = Type.GetTypeFromProgID("WScript.Shell");
        if (shellType == null) return;
        object shell = Activator.CreateInstance(shellType);
        try
        {
            dynamic shellObject = shell;
            dynamic shortcut = shellObject.CreateShortcut(shortcutPath);
            shortcut.TargetPath = exePath;
            shortcut.WorkingDirectory = workingDirectory;
            shortcut.IconLocation = exePath;
            shortcut.Description = "Noodles local AI desktop workspace";
            shortcut.Save();
        }
        finally
        {
            if (shell != null && System.Runtime.InteropServices.Marshal.IsComObject(shell))
                System.Runtime.InteropServices.Marshal.ReleaseComObject(shell);
        }
    }
}

internal static class Program
{
    [STAThread]
    private static void Main()
    {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        Application.Run(new BootstrapperForm());
    }
}
