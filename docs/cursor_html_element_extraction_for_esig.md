# HTML element extraction for esignature form
_Exported on 5/12/2026 at 20:32:10 PDT from Cursor (3.3.30)_

---

**User**

Please extract @Opcenter Execution (4_28_2026 3：06：53 PM).html from this document the whole element with selector #aspnetForm and related to hin styles into new document "esignature-form.html" and preserve how it looks.

---

**Cursor**

Got it. I’ll locate the source HTML, extract the full `#aspnetForm` element, then build a new standalone `esignature-form.html` that keeps the original page’s CSS/asset links needed so the form renders the same.

Next I’ll inspect the source HTML to find the exact `#aspnetForm` block boundaries and what CSS/links the page uses, so the extracted file stays visually identical.

I found **three** `<form id=aspnetForm>` blocks embedded in this SingleFile capture (main page + two embedded frames). Next I’ll inspect each block to identify which one is the actual e-signature UI, then extract that one into `esignature-form.html` with the required CSS/resources.

Now that I’ve located the **e-signature iframe’s** embedded HTML (it’s encoded inside nested `srcdoc` blocks), I’ll extract the `ESigCaptureVP` `#aspnetForm` (lines ~309–398) and rebuild a clean standalone `esignature-form.html` by decoding the embedded HTML and carrying over the head `<style>` blocks that apply to that form.

Got it. Next I’ll programmatically extract the nested iframe `srcdoc` that contains the e-signature page, decode it to real HTML, then pull out the `#aspnetForm` element and all `<style>` blocks from that embedded page into a new standalone `esignature-form.html` that renders the same.

I’ve now identified the exact nesting: the outer SingleFile page contains one iframe `srcdoc` → inside that is the tab iframe `tabfr_...` → inside that is the e-signature iframe `FloatingFrame_frame` whose `srcdoc` contains exactly one `aspnetForm`. Next I’ll generate `esignature-form.html` by extracting all 33 `<style>` blocks plus the `<body>` classes and the full `<form id=\"aspnetForm\">…</form>` from that embedded e-signature document.

I hit a small bug in the helper script: the regex correctly finds `<form ... id=aspnetForm ...>`, but my follow-up `rfind("<form", ...)` was excluding the match start, so it couldn’t re-locate the tag. I’ll fix that to use the match start directly, rerun extraction, then verify the generated `esignature-form.html` contains the full form + all embedded styles.

### Done — extracted `#aspnetForm` into a standalone file

- **Created** `c:\x\bugs\SFLINK-3549, 05.04.26, tricky customization\BSCI-SCREENSHOTS-HTML\esignature-form.html`
- It contains the **full** `<form id="aspnetForm">…</form>` from the embedded e-signature iframe, plus the **embedded styles** (all `<style>` blocks) and the original `<body class="...">` so it should render the same.

### Helper (optional)
- I also added `savefile_extractor.py` in the same folder, which re-generates `esignature-form.html` from the source HTML if you need to rerun it.

---

**User**

Very good, Add read me file on how touse savefile_extractor.py and what exactly it does. Also can I use this script to handle similar files from this folder and can I specify different Ids for different files?

---

**Cursor**

Plan: I’ll (1) read `savefile_extractor.py`, (2) update it to accept command-line args so you can point it at other HTML files and choose a different target `form` id, (3) add a `README.md` explaining what the script does, how to run it, and its limitations/examples.

## README added + script now supports other files/ids

### What I changed
- Added `README.md` in `BSCI-SCREENSHOTS-HTML` with usage + explanation of what the script does.
- Updated `savefile_extractor.py` so you can run it on **other HTML files** and target **different form ids**.

### Can you use it on similar files from this folder?
Yes. Use `--input` (and optionally `--output`):

```powershell
python .\savefile_extractor.py --input "Some Other SingleFile.html" --output "out.html"
```

### Can you specify different ids for different files?
Yes. Use `--form-id`:

```powershell
python .\savefile_extractor.py --input "Some Other SingleFile.html" --output "out.html" --form-id "myFormId"
```

### If the same form id appears multiple times
This is common with SingleFile nesting. The script will **auto-pick the deepest match** and print which iframe-path it selected.  
To force the right one, add `--contains` (example for e-signature):

```powershell
python .\savefile_extractor.py --input "Some Other SingleFile.html" --output "out.html" --form-id "aspnetForm" --contains "ESigCaptureVP.aspx"
```

---

**User**

What is folder __pycache__? Do i need to put it into git?

---

**Cursor**

## What `__pycache__` is
- **`__pycache__`** is a folder Python creates to store **compiled bytecode** files (`.pyc`) for your `.py` files, so future runs start faster.

## Should you commit it to git?
- **No.** It’s machine-/Python-version-specific and is treated as build/cache output.

## What to do
- **Add to `.gitignore`** (if you have one):

```gitignore
__pycache__/
*.py[cod]
```

- If it was already created in your working tree, it’s safe to delete; Python will recreate it when needed.

---

**User**

Got it, now please create .gitignore and package.json so I can initialize repo and put it to github. Also @Opcenter Execution (4_28_2026 3：08：08 PM).html @Opcenter Execution (4_28_2026 3：08：30 PM).html @Opcenter Execution (4_28_2026 3：08：50 PM).html move these files into "tests" folder and update references if required.

---

**Cursor**

Small snag: the first move command failed due to PowerShell quoting/encoding around the timestamps. Next I’ll rerun the move using PowerShell-native quoting (single quotes / `-LiteralPath`) and then verify the files landed under `tests/`.

### Repo setup files added
- **Created** `.gitignore` in `BSCI-SCREENSHOTS-HTML` (ignores Python bytecode/cache, common IDE/OS files, `node_modules`, `.env`).
- **Created** `package.json` in `BSCI-SCREENSHOTS-HTML` with npm scripts:
  - `npm run extract`
  - `npm run extract:help`

### Files moved into `tests/`
Moved these into `BSCI-SCREENSHOTS-HTML\tests\`:
- `Opcenter Execution (4_28_2026 3：08：08 PM).html`
- `Opcenter Execution (4_28_2026 3：08：30 PM).html`
- `Opcenter Execution (4_28_2026 3：08：50 PM).html`

### Reference updates
- I searched the folder for references to those three filenames and **found none**, so **no updates were required**.

