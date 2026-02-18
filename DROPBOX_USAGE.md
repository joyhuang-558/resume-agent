# Dropbox Folder — Usage Guide

## 📁 What is the Dropbox folder?

`dropbox/` is a **local folder** used to simulate a drag-and-drop UI. It is not the cloud service Dropbox—just a regular folder in the project.

**Location:** `./dropbox/` (under the project root)

## 📤 How to add files to the Dropbox folder

### Method 1: Copy files manually (simplest)

#### macOS/Linux:
```bash
# Copy files into the dropbox folder
cp /path/to/your/resume.pdf dropbox/
cp /path/to/your/document.txt dropbox/
```

#### Windows:
```cmd
copy C:\path\to\your\resume.pdf dropbox\
copy C:\path\to\your\document.txt dropbox\
```

#### Using a file manager:
1. Open your file manager (Finder / File Explorer)
2. Locate your PDF or TXT file
3. Copy the file (Cmd+C / Ctrl+C)
4. Navigate to the `dropbox/` folder under the project directory
5. Paste the file (Cmd+V / Ctrl+V)

### Method 2: Create test files from the command line

```bash
# Create a test resume file
cat > dropbox/test_resume.txt << 'EOF'
John Smith
Email: john.smith@email.com
Phone: (555) 123-4567

Education:
- Bachelor's in Computer Science, MIT, 2020

Experience:
- Software Engineer at Tech Corp (2020-2023)
  - Developed Python applications
  - Worked with machine learning models

Skills:
- Python, Machine Learning, Data Science
EOF
```

### Method 3: Drag and drop (macOS)

1. Open Finder
2. Locate your PDF or TXT file
3. Open the project directory and find the `dropbox/` folder
4. Drag the file into the `dropbox/` folder

## 🚀 How to use files in the Dropbox folder

### Option 1: Interactive mode — specify files manually

```bash
python main.py interactive
```

Then enter:
```
> file dropbox/your_resume.pdf
> file dropbox/document.txt
```

### Option 2: Monitor mode — auto watch (recommended)

```bash
# Start monitor mode
python main.py monitor
```

Then add files to the `dropbox/` folder; the program will **detect and ingest them automatically**.

**Workflow:**
1. Run `python main.py monitor`
2. Copy PDF or TXT files into the `dropbox/` folder
3. The program detects new files
4. It calls the `insert_file` tool automatically
5. Files are inserted into the knowledge base

### Option 3: Let the agent handle it (via conversation)

```bash
python main.py interactive
```

Then tell the agent:
```
> Add dropbox/resume.pdf to the knowledge base
> Process all files in the dropbox folder
```

The agent will call the `insert_file` tool for you.

### Option 4: Batch upload script

```bash
# After putting multiple files in the dropbox folder
python batch_upload.py dropbox/
```

This processes all PDF and TXT files in the dropbox folder in batch.

## 📋 Supported file types

- ✅ `.pdf` — PDF files
- ✅ `.txt` — Text files
- ❌ Other formats (not supported)

## 🎯 Full usage examples

### Example 1: Manual file insert

```bash
# 1. Put file in dropbox
cp my_resume.pdf dropbox/

# 2. Start interactive mode
python main.py interactive

# 3. Insert file
> file dropbox/my_resume.pdf

# 4. Query
> What is in my resume?
```

### Example 2: Auto monitor mode

```bash
# Terminal 1: Start monitor
python main.py monitor

# Terminal 2: Add files (program will process them)
cp resume1.pdf dropbox/
cp resume2.txt dropbox/
cp resume3.pdf dropbox/

# All files are inserted into the knowledge base automatically!
```

### Example 3: Agent handles the file

```bash
python main.py interactive

# Ask the agent to process the file
> Add dropbox/resume.pdf to the knowledge base

# The agent will:
# 1. Recognize this as a file-insert request
# 2. Call the insert_file tool
# 3. Insert the file into the knowledge base
# 4. Return a success message
```

## 🔍 Inspecting the Dropbox folder

```bash
# List contents of the dropbox folder
ls -la dropbox/

# Count files
ls dropbox/*.pdf dropbox/*.txt 2>/dev/null | wc -l
```

## 💡 Tips

1. **File paths:** You can use a relative path like `dropbox/file.pdf` or an absolute path.
2. **Auto-creation:** If the `dropbox/` folder does not exist, the program will create it.
3. **Monitor mode:** Best for processing many files in batch.
4. **File size:** Keep files reasonably small (e.g. &lt; 10MB).
5. **Naming:** Use meaningful names, e.g. `john_doe_resume.pdf`.

## 🐛 FAQ

### Q: Files in dropbox are not processed automatically?
**A:** Make sure you are running `python main.py monitor`.

### Q: Which file formats are supported?
**A:** Only `.pdf` and `.txt` are supported.

### Q: Can I put files in subfolders?
**A:** Monitor mode watches only the root of `dropbox/`; subfolders are not watched.

### Q: How do I remove files after they are processed?
**A:** You can delete them manually. The program tracks processed files to avoid re-ingesting them.
