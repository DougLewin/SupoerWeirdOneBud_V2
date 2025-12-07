# AWS Credentials Update Guide

## You need to update your AWS credentials for the 'doug-personal' profile

### Step 1: Locate your AWS credentials file
The file is located at: C:\Users\dougl\.aws\credentials

### Step 2: Open the file in a text editor
You can use VS Code, Notepad, or any text editor:
```powershell
code "$env:USERPROFILE\.aws\credentials"
# OR
notepad "$env:USERPROFILE\.aws\credentials"
```

### Step 3: Update or add the [doug-personal] profile
The file should look like this:

```ini
[doug-personal]
aws_access_key_id = YOUR_ACCESS_KEY_ID_HERE
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY_HERE
region = ap-southeast-2
```

### Step 4: Get your AWS credentials
You need to:
1. Log in to AWS Console (https://console.aws.amazon.com/)
2. Go to IAM (Identity and Access Management)
3. Click on "Users" → Your username
4. Go to "Security credentials" tab
5. Under "Access keys", either:
   - Use an existing active access key
   - Create a new access key (click "Create access key")
   
⚠️ **IMPORTANT**: Copy both the Access Key ID and Secret Access Key when created
   (you can't view the secret key again after creation)

### Step 5: Update the credentials file
Replace the values in your credentials file with:
- aws_access_key_id = [the Access Key ID from AWS]
- aws_secret_access_key = [the Secret Access Key from AWS]

### Step 6: Save the file

### Step 7: Test the credentials
After saving, run this command to test:
```powershell
aws s3 ls s3://superweirdonebud/ --profile doug-personal
```

If it works, you should see the Rotto_Tracker.csv file listed!

---

## Alternative: Remove Invalid Environment Variables

If you have old AWS environment variables set, they might be interfering.
Check with:
```powershell
$env:AWS_ACCESS_KEY_ID
$env:AWS_SECRET_ACCESS_KEY
```

If they show old/invalid values, unset them for this session:
```powershell
Remove-Item Env:\AWS_ACCESS_KEY_ID -ErrorAction SilentlyContinue
Remove-Item Env:\AWS_SECRET_ACCESS_KEY -ErrorAction SilentlyContinue
Remove-Item Env:\AWS_DEFAULT_REGION -ErrorAction SilentlyContinue
```

---

Once you've updated the credentials, come back and we'll test the app!
