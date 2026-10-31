#!/bin/bash
set -e

PROFILE="personal"
REGION="ap-southeast-2"
FUNCTION_NAME="user_service"

echo "Đóng gói mã nguồn thành lambda.zip..."
rm -f lambda.zip
zip -r lambda.zip lambda_function.py models repositories

echo "Cập nhật mã nguồn lên AWS Lambda ($FUNCTION_NAME)..."
aws lambda update-function-code \
  --function-name "$FUNCTION_NAME" \
  --zip-file fileb://lambda.zip \
  --region "$REGION" \
  --profile "$PROFILE"

echo "Chờ Lambda function cập nhật hoàn tất..."
aws lambda wait function-updated-v2 \
  --function-name "$FUNCTION_NAME" \
  --region "$REGION" \
  --profile "$PROFILE"

echo "Triển khai thành công!"
