#!/usr/bin/env bash
set -e

INSTANCE_ID="${BASTION_INSTANCE_ID:-i-0d227015bed325473}"
RDS_ENDPOINT="${RDS_ENDPOINT:-fastapi-btvn-postgres.c7wmcm2ca5dg.ap-southeast-2.rds.amazonaws.com}"
REMOTE_PORT="5432"
LOCAL_PORT="5433"
REGION="ap-southeast-2"
PROFILE="personal"

echo "========================================================="
echo "🚀 ĐANG MỞ ĐƯỜNG HẦM AWS SSM PORT FORWARDING VÀO RDS"
echo "========================================================="
echo "📌 Local Port  : localhost:${LOCAL_PORT}"
echo "📌 Remote Host : ${RDS_ENDPOINT}:${REMOTE_PORT}"
echo "📌 Bastion EC2 : ${INSTANCE_ID}"
echo "---------------------------------------------------------"
echo "👉 Thông tin kết nối DBeaver / TablePlus / Navicat:"
echo "   - Host     : localhost (hoặc 127.0.0.1)"
echo "   - Port     : ${LOCAL_PORT}"
echo "   - Database : app_notes_db"
echo "   - User     : postgres"
echo "   - Password : (mật khẩu bạn đã đặt)"
echo "---------------------------------------------------------"
echo "💡 Nhấn Ctrl + C để đóng đường hầm khi không dùng nữa."
echo "========================================================="

aws ssm start-session \
  --target "${INSTANCE_ID}" \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters "{\"host\":[\"${RDS_ENDPOINT}\"],\"portNumber\":[\"${REMOTE_PORT}\"],\"localPortNumber\":[\"${LOCAL_PORT}\"]}" \
  --region "${REGION}" \
  --profile "${PROFILE}"
