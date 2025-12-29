# AWS S3 Permissions Guide

## Required IAM Permissions

Your AWS user/role needs the following S3 permissions for the application to work:

### Minimal Policy (JSON)
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListAllMyBuckets"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:GetBucketLocation"
            ],
            "Resource": "arn:aws:s3:::*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::*/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:CreateBucket",
                "s3:DeleteBucket"
            ],
            "Resource": "arn:aws:s3:::*"
        }
    ]
}
```

### Alternative: Use AWS Managed Policy
Instead of creating a custom policy, you can attach the AWS managed policy:
- `AmazonS3FullAccess` (gives full S3 access)

## How to Apply Permissions

### Option 1: AWS Console (Web Interface)
1. Go to AWS IAM Console
2. Find your user under "Users"
3. Click "Add permissions" → "Attach policies directly"
4. Search for "AmazonS3FullAccess" and attach it
5. Or create a custom policy with the JSON above

### Option 2: AWS CLI
```bash
# Create the policy file
aws iam create-policy --policy-name S3ClientPolicy --policy-document file://s3-policy.json

# Attach to user (replace YOUR_USERNAME)
aws iam attach-user-policy --user-name YOUR_USERNAME --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/S3ClientPolicy
```

### Option 3: Programmatic User
If you're using programmatic access keys:
1. Go to IAM → Users → Your User
2. Click "Add permissions"
3. Choose "Attach policies directly"
4. Select "AmazonS3FullAccess" or create custom policy

## Testing Permissions
You can test your permissions using AWS CLI:
```bash
# Test list buckets
aws s3 ls

# Test bucket operations
aws s3 mb s3://test-bucket-name-12345
aws s3 rb s3://test-bucket-name-12345
```

## Common Permission Errors

- **AccessDenied on ListBuckets**: Missing `s3:ListAllMyBuckets`
- **AccessDenied on CreateBucket**: Missing `s3:CreateBucket`
- **AccessDenied on file operations**: Missing `s3:GetObject`, `s3:PutObject`, or `s3:DeleteObject`

## Security Best Practices

1. **Principle of Least Privilege**: Only grant permissions you actually need
2. **Use IAM Roles**: For EC2 instances, use IAM roles instead of access keys
3. **Rotate Keys**: Regularly rotate your access keys
4. **Restrict Resources**: Limit permissions to specific buckets if possible:
   ```json
   "Resource": "arn:aws:s3:::my-specific-bucket/*"
   ```