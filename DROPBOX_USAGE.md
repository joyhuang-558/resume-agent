# Dropbox Folder

`dropbox/` is a **local folder** for drag-and-drop file ingestion. It is not the cloud service Dropbox.

---

## How to Use

### Option 1: Monitor mode (auto-ingest)

```bash
python main.py monitor
```

Drop PDF or TXT files into `dropbox/` — they are detected and ingested automatically.

### Option 2: Interactive mode (manual)

```bash
python main.py interactive
```

Then:

```
> file dropbox/resume.pdf
> file dropbox/document.txt
```

### Option 3: Batch upload

```bash
python batch_upload.py dropbox/
```

Processes all PDF files in the folder.

---

## Supported Formats

- `.pdf` — PDF files
- `.txt` — Text files

---

## Adding Files

**Copy or drag** files into `dropbox/`:

```bash
cp /path/to/resume.pdf dropbox/
```

Or use Finder / File Explorer to copy or drag files into the folder.

---

## Notes

- The folder is created automatically if it does not exist.
- Monitor mode watches only the root of `dropbox/`; subfolders are not watched.
- File size: keep under ~10MB for best performance.
