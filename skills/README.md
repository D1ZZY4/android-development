# Skills

All installable skill packages in this repository live here.
Each subdirectory is an independent skill installable via `npx skills add`.

## Available skills

| Skill | Description |
|---|---|
| [android-development](android-development/README.md) | Android platform engineering: ROM build, kernel, GKI, debug, SELinux repair, port ROM |

## Install

### Install all skills from this repo

```bash
npx skills add D1ZZY4/android-development --all
```

### Install a specific skill by name

```bash
npx skills add D1ZZY4/android-development --skill android-development
```

### Install more than one specific skill

```bash
npx skills add owner/repo --skill skill-a --skill skill-b
```

### List available skills before installing

```bash
npx skills add D1ZZY4/android-development --list
```
