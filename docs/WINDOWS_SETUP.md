# Windows Installation & Troubleshooting Guide

SaveToken provides native, first-class support for Windows 10/11 across Command Prompt (`cmd.exe`), PowerShell, and Git Bash.

---

## 1. Quick Installation on Windows

### Option A: Using PowerShell (Recommended)
Open PowerShell and navigate to the `SaveToken` directory:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install.ps1
```

### Option B: Using Command Prompt (`cmd.exe`)
```cmd
install.bat
```

### Option C: Using Python directly
```cmd
python scripts\install_antigravity.py
```

---

## 2. Setting Up PATH

The installer puts the `te` commands in `%USERPROFILE%\.tokeneconomizer\bin`.

To use `te` from any terminal window:
1. Press `Win + R`, type `sysdm.cpl`, and hit Enter.
2. Go to the **Advanced** tab and click **Environment Variables**.
3. Under **User variables**, select `Path` and click **Edit**.
4. Click **New** and add:
   ```
   %USERPROFILE%\.tokeneconomizer\bin
   ```
5. Click **OK** on all dialogs.
6. Open a new Command Prompt or PowerShell window and verify:
   ```cmd
   te doctor
   ```

---

## 3. How SaveToken Handles Windows Differences

1. **Python Executable Discovery**:
   On Windows, Python may be installed as `python.exe`, `py.exe` (Python Launcher), or `python3.exe`.
   SaveToken launchers (`te.cmd`, `te.ps1`, and `antigravity_hook.cmd`) automatically detect which launcher is available without manual configuration.

2. **Console & Subprocess Spawning**:
   On Windows, background hooks must not open annoying pop-up console windows.
   SaveToken uses `CREATE_NO_WINDOW = 0x08000000` via `tokeneconomizer.plugin.winspawn` to execute hooks completely silently in the background.

3. **Path Separators & Home Expansion**:
   All core components use `pathlib.Path` and `os.path.normpath` with `os.path.expanduser("~")`, handling `%USERPROFILE%` and `C:\Users\...` natively.

4. **UTF-8 Encoding**:
   Windows terminals and Python runtimes historically default to CP1252. SaveToken launchers automatically enforce `PYTHONUTF8=1` to guarantee lossless handling of session logs and multilingual text.

---

## 4. Troubleshooting

- **`'te' is not recognized as an internal or external command`**:
  Ensure `%USERPROFILE%\.tokeneconomizer\bin` is added to your PATH environment variable, and restart your terminal.

- **`Microsoft Store opens when running python`**:
  This occurs when Windows App Execution Aliases intercept `python`. Either install Python from [python.org](https://www.python.org/) or disable the execution alias in Windows Settings (`Manage app execution aliases`).

- **Antigravity Hook Timeout**:
  If hooks take longer than expected, verify that your antivirus or Windows Defender is not scanning Python subprocesses synchronously.
