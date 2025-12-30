import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import os
from dotenv import load_dotenv
import threading
import logging

# Set up console logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

class S3ClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AWS S3 Client")
        self.root.geometry("800x600")
        
        self.s3_client = None
        self.current_bucket = None
        self.current_prefix = None
        
        self.setup_ui()
        self.connect_to_s3()
        
        # Load default bucket if specified
        default_bucket = os.getenv('DEFAULT_BUCKET_NAME', '')
        if default_bucket:
            self.bucket_path_var.set(default_bucket)
            # Auto-load the default bucket
            self.load_bucket_path()
    
    def setup_ui(self):
        # Top frame for connection status
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.status_label = ttk.Label(top_frame, text="Status: Not connected", foreground="red")
        self.status_label.pack(side=tk.LEFT)
        
        ttk.Button(top_frame, text="Refresh", command=self.refresh_objects).pack(side=tk.RIGHT, padx=5)
        
        # Bucket and path selection frame
        bucket_frame = ttk.Frame(self.root, padding="10")
        bucket_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(bucket_frame, text="Bucket/Path:").pack(side=tk.LEFT, padx=(0, 5))
        self.bucket_path_var = tk.StringVar()
        self.bucket_path_entry = ttk.Entry(bucket_frame, textvariable=self.bucket_path_var, width=50)
        self.bucket_path_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.bucket_path_entry.bind('<Return>', self.on_bucket_path_change)
        
        ttk.Button(bucket_frame, text="Load", command=self.load_bucket_path).pack(side=tk.LEFT, padx=5)
        
        # Help text
        help_frame = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        help_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        help_text = "Examples: 'my-bucket' or 'my-bucket/documents' or 'my-bucket/images/2024/'"
        ttk.Label(help_frame, text=help_text, foreground="gray").pack(side=tk.LEFT)
        
        # Main container for objects
        main_frame = ttk.LabelFrame(self.root, text="Objects", padding="10")
        main_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10)
        
        # Treeview for objects
        columns = ('Name', 'Size', 'Modified')
        self.object_tree = ttk.Treeview(main_frame, columns=columns, show='tree headings')
        self.object_tree.heading('#0', text='Type')
        self.object_tree.heading('Name', text='Name')
        self.object_tree.heading('Size', text='Size')
        self.object_tree.heading('Modified', text='Last Modified')
        
        self.object_tree.column('#0', width=50)
        self.object_tree.column('Name', width=400)
        self.object_tree.column('Size', width=100)
        self.object_tree.column('Modified', width=150)
        
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.object_tree.yview)
        self.object_tree.configure(yscrollcommand=scrollbar.set)
        
        self.object_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click for folder navigation
        self.object_tree.bind('<Double-1>', self.on_object_double_click)
        
        # Object operations frame
        obj_btn_frame = ttk.Frame(self.root, padding="10")
        obj_btn_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))
        
        ttk.Button(obj_btn_frame, text="Upload File", command=self.upload_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(obj_btn_frame, text="Download File", command=self.download_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(obj_btn_frame, text="Delete File", command=self.delete_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(obj_btn_frame, text="Go Up", command=self.go_up_folder).pack(side=tk.LEFT, padx=5)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(3, weight=1)
    
    def connect_to_s3(self):
        try:
            logger.info("Initializing S3 client...")
            self.s3_client = boto3.client('s3')
            logger.info("S3 client initialized successfully")
            # Skip connection test - we'll validate when accessing specific bucket
            self.status_label.config(text="Status: Ready", foreground="green")
        except NoCredentialsError as e:
            logger.error(f"No AWS credentials found: {e}")
            messagebox.showerror("Error", "AWS credentials not found. Please configure .env file.")
            self.status_label.config(text="Status: No credentials", foreground="red")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            messagebox.showerror("Error", f"Failed to initialize S3 client: {str(e)}")
            self.status_label.config(text="Status: Initialization failed", foreground="red")
    
    def on_bucket_path_change(self, event):
        """Handle Enter key press in bucket/path entry"""
        self.load_bucket_path()
    
    def parse_bucket_path(self, bucket_path):
        """Parse bucket/path string into bucket and prefix"""
        if not bucket_path:
            return None, None
        
        parts = bucket_path.split('/', 1)
        bucket = parts[0]
        prefix = parts[1] if len(parts) > 1 else None
        
        return bucket, prefix
    
    def load_bucket_path(self):
        """Load the specified bucket and path"""
        bucket_path = self.bucket_path_var.get().strip()
        if not bucket_path:
            messagebox.showwarning("Warning", "Please enter a bucket name or bucket/path")
            return
        
        if not self.s3_client:
            messagebox.showerror("Error", "S3 client not initialized")
            return
        
        # Parse bucket and prefix
        bucket, prefix = self.parse_bucket_path(bucket_path)
        if not bucket:
            messagebox.showerror("Error", "Invalid bucket/path format")
            return
        
        logger.info(f"Loading bucket: {bucket}, prefix: {prefix}")
        
        self.current_bucket = bucket
        self.current_prefix = prefix
        
        # Try to load objects
        try:
            self.load_objects()
            if prefix:
                self.status_label.config(text=f"Status: Browsing {bucket}/{prefix}", foreground="green")
            else:
                self.status_label.config(text=f"Status: Browsing {bucket}", foreground="green")
            logger.info(f"Successfully loaded bucket/path: {bucket_path}")
        except Exception as e:
            logger.error(f"Failed to load bucket/path {bucket_path}: {e}")
            self.current_bucket = None
            self.current_prefix = None
            self.status_label.config(text="Status: Ready", foreground="orange")
    
    def load_objects(self):
        if not self.s3_client or not self.current_bucket:
            return
        
        logger.info(f"Loading objects from bucket: {self.current_bucket}, prefix: {self.current_prefix}")
        self.object_tree.delete(*self.object_tree.get_children())
        
        try:
            # List objects with prefix if specified
            kwargs = {'Bucket': self.current_bucket}
            if self.current_prefix:
                kwargs['Prefix'] = self.current_prefix
                if not self.current_prefix.endswith('/'):
                    kwargs['Prefix'] += '/'
            
            logger.info(f"Calling list_objects_v2 with kwargs: {kwargs}")
            response = self.s3_client.list_objects_v2(**kwargs)
            logger.info(f"list_objects_v2 response keys: {list(response.keys())}")
            
            if 'Contents' in response:
                logger.info(f"Found {len(response['Contents'])} objects")
                # Group objects by folders
                folders = set()
                files = []
                
                for obj in response['Contents']:
                    key = obj['Key']
                    logger.debug(f"Processing object: {key}")
                    
                    # Remove current prefix from display
                    display_key = key
                    if self.current_prefix:
                        prefix_with_slash = self.current_prefix if self.current_prefix.endswith('/') else self.current_prefix + '/'
                        if key.startswith(prefix_with_slash):
                            display_key = key[len(prefix_with_slash):]
                    
                    # Check if this is a folder or file
                    if '/' in display_key:
                        folder_name = display_key.split('/')[0]
                        folders.add(folder_name)
                    else:
                        if display_key:  # Don't show empty keys
                            files.append((display_key, obj))
                
                # Add folders first
                for folder in sorted(folders):
                    self.object_tree.insert('', tk.END, text='📁', 
                                          values=(folder + '/', '', ''))
                
                # Add files
                for display_key, obj in files:
                    size = self.format_size(obj['Size'])
                    modified = obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')
                    self.object_tree.insert('', tk.END, text='📄', 
                                          values=(display_key, size, modified))
                
                logger.info(f"Displayed {len(folders)} folders and {len(files)} files")
            else:
                logger.info("No 'Contents' key in response - bucket/path is empty or no matches")
                                          
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"AWS ClientError - Code: {error_code}, Message: {error_message}")
            logger.error(f"Full error response: {e.response}")
            
            if error_code == 'AccessDenied':
                logger.error(f"Access denied for bucket '{self.current_bucket}' - check IAM permissions")
                messagebox.showerror("Permission Error", 
                    f"Access denied when listing objects in bucket '{self.current_bucket}'.\n\n"
                    f"Required permissions for bucket '{self.current_bucket}':\n"
                    f"- s3:ListBucket (to browse contents)\n"
                    f"- s3:GetObject (for downloads)\n"
                    f"- s3:PutObject (for uploads)\n"
                    f"- s3:DeleteObject (for deletions)\n\n"
                    f"AWS Error: {error_message}\n\n"
                    f"You can still upload/download/delete files if you know the exact object keys.")
            elif error_code == 'NoSuchBucket':
                logger.error(f"Bucket '{self.current_bucket}' does not exist")
                messagebox.showerror("Error", f"Bucket '{self.current_bucket}' does not exist or you don't have access to it.")
            else:
                logger.error(f"Unexpected AWS error: {error_code} - {error_message}")
                messagebox.showerror("Error", f"AWS Error ({error_code}): {error_message}")
        except Exception as e:
            logger.error(f"Unexpected error loading objects: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to load objects: {str(e)}")
    
    def on_object_double_click(self, event):
        """Handle double-click on folders to navigate into them"""
        selection = self.object_tree.selection()
        if not selection:
            return
        
        item = self.object_tree.item(selection[0])
        object_name = item['values'][0]
        
        # If it's a folder (ends with /), navigate into it
        if object_name.endswith('/'):
            current_path = self.bucket_path_var.get().strip()
            
            # Build new path
            if self.current_prefix:
                new_prefix = self.current_prefix
                if not new_prefix.endswith('/'):
                    new_prefix += '/'
                new_prefix += object_name
            else:
                new_prefix = object_name
            
            new_path = f"{self.current_bucket}/{new_prefix}"
            self.bucket_path_var.set(new_path)
            self.load_bucket_path()
    
    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
    
    def upload_file(self):
        if not self.current_bucket:
            messagebox.showwarning("Warning", "Please load a bucket/path first")
            return
        
        file_path = filedialog.askopenfilename()
        if not file_path:
            return
        
        file_name = os.path.basename(file_path)
        
        # Construct the S3 key using current prefix
        if self.current_prefix:
            if not self.current_prefix.endswith('/'):
                s3_key = self.current_prefix + '/' + file_name
            else:
                s3_key = self.current_prefix + file_name
        else:
            s3_key = file_name
        
        logger.info(f"Uploading file: {file_path} -> s3://{self.current_bucket}/{s3_key}")
        
        # Ask user to confirm the upload path
        confirm_msg = f"Upload '{file_name}' as:\ns3://{self.current_bucket}/{s3_key}\n\nProceed?"
        if not messagebox.askyesno("Confirm Upload", confirm_msg):
            return
        
        try:
            self.s3_client.upload_file(file_path, self.current_bucket, s3_key)
            logger.info(f"Successfully uploaded: {s3_key}")
            messagebox.showinfo("Success", f"File uploaded as 's3://{self.current_bucket}/{s3_key}'")
            
            # Refresh the current view
            self.load_objects()
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Upload failed - AWS ClientError - Code: {error_code}, Message: {error_message}")
            logger.error(f"Full error response: {e.response}")
            
            if error_code == 'AccessDenied':
                messagebox.showerror("Permission Error", f"Access denied when uploading file. You need 's3:PutObject' permission.\n\nAWS Error: {error_message}")
            else:
                messagebox.showerror("Error", f"AWS Error ({error_code}): {error_message}")
        except Exception as e:
            logger.error(f"Upload failed with unexpected error: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to upload file: {str(e)}")
    
    def download_file(self):
        selection = self.object_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a file")
            return
        
        item = self.object_tree.item(selection[0])
        display_name = item['values'][0]
        
        # Skip folders
        if display_name.endswith('/'):
            messagebox.showwarning("Warning", "Cannot download folders. Please select a file.")
            return
        
        # Reconstruct full S3 key
        if self.current_prefix:
            if not self.current_prefix.endswith('/'):
                object_key = self.current_prefix + '/' + display_name
            else:
                object_key = self.current_prefix + display_name
        else:
            object_key = display_name
        
        logger.info(f"Downloading file: s3://{self.current_bucket}/{object_key}")
        
        save_path = filedialog.asksaveasfilename(initialfile=display_name)
        if not save_path:
            return
        
        try:
            self.s3_client.download_file(self.current_bucket, object_key, save_path)
            logger.info(f"Successfully downloaded to: {save_path}")
            messagebox.showinfo("Success", f"File downloaded to '{save_path}'")
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Download failed - AWS ClientError - Code: {error_code}, Message: {error_message}")
            logger.error(f"Full error response: {e.response}")
            
            if error_code == 'AccessDenied':
                messagebox.showerror("Permission Error", f"Access denied when downloading file. You need 's3:GetObject' permission.\n\nAWS Error: {error_message}")
            elif error_code == 'NoSuchKey':
                messagebox.showerror("Error", f"File '{object_key}' not found in bucket '{self.current_bucket}'.")
            else:
                messagebox.showerror("Error", f"AWS Error ({error_code}): {error_message}")
        except Exception as e:
            logger.error(f"Download failed with unexpected error: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to download file: {str(e)}")
    
    def delete_file(self):
        selection = self.object_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a file")
            return
        
        item = self.object_tree.item(selection[0])
        display_name = item['values'][0]
        
        # Skip folders
        if display_name.endswith('/'):
            messagebox.showwarning("Warning", "Cannot delete folders directly. Delete all files in the folder first.")
            return
        
        # Reconstruct full S3 key
        if self.current_prefix:
            if not self.current_prefix.endswith('/'):
                object_key = self.current_prefix + '/' + display_name
            else:
                object_key = self.current_prefix + display_name
        else:
            object_key = display_name
        
        logger.info(f"Deleting file: s3://{self.current_bucket}/{object_key}")
        
        if messagebox.askyesno("Confirm", f"Delete file 's3://{self.current_bucket}/{object_key}'?"):
            try:
                self.s3_client.delete_object(Bucket=self.current_bucket, Key=object_key)
                logger.info(f"Successfully deleted: {object_key}")
                messagebox.showinfo("Success", f"File 's3://{self.current_bucket}/{object_key}' deleted")
                
                # Refresh the current view
                self.load_objects()
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                logger.error(f"Delete failed - AWS ClientError - Code: {error_code}, Message: {error_message}")
                logger.error(f"Full error response: {e.response}")
                
                if error_code == 'AccessDenied':
                    messagebox.showerror("Permission Error", f"Access denied when deleting file. You need 's3:DeleteObject' permission.\n\nAWS Error: {error_message}")
                else:
                    messagebox.showerror("Error", f"AWS Error ({error_code}): {error_message}")
            except Exception as e:
                logger.error(f"Delete failed with unexpected error: {e}", exc_info=True)
                messagebox.showerror("Error", f"Failed to delete file: {str(e)}")
    
    def go_up_folder(self):
        """Navigate up one folder level"""
        if not self.current_prefix:
            # Already at bucket root
            return
        
        # Remove trailing slash and go up one level
        prefix = self.current_prefix.rstrip('/')
        if '/' in prefix:
            parent_prefix = '/'.join(prefix.split('/')[:-1]) + '/'
            new_path = f"{self.current_bucket}/{parent_prefix}"
        else:
            # Go to bucket root
            new_path = self.current_bucket
        
        self.bucket_path_var.set(new_path)
        self.load_bucket_path()
    
    def refresh_objects(self):
        if self.current_bucket:
            self.load_objects()
        else:
            messagebox.showwarning("Warning", "Please load a bucket/path first")

if __name__ == "__main__":
    root = tk.Tk()
    app = S3ClientGUI(root)
    root.mainloop()