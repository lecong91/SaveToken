#!/usr/bin/env python3
"""Cross-platform installer for SaveToken / TokenEconomizer on Google Antigravity.

Supports macOS, Linux, and Windows.
Installs the native Antigravity plugin with zero dependencies (pure stdlib).
"""
import json
import os
import shutil
import sys


def get_home_dir():
    return os.path.expanduser("~")


def get_antigravity_plugins_dir():
    # ~/.gemini/config/plugins on Unix, %USERPROFILE%\.gemini\config\plugins on Windows
    return os.path.join(get_home_dir(), ".gemini", "config", "plugins")


def get_te_home_dir():
    return os.path.join(get_home_dir(), ".tokeneconomizer")


def install(repo_root):
    print("=" * 60)
    print(" SaveToken / TokenEconomizer Installer for Google Antigravity")
    print("=" * 60)

    plugins_dir = get_antigravity_plugins_dir()
    target_plugin = os.path.join(plugins_dir, "tokeneconomizer")
    te_home = get_te_home_dir()
    te_bin = os.path.join(te_home, "bin")

    print(f"\n[1/4] Preparing target plugin directory:\n      {target_plugin}")
    os.makedirs(target_plugin, exist_ok=True)
    os.makedirs(te_bin, exist_ok=True)

    # 1. Copy plugin manifest, rules, skills, assets
    src_plugin = os.path.join(repo_root, "plugin")
    src_core = os.path.join(repo_root, "tokeneconomizer")

    for item in ["plugin.json", "hooks.json", "LICENSE", "README.md"]:
        src_file = os.path.join(src_plugin, item)
        if not os.path.exists(src_file):
            src_file = os.path.join(repo_root, item)
        if os.path.exists(src_file):
            shutil.copy2(src_file, os.path.join(target_plugin, item))

    for folder in ["rules", "assets"]:
        src_folder = os.path.join(src_plugin, folder)
        dst_folder = os.path.join(target_plugin, folder)
        if os.path.exists(src_folder):
            if os.path.exists(dst_folder):
                shutil.rmtree(dst_folder)
            shutil.copytree(src_folder, dst_folder)

    # Skills: copy from antigravity-skills or skills
    skills_src = os.path.join(src_plugin, "antigravity-skills")
    if not os.path.exists(skills_src):
        skills_src = os.path.join(src_plugin, "skills")
    if os.path.exists(skills_src):
        dst_skills = os.path.join(target_plugin, "skills")
        if os.path.exists(dst_skills):
            shutil.rmtree(dst_skills)
        shutil.copytree(skills_src, dst_skills)

    # 2. Copy scripts
    print("[2/4] Installing lifecycle hooks and CLI launchers...")
    dst_scripts = os.path.join(target_plugin, "scripts")
    if os.path.exists(dst_scripts):
        shutil.rmtree(dst_scripts)
    shutil.copytree(os.path.join(src_plugin, "scripts"), dst_scripts)

    # Set executable permissions on Unix
    if os.name != "nt":
        for script_name in ["antigravity_hook.py", "te", "te-hook"]:
            script_path = os.path.join(dst_scripts, script_name)
            if os.path.exists(script_path):
                os.chmod(script_path, 0o755)

    # 3. Bundle core package into lib/tokeneconomizer (Zero-dependency guarantee)
    print("[3/4] Bundling core zero-dependency package into plugin lib...")
    dst_lib = os.path.join(target_plugin, "lib", "tokeneconomizer")
    if os.path.exists(dst_lib):
        shutil.rmtree(dst_lib)
    os.makedirs(os.path.dirname(dst_lib), exist_ok=True)
    shutil.copytree(
        src_core,
        dst_lib,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache")
    )

    # 4. Configure global CLI link and default config
    print(f"[4/4] Setting up global CLI wrappers in {te_bin}...")
    
    # Unix launcher
    te_unix_path = os.path.join(te_bin, "te")
    target_te_script = os.path.join(dst_scripts, "te")
    with open(te_unix_path, "w", encoding="utf-8") as f:
        f.write(f'#!/bin/sh\nexec "{target_te_script}" "$@"\n')
    if os.name != "nt":
        os.chmod(te_unix_path, 0o755)

    # Windows CMD launcher
    te_cmd_path = os.path.join(te_bin, "te.cmd")
    with open(te_cmd_path, "w", encoding="utf-8") as f:
        f.write(f'@echo off\ncall "{os.path.join(dst_scripts, "te.cmd")}" %*\n')

    # Windows PowerShell launcher
    te_ps1_path = os.path.join(te_bin, "te.ps1")
    with open(te_ps1_path, "w", encoding="utf-8") as f:
        f.write(f'& "{os.path.join(dst_scripts, "te.ps1")}" @args\n')

    # Also copy bootstrap as safety fallback
    shutil.copy2(os.path.join(dst_scripts, "te_bootstrap.py"), os.path.join(te_bin, "te_bootstrap.py"))

    # Initialize default config if not exists
    config_file = os.path.join(te_home, "config.json")
    if not os.path.exists(config_file):
        default_config = {
            "version": 1,
            "microskills": "envfacts",
            "loopguard": "on",
            "toolprune": "auto",
            "hosts": {
                "antigravity": {"enabled": True},
                "claude": {"enabled": True}
            }
        }
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2)
            f.write("\n")
        print(f"      Created default configuration: {config_file}")

    print("\n" + "=" * 60)
    print(" Installation completed successfully!")
    print("=" * 60)
    print(f"Plugin location: {target_plugin}")
    print(f"CLI location:    {te_bin}")
    print("\nNext steps:")
    if os.name == "nt":
        print(f'1. Ensure "{te_bin}" is added to your Windows PATH.')
        print("2. In Command Prompt or PowerShell, verify with: te doctor")
    else:
        print(f'1. Add to PATH: export PATH="{te_bin}:$PATH"')
        print("2. In your terminal, verify with: te doctor")
    print("3. Restart Google Antigravity to activate the plugin.")
    print("=" * 60)
    return 0


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return install(repo_root)


if __name__ == "__main__":
    sys.exit(main())
