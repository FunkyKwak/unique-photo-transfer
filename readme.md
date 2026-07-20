# Unique Photo Transfer

![Status](https://img.shields.io/badge/status-in%20development-orange)

**Unique Photo Transfer** is a lightweight desktop application designed to safely copy photos and videos from one folder to another while avoiding duplicates.

The goal is to provide a simple and reliable tool for migrating, consolidating or backing up large photo libraries.

## Features

### Duplicate detection

Unlike a simple copy operation, Unique Photo Transfer identifies already existing files using metadata comparison:

- File name
- File size
- Last modification date

Files matching these criteria are considered already present and are skipped.

No file content hashing is performed by default, avoiding unnecessary reads of several terabytes of data.

### Large library support

Designed for large photo collections:

- Multiple terabytes of data
- Thousands of subdirectories
- Hundreds of thousands of files
- Single-pass directory indexing for performance

The destination folder is indexed once, then source files are checked against this index.

### Desktop application

The application provides a graphical interface:

- Select source folder
- Select destination folder
- Start / cancel transfer
- Progress indicator
- Transfer statistics
- Error reporting

No command line required.

## Use cases

Examples:

- Merge several photo backups into one library
- Import photos from external drives
- Consolidate camera and smartphone folders
- Prepare a photo archive migration
- Avoid duplicate files when restoring backups

## How it works

The application performs the following steps:

1. Scan the destination folder recursively.
2. Build an in-memory index of existing files.
3. Scan the source folder recursively.
4. Compare each file against the destination index.
5. Copy only missing files.

The comparison key is:
(filename, size, modification date)



## Performance considerations

The application is designed to minimize disk access:

- No full file hashing
- No repeated scans of the destination
- Metadata-based comparison
- Sequential directory traversal

The bottleneck is expected to be storage performance rather than CPU usage.

## Installation

### Download

Download the latest release from the GitHub Releases page:
https://github.com/FunkyKwak/unique-photo-transfer/releases




The application runs as a standalone Windows executable.

Python installation is not required.

### Build from source

Requirements:

- Python 3.12+
- pip

Install dependencies:

```bash
pip install -r requirements.txt
```



 Run the application:
```bash
python main.py
```

The generated executable will be available in:
```
dist/
```
