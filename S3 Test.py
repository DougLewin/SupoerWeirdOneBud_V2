import boto3

s3 = boto3.Session(profile_name='doug-personal').client('s3', region_name='ap-southeast-2')
for obj in s3.list_objects_v2(Bucket='superweirdonebud').get('Contents', []):
    print(obj['Key'])
