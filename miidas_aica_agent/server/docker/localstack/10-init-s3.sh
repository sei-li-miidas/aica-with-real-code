#!/usr/bin/env sh

set -e
export AWS_ACCESS_KEY_ID=dummy
export AWS_SECRET_ACCESS_KEY=dummy
export AWS_DEFAULT_REGION=ap-northeast-1

BUCKETS="local-miidas-app"
for b in $BUCKETS; do
  echo "Creating bucket: $b"
  if [ "$AWS_DEFAULT_REGION" = "us-east-1" ]; then
    awslocal s3api create-bucket --bucket "$b" >/dev/null 2>&1 || true
  else
    awslocal s3api create-bucket --bucket "$b" --create-bucket-configuration LocationConstraint="$AWS_DEFAULT_REGION" >/dev/null 2>&1 || true
  fi

  awslocal s3api put-bucket-cors --bucket "$b" --cors-configuration '{
      "CORSRules": [
          {
              "AllowedHeaders": ["*"],
              "AllowedMethods": ["GET", "PUT", "POST"],
              "AllowedOrigins": ["*"],
              "ExposeHeaders": [],
              "MaxAgeSeconds": 3000
          }
      ]
  }'

  echo "Configuring website hosting for bucket: $b"
  awslocal s3api put-bucket-website --bucket "$b" --website-configuration '{
    "IndexDocument": {"Suffix": "index.html"},
    "ErrorDocument": {"Key": "error.html"}
  }' || true

  echo "Applying public-read bucket policy for: $b"
  awslocal s3api put-bucket-policy --bucket "$b" --policy '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "PublicReadGetObject",
        "Effect": "Allow",
        "Principal": "*",
        "Action": ["s3:GetObject"],
        "Resource": ["arn:aws:s3:::'"$b"'/*"]
      }
    ]
  }' || true

  if ! awslocal s3 ls "s3://$b/index.html" >/dev/null 2>&1; then
    echo "<html><body><h1>$b index</h1></body></html>" > /tmp/index.html
    awslocal s3 cp /tmp/index.html "s3://$b/index.html"
    rm /tmp/index.html
  fi
  if ! awslocal s3 ls "s3://$b/error.html" >/dev/null 2>&1; then
    echo "<html><body><h1>Error</h1></body></html>" > /tmp/error.html
    awslocal s3 cp /tmp/error.html "s3://$b/error.html"
    rm /tmp/error.html
  fi
  if ! awslocal s3 ls "s3://$b/api/v1/maintenance/aica.json" >/dev/null 2>&1; then
    echo '{"isMaintenance": false}' > /tmp/aica.json
    awslocal s3 cp /tmp/aica.json "s3://$b/api/v1/maintenance/aica.json"
    rm /tmp/aica.json
  fi
done

awslocal s3api list-buckets || true
