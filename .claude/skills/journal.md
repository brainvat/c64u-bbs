---
name: journal
description: Create a new journal entry in docs/journal/. Use when the user asks to journal, log, or write about something — progress, decisions, ideas, anything they want to record.
user_invocable: true
---

# Journal Skill

You are creating a journal entry for the c64u-bbs project. The user will tell you what they want to journal about. Your job is to turn their input into a beautiful, well-written HTML page.

## Step 1: Determine the entry name

Create a short, URL-friendly slug from the user's topic. Use the format `YYYY-MM-DD-slug` (e.g. `2026-04-11-initial-setup`). Use today's date.

## Step 2: Create the entry directory and HTML page

Create `docs/journal/{entry-name}/index.html` with:

- The same C64 retro aesthetic as the rest of the site (blue background, monospace font, C64 color palette)
- A clear title based on the user's topic
- The date prominently displayed
- A well-written summary of whatever the user wanted to journal about — expand on their input, organize it clearly, use sections if appropriate
- A "Back to Journal" link pointing to `../index.html`
- A "Back to Home" link pointing to `../../index.html`

Use this base style (matching the project's existing pages):

```css
:root {
  --c64-blue: #4040e0;
  --c64-light-blue: #7070ff;
  --c64-bg: #4040e0;
  --c64-border: #7070ff;
  --c64-text: #a0a0ff;
  --c64-white: #ffffff;
  --c64-cyan: #70d0d0;
  --c64-green: #50b050;
  --c64-yellow: #d0d050;
}
body {
  background: #1a1a2e;
  color: var(--c64-text);
  font-family: 'Courier New', 'Lucida Console', monospace;
}
```

## Step 3: Update the journal index

Read `docs/journal/index.html`. Replace the content between `<!-- JOURNAL_ENTRIES_START -->` and `<!-- JOURNAL_ENTRIES_END -->` with an updated `<ul class="entries">` list. Each entry should be an `<li>` with:

- A link to `{entry-name}/index.html` with the entry title
- A `.entry-date` div with the date
- A `.entry-summary` div with a 1-2 sentence summary

Order entries with the newest first.

## Step 4: Link from docs/index.html

Read `docs/index.html`. Make sure there is a link to the journal in the Documentation section. If a journal link already exists, leave it. If not, add one:

```html
<li><a href="journal/index.html">Development Journal</a> — Progress notes and project log</li>
```

## Step 5: Stage the files

```bash
git add docs/journal/
```

Tell the user the journal entry has been created and is staged for commit. Show them the path to their new entry.
