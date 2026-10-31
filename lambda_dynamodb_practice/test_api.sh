#!/bin/bash
set -e

API_URL="https://qgfiqxspse.execute-api.ap-southeast-2.amazonaws.com"

echo "=========================================="
echo "0. GET / (API Info & Service Status)"
echo "=========================================="
curl -s "${API_URL}/" | jq .

echo -e "\n=========================================="
echo "1. GET /users (Lấy danh sách tất cả users)"
echo "=========================================="
curl -s "${API_URL}/users" | jq .

echo -e "\n=========================================="
echo "2. GET /users/u1 (Lấy chi tiết user u1)"
echo "=========================================="
curl -s "${API_URL}/users/u1" | jq .

echo -e "\n=========================================="
echo "3. GET /orders (Lấy toàn bộ đơn hàng trong hệ thống)"
echo "=========================================="
curl -s "${API_URL}/orders" | jq .

echo -e "\n=========================================="
echo "4. GET /users/u1/orders (Lấy toàn bộ đơn hàng của user u1)"
echo "=========================================="
curl -s "${API_URL}/users/u1/orders" | jq .

echo -e "\n=========================================="
echo "5. POST /orders (Tạo đơn hàng mới)"
echo "=========================================="
curl -s -X POST "${API_URL}/orders" \
  -H "Content-Type: application/json" \
  -d '{"userId": "u3", "orderId": "2026-10-31#005", "total": 750000, "status": "pending"}' | jq .

echo -e "\n=========================================="
echo "6. DELETE /orders/u3/2026-10-31#005 (Dọn dẹp đơn hàng mẫu)"
echo "=========================================="
curl -s -X DELETE "${API_URL}/orders/u3/2026-10-31%23005" | jq .

echo -e "\n=========================================="
echo "TẤT CẢ KIỂM THỬ THÀNH CÔNG!"
echo "=========================================="
