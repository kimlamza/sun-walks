# 04 — Cursor and GitHub, from zero

Written for someone who has never coded. No prior knowledge assumed.

---

## The short version

- **Cursor** is where you write code. It is a text editor with AI built into it.
- **Git** is a system that records every version of your files, so you can always go back.
- **GitHub** is a website that stores your Git history online, as a backup and a shareable copy.

They are three separate things that work together. Cursor edits files, Git records the changes, GitHub holds the record.

---

## 1. What a code editor actually is

A code file is a plain text file. You could write Python in Notepad and it would run. An editor exists to make that pleasant rather than possible.

**Cursor** is a fork of **VS Code** — the most widely used code editor — with AI features added. Everything true of VS Code is true of Cursor, which means every VS Code tutorial and extension applies.

### The layout

| Area | What it is |
|---|---|
| **File tree** (left) | Every file in your project folder. Click to open |
| **Editor** (centre) | The file's contents. Tabs across the top, like a browser |
| **Terminal** (bottom, `` Ctrl+` ``) | A text prompt where you run commands — starting the app, installing libraries, using Git |
| **Chat / AI panel** (right, `Ctrl+L`) | Ask questions about your code |

**The terminal is the part that feels most alien and matters most.** It is the same PowerShell you have used with Claude Code, embedded in the editor. You type a command, press Enter, it does something and prints the result.

### The AI features

| Shortcut | What it does |
|---|---|
| `Ctrl+K` | Select some code, describe a change in plain English, Cursor rewrites it in place |
| `Ctrl+L` | Chat about your code. It can see the files you have open |
| `Ctrl+I` | Agent mode — describe a task, it edits multiple files. Powerful, and easy to over-rely on |
| `Tab` | Autocomplete. Suggests the rest of the line as you type. Press Tab to accept |

**A caution, given your stated goal.** You said the point is to work with code and understand it, not to have an app generated. Cursor's agent mode can write the whole project for you, and you will end up with something that works and that you cannot debug or explain. The discipline that pays off:

> Use `Ctrl+K` and chat to write code you then read line by line. When you do not understand a line, ask what it does before accepting it. Accept nothing you could not roughly explain to someone else.

That is slower for the first fortnight and much faster after it.

### `.cursorrules`

A plain text file in your project root holding standing instructions for Cursor's AI. For this project, something like:

```
This project is built by someone learning to code.
Explain what code does; do not just produce it.
Prefer clear, simple code over clever code.
Add comments explaining why, not what.
Python 3.12. Use type hints.
Never write a large block of code without explaining the approach first.
```

Worth setting up on day one. It changes the character of every interaction.

### Useful to know

**Claude Code runs inside Cursor's terminal.** You are not choosing between them. Open Cursor, press `` Ctrl+` ``, type `claude`, and you have the same session you have now, with the editor beside it. Many people use Cursor's inline AI for small edits and Claude Code in the terminal for larger, multi-file work.

---

## 2. What Git and GitHub actually are

### The problem they solve

You have `app.py`. It works. You change it. It breaks. You cannot remember what you changed.

The amateur solution is `app_v2.py`, `app_final.py`, `app_final_ACTUAL.py`. Git is the professional one.

**Git records a snapshot of your entire project every time you ask it to.** Every snapshot is labelled, dated and permanent. You can see exactly what changed between any two, and return to any of them.

### The vocabulary

| Term | Meaning |
|---|---|
| **Repository** ("repo") | A project folder that Git is tracking. Your `sun-walks` folder |
| **Commit** | One saved snapshot, with a message describing what changed |
| **Message** | Your note on a commit: "Add horizon ray march". Write these for your future self |
| **Branch** | A parallel line of work. `main` is the default. Experiment on a branch, merge it in when it works |
| **Remote** | A copy of the repo somewhere else — GitHub |
| **Push** | Send your commits to GitHub |
| **Pull** | Fetch commits from GitHub to your machine |
| **Clone** | Download a repo to a new machine for the first time |
| **`.gitignore`** | A list of files Git should ignore — big data files, passwords, temporary junk |

### Git vs GitHub

**Git** is a program on your computer. It works with no internet connection. It does the actual version tracking.

**GitHub** is a website owned by Microsoft that stores Git repositories online. It gives you a backup, a copy you can access from anywhere, and a place to share code.

You can use Git without GitHub. You cannot sensibly use GitHub without Git.

### The daily loop

Roughly five commands, and you will use three of them constantly:

```powershell
git status                          # what have I changed?
git add .                           # stage everything for the next snapshot
git commit -m "Add horizon lookup"  # take the snapshot
git push                            # send it to GitHub
git pull                            # get changes from GitHub
```

Cursor has buttons for all of these in its Source Control panel (the branch icon in the left sidebar). **Learn the commands anyway.** The buttons hide what is happening, and when something goes wrong the fix is always at the command line.

### Commit habits worth forming now

- **Commit often** — every time something works, not once a day. A commit costs nothing
- **One idea per commit.** "Add weather fetch" not "various changes"
- **Write the message for someone who has forgotten everything.** That person is you in three weeks
- **Never commit secrets.** API keys, passwords. Once pushed to GitHub, treat them as public forever — deleting them does not remove them from the history
- **Never commit large data.** GitHub rejects files over 100 MB. Your DEM goes in `.gitignore`

---

## 3. Setup, in order

Roughly 45 minutes. Do it in this order — each step depends on the last.

### Step 1 — Python

Download from [python.org](https://www.python.org/downloads/). Install **3.12** (not the newest; some geospatial libraries lag).

**Critical:** on the first installer screen, tick **"Add python.exe to PATH"**. It is easy to miss and everything fails confusingly without it.

Verify — open PowerShell:
```powershell
python --version
```
Should print `Python 3.12.x`.

### Step 2 — Git

Download from [git-scm.com](https://git-scm.com/download/win). Accept every default except one: when asked about the default editor, choose something you recognise rather than Vim, which is difficult to exit if you land in it by accident.

Verify:
```powershell
git --version
```

Then tell Git who you are — this is stamped on every commit:
```powershell
git config --global user.name "Kim Lamza"
git config --global user.email "kim.lamza@gmail.com"
```

### Step 3 — GitHub account

Sign up at [github.com](https://github.com). Free tier is more than enough — unlimited private repositories.

**Turn on two-factor authentication.** GitHub requires it, and it saves a forced interruption later.

### Step 4 — Cursor

Download from [cursor.com](https://cursor.com). Install. On first launch it offers to import VS Code settings — you have none, so skip.

Sign in. There is a free tier; the paid tier gives more AI usage. Start free and see whether you hit the limit.

### Step 5 — Create the repository

On github.com, click **New repository**:
- Name: `sun-walks`
- **Private** (you can make it public later; you cannot un-publish reliably)
- Tick **Add a README file**
- Add a `.gitignore` — choose the **Python** template

Then clone it to your machine. In PowerShell:

```powershell
cd C:\Claude\Work
git clone https://github.com/YOUR-USERNAME/sun-walks.git Sun-Walks-repo
```

A browser window will open to authenticate the first time.

> **Note on where this lives.** Your scoping documents are currently in `C:\Claude\Work\Sun-Walks\`, inside the Obsidian vault. Two sensible options: clone the repo separately as above and copy the `docs/` folder into it, or turn `Sun-Walks` itself into the repository by running `git init` inside it and connecting it to GitHub. The second keeps documents and code together, which is tidier — but means Obsidian will show your code files. Decide this before step 6; it is annoying to change later.

### Step 6 — Open it in Cursor

`File → Open Folder` → select the repo folder. The file tree appears on the left.

Open the terminal (`` Ctrl+` ``) and create a **virtual environment** — an isolated set of libraries for this project only, so it cannot break other Python work:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks the second command with an execution-policy error, run this once and retry:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

When active, your prompt is prefixed with `(.venv)`. **You must activate it in every new terminal session.** Forgetting is the single most common source of "but I installed that library" confusion.

Add `.venv/` to `.gitignore`.

### Step 7 — First commit

Create a file, then:

```powershell
git status
git add .
git commit -m "First commit"
git push
```

Refresh github.com. Your file is there. That is the whole loop, and you will repeat it several hundred times.

---

## 4. Concepts you will meet in the first week

| Term | What it means |
|---|---|
| **Package / library** | Someone else's code you use. Installed with `pip install rasterio` |
| **`pip`** | Python's installer |
| **`requirements.txt`** | A list of the libraries your project needs, so anyone can recreate the environment with `pip install -r requirements.txt` |
| **Virtual environment (`venv`)** | An isolated library set per project. Prevents version collisions |
| **Import** | `import numpy` — making a library available in a file |
| **Function** | A named, reusable block of code |
| **Module** | A `.py` file. `src/terrain.py` is the `terrain` module |
| **Traceback** | The error text when something breaks. **Read the bottom line first** — that is the actual error. The rest is the route it took to get there |
| **PATH** | The list of places Windows looks for programs. Why step 1's checkbox mattered |

### On errors

You will see a great many, and most of a beginner's time goes on them. This is normal and not a signal about your aptitude.

The habit that matters: **read the last line of the error before doing anything else.** It usually says exactly what is wrong — `FileNotFoundError`, `ModuleNotFoundError`, `KeyError`. Paste the whole traceback into Cursor's chat and ask what it means. Do not guess at fixes; understand the error first, then fix it.

---

## 5. What to do next

1. Complete steps 1–7. Nothing else can start until the toolchain works
2. Decide the repository location question in step 5
3. Export **three** GPX files of walks you know well — ideally one you know sits in shadow in winter, as a test case
4. Register at the OS Data Hub and download OS Terrain 50 for that area
5. Then start at step 2 of the build order in `03-app-design.md`

Work through the build order in sequence. Each step is small enough to finish in a sitting and produces something you can check, which is what keeps a first project moving.
