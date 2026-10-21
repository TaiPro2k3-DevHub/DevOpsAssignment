# 1. Nén code và thư mục node_modules vừa tạo
zip -r deploy.zip index.mjs package.json node_modules

# 2. Đẩy lên AWS Lambda
aws lambda update-function-code \
  --region us-east-1 \
  --function-name expressjs-example-f8 \
  --zip-file fileb://deploy.zip