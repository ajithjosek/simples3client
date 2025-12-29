# AWS S3 Client GUI

A simple desktop application for managing AWS S3 objects with a graphical user interface.

## Features

- Connect to a specific S3 bucket by name
- View objects in buckets with folder navigation
- Upload files to S3 with prefix/folder support
- Download files from S3
- Delete objects from S3
- Navigate folder structures with double-click

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure AWS credentials:
   - Copy `.env.example` to `.env`
   - Add your AWS credentials and default bucket:
```
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-1
DEFAULT_BUCKET_NAME=my-bucket-name
```

Alternatively, you can use AWS CLI configuration or IAM roles.

## Usage

Run the application:
```bash
python s3_client_gui.py
```

## Operations

- **Bucket**: Enter a bucket name and click "Load Bucket" or press Enter
- **Default Bucket**: Set `DEFAULT_BUCKET_NAME` in .env to auto-load a bucket on startup
- **Upload**: Enter a prefix/folder path, then click "Upload File" to select and upload
- **Download**: Select a file and click "Download File" to save it locally
- **Delete**: Select a file and click "Delete File"
- **Navigation**: Double-click folders to enter them, use "Go Up" or "Clear Prefix" to navigate
- **Refresh**: Click "Refresh" to reload the current bucket contents

## Folder/Prefix Usage

- Enter `documents/` in the prefix field before uploading to create folder structure
- Double-click folders in the file list to navigate into them
- Use "Go Up" to move up one folder level
- Use "Clear Prefix" to return to bucket root

## Requirements

- Python 3.7+
- AWS account with S3 access
- Valid AWS credentials with bucket permissions
