# Project Detection

Treat actual manifests, lockfiles, wrappers, and configuration as the source of truth.

| Area | Primary evidence |
| --- | --- |
| Node / Web | `package.json`, `packageManager`, lockfiles, framework configuration, scripts |
| Python | `pyproject.toml`, `uv.lock`, `poetry.lock`, requirements files, tool configuration |
| Rust | `Cargo.toml`, workspace configuration, binaries/examples |
| Go | `go.mod`, `cmd/`, Makefile, Taskfile |
| .NET | `*.sln`, `*.csproj`, target frameworks, launch settings |
| Flutter | `pubspec.yaml`, platform directories, test/driver configuration |
| Android | `settings.gradle*`, module Gradle files, wrapper tasks |
| Swift | `Package.swift`, `*.xcodeproj`, `*.xcworkspace`, discoverable schemes |
| Unity | `ProjectSettings/ProjectVersion.txt`, `Packages/manifest.json`, scenes, test assemblies |
| Godot | `project.godot`, main scene, add-ons, test commands |
| Unreal | `*.uproject`, modules, targets, automation commands |
| Java | `pom.xml`, Gradle files, wrapper tasks |
| Monorepo | workspace manifests, task runners, package boundaries |

## Package manager

- Use the package manager supported by both the manifest declaration and the lockfile.
- If multiple lockfiles conflict, do not choose the newest one automatically. Check repository documentation and actual execution evidence.
- Prefer a checked-in wrapper over a globally installed tool.

## Entry point

Look for:

- the official scaffold's default entry point
- manifest `bin`, `start`, or `main` declarations
- framework route or app directories
- an engine's main scene or project file
- the startup target in a solution or project

## Commands

Find command candidates in this order:

1. manifest scripts or a task runner
2. checked-in wrapper
3. project documentation and CI
4. framework or engine configuration

Do not create commands from convention alone.

## UI tooling

Look for:

- Storybook or component preview
- Playwright, Cypress, or other browser tests
- visual-regression or screenshot scripts
- simulator or device commands
- game test scenes, input tests, and capture paths

## State decision

- no manifest and no entry point: `empty`
- manifest and entry point exist, but baseline run/build or the command table is unverified: `scaffolded`
- command table matches the repository and minimum baseline validation passes: `operational`
