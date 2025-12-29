# AWS S3 Permissions Guide

## Required IAM Permissions

Your AWS user/role needs the following S3 permissions for the application to work with a specific bucket:

### Minimal Policy for Specific Bucket (JSON)
Replace `YOUR-BUCKET-NAME` with your actual bucket name:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
        }
    ]
}
```

### Example for bucket named "my-app-files":
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::my-app-files"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::my-app-files/*"
        }
    ]
}
```

## Permission Breakdown

- **s3:ListBucket** on bucket resource: Required to list objects in the bucket
- **s3:GetObject** on bucket objects: Required to download files
- **s3:PutObject** on bucket objects: Required to upload files
- **s3:DeleteObject** on bucket objects: Required to delete files

## How to Apply Permissions

### Option 1: AWS Console (Web Interface)
1. Go to AWS IAM Console
2. Find your user under "Users"
3. Click "Add permissions" → "Create inline policy"
4. Use the JSON editor and paste the policy above
5. Replace `YOUR-BUCKET-NAME` with your actual bucket name
6. Name the policy (e.g., "S3BucketAccess") and save

### Option 2: AWS CLI
```bash
# Save the policy to a file (replace YOUR-BUCKET-NAME first)
cat > s3-bucket-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["s3:ListBucket"],
            "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME"
        },
        {
            "Effect": "Allow",
            "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
            "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
        }
    ]
}
EOF

# Create and attach the policy (replace YOUR_USERNAME and YOUR_ACCOUNT_ID)
aws iam create-policy --policy-name S3BucketAccess --policy-document file://s3-bucket-policy.json
aws iam attach-user-policy --user-name YOUR_USERNAME --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/S3BucketAccess
```

## Testing Permissions
You can test your permissions using AWS CLI:
```bash
# Test list bucket (should work)
aws s3 ls s3://YOUR-BUCKET-NAME/

# Test upload (should work)
echo "test" > test.txt
aws s3 cp test.txt s3://YOUR-BUCKET-NAME/

# Test download (should work)
aws s3 cp s3://YOUR-BUCKET-NAME/test.txt downloaded.txt

# Test delete (should work)
aws s3 rm s3://YOUR-BUCKET-NAME/test.txt
```

## Common Permission Errors

- **AccessDenied on ListBucket**: Missing `s3:ListBucket` permission on bucket resource
- **AccessDenied on GetObject**: Missing `s3:GetObject` permission on bucket objects (`bucket-name/*`)
- **AccessDenied on PutObject**: Missing `s3:PutObject` permission on bucket objects
- **AccessDenied on DeleteObject**: Missing `s3:DeleteObject` permission on bucket objects
- **NoSuchBucket**: Bucket doesn't exist or you don't have any permissions to it

## Security Best Practices

1. **Bucket-Specific Permissions**: Only grant access to the specific bucket you need
2. **Principle of Least Privilege**: Only grant the permissions you actually use
3. **Use IAM Roles**: For EC2 instances, use IAM roles instead of access keys
4. **Rotate Keys**: Regularly rotate your access keys
5. **Monitor Usage**: Use CloudTrail to monitor S3 API calls

## No Global S3 Permissions Needed

This application is designed to work without these broader permissions:
- ❌ `s3:ListAllMyBuckets` - Not needed since you specify the bucket name
- ❌ `s3:CreateBucket` - Not needed since bucket management is removed
- ❌ `s3:DeleteBucket` - Not needed since bucket management is removed