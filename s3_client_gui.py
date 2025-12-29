import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import os
from dotenv import load_dotenv
import threading

load_dotenv()

class S3ClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AWS S3 Client")
        self.root.geometry("800x600")
        
        self.s3_client = None
        self.current_bucket = None
        
        self.setup_ui()
        self.connect_to_s3()
        
        # Load default bucket if specified
        default_bucket = os.getenv('DEFAULT_BUCKET_NAME', '')
        if default_bucket:
            self.bucket_var.set(default_bucket)
            self.current_bucket = default_bucket
            self.load_objects()
    
    def setup_ui(self):
        # Top frame for connection status and bucket input
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.status_label = ttk.Label(top_frame, text="Status: Not connected", foreground="red")
        self.status_label.pack(side=tk.LEFT)
        
        ttk.Button(top_frame, text="Refresh", command=self.refresh_objects).pack(side=tk.RIGHT, padx=5)
        
        # Bucket selection frame
        bucket_frame = ttk.Frame(self.root, padding="10")
        bucket_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(bucket_frame, text="Bucket Name:").pack(side=tk.LEFT, padx=(0, 5))
        self.bucket_var = tk.StringVar()
        self.bucket_entry = ttk.Entry(bucket_frame, textvariable=self.bucket_var, width=30)
        self.bucket_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.bucket_entry.bind('<Return>', self.on_bucket_change)
        
        ttk.Button(bucket_frame, text="Load Bucket", command=self.load_bucket).pack(side=tk.LEFT, padx=5)
        
        # Main container for objects
        main_frame = ttk.LabelFrame(self.root, text="Objects", padding="10")
        main_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10)
        
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
        
        # Object buttons and prefix input
        obj_btn_frame = ttk.Frame(self.root, padding="10")
        obj_btn_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        
        # Prefix input
        ttk.Label(obj_btn_frame, text="Prefix/Folder:").pack(side=tk.LEFT, padx=(0, 5))
        self.prefix_var = tk.StringVar()
        self.prefix_entry = ttk.Entry(obj_btn_frame, textvariable=self.prefix_var, width=20)
        self.prefix_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(obj_btn_frame, text="Upload File", command=self.upload_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(obj_btn_frame, text="Download File", command=self.download_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(obj_btn_frame, text="Delete File", command=self.delete_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(obj_btn_frame, text="Go Up", command=self.go_up_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(obj_btn_frame, text="Clear Prefix", command=self.clear_prefix).pack(side=tk.LEFT, padx=5)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)
    
    def connect_to_s3(self):
        try:
            self.s3_client = boto3.client('s3')
            # Test connection with minimal permissions
            self.s3_client.list_buckets()
            self.status_label.config(text="Status: Connected", foreground="green")
        except NoCredentialsError:
            messagebox.showerror("Error", "AWS credentials not found. Please configure .env file.")
            self.status_label.config(text="Status: No credentials", foreground="red")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                messagebox.showerror("Permission Error", 
                    "Access denied. Your AWS credentials don't have S3 permissions.\n\n"
                    "Required permissions:\n"
                    "- s3:ListBucket\n"
                    "- s3:GetObject\n"
                    "- s3:PutObject\n"
                    "- s3:DeleteObject\n\n"
                    "Please contact your AWS administrator to grant these permissions.")
                self.status_label.config(text="Status: Access denied", foreground="red")
            elif error_code == 'InvalidAccessKeyId':
                messagebox.showerror("Error", "Invalid AWS Access Key ID. Please check your credentials.")
                self.status_label.config(text="Status: Invalid credentials", foreground="red")
            elif error_code == 'SignatureDoesNotMatch':
                messagebox.showerror("Error", "Invalid AWS Secret Access Key. Please check your credentials.")
                self.status_label.config(text="Status: Invalid credentials", foreground="red")
            else:
                messagebox.showerror("Error", f"AWS Error ({error_code}): {e.response['Error']['Message']}")
                self.status_label.config(text="Status: Connection failed", foreground="red")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect: {str(e)}")
            self.status_label.config(text="Status: Connection failed", foreground="red")
    
    def on_bucket_change(self, event):
        """Handle Enter key press in bucket entry"""
        self.load_bucket()
    
    def load_bucket(self):
        """Load the specified bucket"""
        bucket_name = self.bucket_var.get().strip()
        if not bucket_name:
            messagebox.showwarning("Warning", "Please enter a bucket name")
            return
        
        if not self.s3_client:
            messagebox.showerror("Error", "Not connected to AWS S3")
            return
        
        # Test if bucket exists and is accessible
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            self.current_bucket = bucket_name
            self.prefix_var.set('')  # Clear prefix when switching buckets
            self.load_objects()
            messagebox.showinfo("Success", f"Loaded bucket: {bucket_name}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                messagebox.showerror("Error", f"Bucket '{bucket_name}' does not exist")
            elif error_code == 'AccessDenied':
                messagebox.showerror("Permission Error", f"Access denied to bucket '{bucket_name}'. You need 's3:ListBucket' permission.")
            else:
                messagebox.showerror("Error", f"AWS Error ({error_code}): {e.response['Error']['Message']}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to access bucket: {str(e)}")
    
    def load_objects(self):
        if not self.s3_client or not self.current_bucket:
            return
        
        self.object_tree.delete(*self.object_tree.get_children())
        
        try:
            # Get current prefix from entry
            current_prefix = self.prefix_var.get().strip()
            
            # List objects with prefix if specified
            kwargs = {'Bucket': self.current_bucket}
            if current_prefix:
                kwargs['Prefix'] = current_prefix
                if not current_prefix.endswith('/'):
                    kwargs['Prefix'] += '/'
            
            response = self.s3_client.list_objects_v2(**kwargs)
            
            if 'Contents' in response:
                # Group objects by folders
                folders = set()
                files = []
                
                for obj in response['Contents']:
                    key = obj['Key']
                    
                    # Remove current prefix from display
                    display_key = key
                    if current_prefix:
                        prefix_with_slash = current_prefix if current_prefix.endswith('/') else current_prefix + '/'
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
                                          
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                messagebox.showerror("Permission Error", f"Access denied when listing objects in bucket '{self.current_bucket}'. You need 's3:ListBucket' permission.")
            else:
                messagebox.showerror("Error", f"AWS Error ({error_code}): {e.response['Error']['Message']}")
        except Exception as e:
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
            current_prefix = self.prefix_var.get().strip()
            if current_prefix and not current_prefix.endswith('/'):
                current_prefix += '/'
            new_prefix = current_prefix + object_name
            self.prefix_var.set(new_prefix)
            self.load_objects()
    
    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
    
    def upload_file(self):
        if not self.current_bucket:
            messagebox.showwarning("Warning", "Please load a bucket first")
            return
        
        file_path = filedialog.askopenfilename()
        if not file_path:
            return
        
        file_name = os.path.basename(file_path)
        
        # Get prefix from entry
        prefix = self.prefix_var.get().strip()
        
        # Construct the S3 key (object name)
        if prefix:
            # Ensure prefix ends with / if it's meant to be a folder
            if not prefix.endswith('/'):
                prefix += '/'
            s3_key = prefix + file_name
        else:
            s3_key = file_name
        
        # Ask user to confirm the upload path
        confirm_msg = f"Upload '{file_name}' as:\n'{s3_key}'\n\nProceed?"
        if not messagebox.askyesno("Confirm Upload", confirm_msg):
            return
        
        try:
            self.s3_client.upload_file(file_path, self.current_bucket, s3_key)
            messagebox.showinfo("Success", f"File uploaded as '{s3_key}'")
            self.load_objects()
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                messagebox.showerror("Permission Error", "Access denied when uploading file. You need 's3:PutObject' permission.")
            else:
                messagebox.showerror("Error", f"AWS Error ({error_code}): {e.response['Error']['Message']}")
        except Exception as e:
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
        current_prefix = self.prefix_var.get().strip()
        if current_prefix:
            if not current_prefix.endswith('/'):
                current_prefix += '/'
            object_key = current_prefix + display_name
        else:
            object_key = display_name
        
        save_path = filedialog.asksaveasfilename(initialfile=display_name)
        if not save_path:
            return
        
        try:
            self.s3_client.download_file(self.current_bucket, object_key, save_path)
            messagebox.showinfo("Success", f"File downloaded to '{save_path}'")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                messagebox.showerror("Permission Error", "Access denied when downloading file. You need 's3:GetObject' permission.")
            elif error_code == 'NoSuchKey':
                messagebox.showerror("Error", f"File '{object_key}' not found in bucket.")
            else:
                messagebox.showerror("Error", f"AWS Error ({error_code}): {e.response['Error']['Message']}")
        except Exception as e:
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
        current_prefix = self.prefix_var.get().strip()
        if current_prefix:
            if not current_prefix.endswith('/'):
                current_prefix += '/'
            object_key = current_prefix + display_name
        else:
            object_key = display_name
        
        if messagebox.askyesno("Confirm", f"Delete file '{object_key}'?"):
            try:
                self.s3_client.delete_object(Bucket=self.current_bucket, Key=object_key)
                messagebox.showinfo("Success", f"File '{object_key}' deleted")
                self.load_objects()
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'AccessDenied':
                    messagebox.showerror("Permission Error", "Access denied when deleting file. You need 's3:DeleteObject' permission.")
                else:
                    messagebox.showerror("Error", f"AWS Error ({error_code}): {e.response['Error']['Message']}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete file: {str(e)}")
    
    def go_up_folder(self):
        """Navigate up one folder level"""
        current_prefix = self.prefix_var.get().strip()
        if not current_prefix:
            return
        
        # Remove trailing slash
        if current_prefix.endswith('/'):
            current_prefix = current_prefix[:-1]
        
        # Find parent folder
        if '/' in current_prefix:
            parent_prefix = '/'.join(current_prefix.split('/')[:-1]) + '/'
        else:
            parent_prefix = ''
        
        self.prefix_var.set(parent_prefix)
        self.load_objects()
    
    def clear_prefix(self):
        """Clear the prefix to show root level"""
        self.prefix_var.set('')
        self.load_objects()
    
    def refresh_objects(self):
        if self.current_bucket:
            self.load_objects()
        else:
            messagebox.showwarning("Warning", "Please load a bucket first")

if __name__ == "__main__":
    root = tk.Tk()
    app = S3ClientGUI(root)
    root.mainloop()