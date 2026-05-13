## `savefile_extractor.py`

### What it does
This script **extracts one `<form>` element (by id)** from a **SingleFile-saved HTML** and writes it into a **standalone HTML file** that preserves the form’s **visual styling**.

Specifically it:
- Walks through **nested** `iframe[srcdoc]` documents (SingleFile embeds pages this way).
- Finds the **first document** that contains `<form id="<your-id>">`.
- Extracts:
  - the document’s opening `<body ...>` tag (to keep theme/body classes)
  - **all inline `<style>...</style>` blocks** from that same document
  - the full `<form ...> ... </form>` HTML for the requested id
- Writes a new HTML file containing only those pieces.

### What it does *not* do
- It does **not** guarantee the extracted form is fully functional (some pages rely on external scripts/services).
- It does **not** download external resources. It only keeps what is already embedded in the SingleFile HTML.

### Requirements
- **Python 3** (uses only the standard library).

### Usage (Windows / PowerShell)
From this folder:

```powershell
python .\savefile_extractor.py
```

By default, it reads:
- `Opcenter Execution (4_28_2026 3：06：53 PM).html`

and writes:
- `esignature-form.html`

### Using it on other similar files in this folder
Yes — point it at a different input file:

```powershell
python .\savefile_extractor.py --input "Another SingleFile Page.html" --output "out.html"
```

### Extracting a different form id
Yes — specify a different form id:

```powershell
python .\savefile_extractor.py --input "Some Page.html" --output "some-form.html" --form-id "myFormId"
```

### When there are multiple matches (common with SingleFile)
Sometimes the same `<form id="...">` appears at multiple nesting levels. The script will **auto-select the deepest match** and print which iframe path it chose.

If you want to force which match is used, add `--contains` with a substring that only appears in the correct embedded page (for e-signature pages, `ESigCaptureVP.aspx` is a good discriminator):

```powershell
python .\savefile_extractor.py --input "Some Page.html" --output "out.html" --form-id "aspnetForm" --contains "ESigCaptureVP.aspx"
```

### Batch example (run on all `.html` files)
This runs the extractor on every `.html` in the current folder and writes `*-extracted.html` outputs:

```powershell
Get-ChildItem -Filter *.html | ForEach-Object {
  $out = Join-Path $_.DirectoryName ($_.BaseName + "-extracted.html")
  python .\savefile_extractor.py --input $_.FullName --output $out --form-id "aspnetForm"
}
```

### Troubleshooting
- **“Could not find `<form id=...>` …”**:
  - Confirm the form id is correct.
  - The form might not be inside `iframe[srcdoc]` in that file.
  - Increase depth: `--max-depth 15`
- **“Found multiple … even after filtering by --contains”**:
  - Pick a more specific `--contains` string.

