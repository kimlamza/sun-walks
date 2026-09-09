# 10 — Session 1, step by step

**Goal: by the end of this session you will have code on GitHub that computes today's sunrise and sunset for Canmore, and you will have checked it against a published table.**

Written for someone who has never done any of this. Every command is given in full. After each block there is a **✓ Check** — do not move on until it passes.

**Already done:** Cursor installed and signed in with Google; GitHub account created and linked to Cursor.

**Still to do:** everything below. Budget 2–3 hours including things going wrong. Losing 45 minutes to an installer is normal and says nothing about your aptitude.

---

## The one distinction that confuses everybody

**Git and GitHub are two different things.**

- **Git** is a program that runs on your laptop. It records versions of your files. **You have not installed it yet** — having a GitHub account does not install Git, any more than having a Gmail account installs Outlook
- **GitHub** is a website that stores Git's history online

Step 2 installs Git. That is the missing piece.

---

## Step 1 — Install Python

1. Go directly to **[python.org/downloads/release/python-31315](https://www.python.org/downloads/release/python-31315/)**
2. Scroll to the **Files** table at the bottom and click **"Windows installer (64-bit)"**

**Use 3.13, not the newest.** As of September 2026 the site pushes you to 3.14, but some geospatial libraries — `rasterio` especially — lag a release behind on Windows wheels. 3.13 has been out nearly two years, so everything is built for it.

⚠ **Do not download a "source tarball"** (`.tgz` or `.tar.xz`). That is raw source code you would have to compile yourself. You want the `.exe` installer.

⚠ **Python 3.12 is no longer an option.** It has moved to "security fixes only", which means source-only releases — **3.12.10 (April 2025) was the last version with a Windows installer.** An earlier draft of this document recommended 3.12; that advice is out of date.

3. Run the installer
4. **On the very first screen, tick "Add python.exe to PATH"** at the bottom

That checkbox is the single most-missed step in this entire document. Without it, Windows cannot find Python and everything afterwards fails with a confusing error.

5. Click **Install Now**
6. When it finishes, **close any PowerShell window that is already open**. PATH changes only apply to windows opened afterwards

**✓ Check** — open a *new* PowerShell (Start menu → type "PowerShell") and run:

```powershell
python --version
```

You should see `Python 3.13.x`.

**If the Microsoft Store opens instead**, the PATH checkbox was missed. Either re-run the installer and choose Modify, or use `py` instead of `python` everywhere below — the `py` launcher is installed regardless and works fine.

---

## Step 2 — Install Git

1. Go to **[git-scm.com/download/win](https://git-scm.com/download/win)** — the download starts automatically
2. Run the installer
3. **Accept every default except one:** when it asks which editor Git should use, change it from **Vim** to **Notepad** or **Visual Studio Code**

Vim is a text editor that is genuinely difficult to exit if you land in it unexpectedly. There is no reason to risk it.

4. Click through the remaining screens and install
5. **Close and reopen PowerShell again**

**✓ Check**

```powershell
git --version
```

You should see `git version 2.4x.x`.

---

## Step 3 — Tell Git who you are

Git stamps your name and email on every saved version. Run these two commands, once, ever:

```powershell
git config --global user.name "Kim Lamza"
git config --global user.email "kim.lamza@gmail.com"
```

Use the **same email as your GitHub account** so your commits are linked to your profile.

**✓ Check**

```powershell
git config --global --list
```

You should see your name and email listed back.

---

## Step 4 — Open the project in Cursor

1. Open Cursor
2. **File → Open Folder**
3. Select `C:\Claude\Work\Sun-Walks`
4. If it asks whether you trust the authors of this folder, say **yes** — it is your own folder

You should now see the file tree on the left: `CLAUDE.md`, `README.md`, and the `docs` folder.

**Open the terminal inside Cursor:** press `` Ctrl+` `` — that is the backtick key, immediately left of the `1` key.

A panel opens at the bottom with a prompt reading something like:

```
PS C:\Claude\Work\Sun-Walks>
```

**This terminal is where every command below goes.** It is the same PowerShell as before, just embedded in the editor so you can see your files while you work.

---

## Step 5 — Turn the folder into a Git repository

A repository is just a folder Git is watching. This command starts the watching:

```powershell
git init -b main
```

`-b main` names the default branch `main`, which is what GitHub expects.

**✓ Check**

```powershell
git status
```

You should see a list of "Untracked files" — your markdown documents. Untracked means Git can see them but is not yet recording them.

---

## Step 6 — Create `.gitignore` before anything else

`.gitignore` is a list of things Git should ignore — large data files, temporary junk, anything with a password in it. **Create it before your first commit**, so junk never enters the history in the first place. Removing things later is far more painful.

In Cursor's file tree, right-click in the empty space below your files → **New File** → name it exactly:

```
.gitignore
```

Yes, it starts with a dot and has no other extension. Paste this in and save with `Ctrl+S`:

```
# Large data — rebuilt by script, never committed
data/dem/
data/horizons/

# Python
__pycache__/
*.pyc
.venv/

# Secrets
.env
.streamlit/secrets.toml

# OS junk
Thumbs.db
.DS_Store
```

---

## Step 7 — Your first commit

A **commit** is one saved snapshot of the whole project, with a note describing it.

```powershell
git add .
```

`git add .` stages everything — "include all of this in the next snapshot". The `.` means "this folder and everything in it".

```powershell
git commit -m "Add scoping documents"
```

`-m` supplies the message. Write these for yourself in three weeks' time, when you have forgotten everything.

**✓ Check**

```powershell
git log --oneline
```

One line, showing a short code and your message. **You have just made your first commit.** It exists only on your laptop so far.

---

## Step 8 — Create the repository on GitHub

1. Go to **[github.com](https://github.com)** and sign in
2. Top right, click **+** → **New repository**
3. **Repository name:** `sun-walks`
4. Select **Private**
5. **⚠ Do NOT tick "Add a README file". Do NOT add a .gitignore or a licence.**

This is the classic trap. Those options create a first commit on GitHub's side, which then conflicts with the commit you just made locally, and your first `git push` fails with an unhelpful error. Leave the repository completely empty.

6. Click **Create repository**

GitHub shows you a page of setup commands. Ignore most of it — you only need the URL, which looks like:

```
https://github.com/YOUR-USERNAME/sun-walks.git
```

---

## Step 9 — Connect and push

Back in Cursor's terminal, substituting your actual username:

```powershell
git remote add origin https://github.com/kimlamza/sun-walks.git
```

⚠ **Substitute your real username — do not paste a placeholder.** Pasting `YOUR-USERNAME` literally produces `remote: Repository not found`, which looks like a missing repository but is only a bad URL. If it happens, correct it with `git remote set-url origin <real url>` — `set-url` rather than `add`, because `origin` already exists.

`origin` is just a nickname for "the copy on GitHub". Then:

```powershell
git push -u origin main
```

**A browser window will pop up asking you to authorise Git.** This is normal and expected — it is Git Credential Manager linking your laptop to your GitHub account. Approve it. You will not be asked again.

**✓ Check** — refresh your repository page on github.com. Your documents are there.

**That is the whole loop**, and you will repeat it several hundred times: change files → `git add .` → `git commit -m "..."` → `git push`.

---

## Step 10 — Create a virtual environment

A **virtual environment** is a private set of libraries for this project alone, so installing something here can never break other Python work on your machine.

```powershell
python -m venv .venv
```

Takes a few seconds and creates a `.venv` folder. Then activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

**If you get a red error mentioning "execution policy"** — Windows blocking scripts by default — run this once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Answer `Y`, then run the activate command again.

**✓ Check** — your prompt now starts with `(.venv)`:

```
(.venv) PS C:\Claude\Work\Sun-Walks>
```

**⚠ You must activate the environment in every new terminal you open.** Forgetting is the single most common source of "but I installed that library" confusion. If something is suddenly "not found", check for `(.venv)` first.

`.venv` is already in your `.gitignore`, so it will not be committed.

---

## Step 11 — Install the libraries

```powershell
pip install pvlib pandas
```

Takes a minute. `pvlib` computes solar position; `pandas` handles tables of times and values.

Then record what the project needs, so the environment can be rebuilt on any machine:

```powershell
pip freeze > requirements.txt
```

**✓ Check** — a `requirements.txt` file appears in your file tree.

---

## Step 12 — Write the sun calculator

In Cursor's file tree: right-click empty space → **New Folder** → `src`. Then right-click `src` → **New File** → `sun.py`.

Paste this in and save:

```python
"""
Solar position for Canmore, Alberta.

Session 1 deliverable: prove the toolchain works end to end, and check the
computed sunrise and sunset against a published table.

Note what sunrise actually is here: the moment the sun's elevation crosses
zero. The shadow engine in session 2 runs exactly the same test, but against
a non-zero horizon angle — the height of the mountains in that direction.
That is the whole idea of this project in one line of code.
"""

from datetime import date

import pandas as pd
import pvlib

# Canmore, Alberta — valley floor
LATITUDE = 51.0894
LONGITUDE = -115.3592
ELEVATION_M = 1309
TIMEZONE = "America/Edmonton"

CANMORE = pvlib.location.Location(
    latitude=LATITUDE,
    longitude=LONGITUDE,
    tz=TIMEZONE,
    altitude=ELEVATION_M,
    name="Canmore",
)


def solar_day(day):
    """Sun position for every minute of `day`, in local time."""
    times = pd.date_range(
        start=f"{day} 00:00",
        end=f"{day} 23:59",
        freq="1min",
        tz=TIMEZONE,
    )
    return CANMORE.get_solarposition(times)


def sun_events(solpos):
    """Sunrise, sunset and the daily high point, from an elevation series."""
    above = solpos["apparent_elevation"] > 0
    previous = above.shift(1, fill_value=False)

    sunrise = solpos.index[above & ~previous]
    sunset = solpos.index[~above & previous]
    peak = solpos["apparent_elevation"].idxmax()

    return sunrise, sunset, peak


if __name__ == "__main__":
    today = date.today()
    solpos = solar_day(today)
    sunrise, sunset, peak = sun_events(solpos)

    print(f"Canmore, Alberta — {today}")
    print(f"  Sunrise       {sunrise[0]:%H:%M}")
    print(f"  Sunset        {sunset[0]:%H:%M}")
    print(f"  Highest sun   {peak:%H:%M}, "
          f"{solpos['apparent_elevation'].max():.1f}° above the horizon")
    print(f"  Bearing then  {solpos.loc[peak, 'azimuth']:.0f}° from north")
```

Run it:

```powershell
python src/sun.py
```

**✓ Check** — you get four lines of output with plausible times.

---

## Step 13 — The validation that matters

**This is the actual point of the session.** Everything before it was plumbing.

1. Go to **[timeanddate.com/sun/canada/canmore](https://www.timeanddate.com/sun/canada/canmore)**
2. Compare today's sunrise and sunset against what your script printed

**They should agree to within a couple of minutes.** Small differences are expected — published tables define sunrise at the moment the sun's *upper edge* appears, while this script uses its *centre*, a gap of a couple of minutes.

**If they are out by exactly one hour, the timezone handling is wrong** — that is the daylight-saving trap in `01-data-sources.md` §D, and it is worth fixing immediately rather than discovering it in session 3.

You have now passed **validation test A2** from `07-validation-without-local-knowledge.md`. Your first independent check, on day one.

**Bonus:** the "highest sun" figure is the solar noon elevation. `02-method-and-assumptions.md` §0 predicts about 62.4° at midsummer and 15.5° at midwinter. Change `today` to `date(2026, 12, 21)` and see whether the model agrees with the document.

---

## Step 14 — Commit and push

```powershell
git add .
git commit -m "Add solar position calculator for Canmore"
git push
```

Note: after the first time, plain `git push` is enough — no `-u origin main`.

**✓ Check** — `src/sun.py` and `requirements.txt` are visible on github.com.

---

## Done

You now have:

- A working Python and Git toolchain
- A private GitHub repository with two commits of real history
- Code that computes solar position for Canmore
- **One independent validation already passed**

**Session 2** builds the shadow engine — and the good news is that it needs no new installs beyond `numpy` and `pytest`, and no downloaded data until the very end.

---

## Friction actually hit on 9 September 2026

Recorded because a first run through is the only chance to catch these.

| What happened | Cause | Resolution |
|---|---|---|
| **Python 3.12 offered only source tarballs** | 3.12 moved to security-fixes-only; 3.12.10 was the last with a Windows installer | Switched to **3.13.15**. Document updated |
| **Git installer skipped all option screens** | Some builds install silently with defaults | Harmless. Editor set afterwards with `git config --global core.editor notepad` |
| **Cursor wasn't installed** | An account on cursor.com had been created, but not the desktop app | Downloaded from cursor.com. Account ≠ application, same as Git ≠ GitHub |
| **Cursor opened as "Cursor Agent"**, no file tree, no icon strip | Cursor's agent surface rather than the editor view | **Unresolved.** Session 1 completed in plain PowerShell instead. Revisit at the start of session 2 — try `Ctrl+Shift+E`, then `Ctrl+Shift+P` → "View: Show Explorer" |
| **`Set-ExecutionPolicy` failed** with "Cannot convert value RemoteSigned,answer" | Prose was pasted along with the command | Run the command alone. The `Y` confirmation is a separate prompt |
| **`git push` — "no upstream branch"** | GitHub repo creation and `git remote add` had been skipped | `git remote add origin <url>` then `git push -u origin main` |
| **`remote: Repository not found`** | Placeholder `YOUR-USERNAME` pasted literally | `git remote set-url origin <real url>` |

**The lesson worth keeping:** none of these were the actual work. Toolchain friction is the tax on session 1 and it is paid once — session 2 needs no new installs, no accounts, and no downloads.

---

## If something goes wrong

**Read the last line of the error first.** It usually says exactly what is wrong. Everything above it is just the route the program took to get there.

| Error | Cause | Fix |
|---|---|---|
| `'python' is not recognized` | PATH checkbox missed in step 1 | Use `py` instead, or re-run the installer |
| Microsoft Store opens | Same | Same |
| `'git' is not recognized` | Git not installed, or terminal opened before install | Step 2, then reopen the terminal |
| `cannot be loaded because running scripts is disabled` | PowerShell execution policy | `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` |
| `ModuleNotFoundError: No module named 'pvlib'` | Virtual environment not active | Look for `(.venv)`. Re-run the activate command |
| `failed to push some refs` / `rejected` | GitHub repo was created with a README | Easiest fix: delete the GitHub repo and recreate it empty |
| `src/sun.py` not found | Wrong folder | `pwd` should show `C:\Claude\Work\Sun-Walks` |

**And paste any error you cannot place into Cursor's chat (`Ctrl+L`) and ask what it means.** Understand it, then fix it — do not guess at fixes. That habit is most of what separates people who find this frustrating from people who find it fast.
