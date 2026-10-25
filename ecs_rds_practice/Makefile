AWS_REGION   ?= ap-southeast-2
AWS_PROFILE  ?= personal
ACCOUNT_ID   ?= 561598984108
ECR_REPO     ?= f8-cloud-fastapi-btvn
IMAGE_NAME   ?= fastapi-ecs-rds

# Version ngữ nghĩa (Semantic Versioning) dễ nhớ, ví dụ: v1.0.0, v1.0.1, v1.1.0
# Bạn có thể sửa số ở dòng này, hoặc truyền khi chạy: make push-prod VERSION=v1.0.2
VERSION      ?= v1.0.1
ECR_URI      := $(ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(ECR_REPO)

.PHONY: help tunnel dev dev-logs dev-down build-prod push-prod

help:
	@echo "Danh sách các lệnh hỗ trợ trong dự án:"
	@echo "  make tunnel                     - Mở đường hầm SSM port forwarding kết nối RDS từ máy local (cổng 5433)"
	@echo "  make dev                        - Chạy ứng dụng local bằng Docker Compose (hot-reload)"
	@echo "  make dev-logs                   - Xem logs container app đang chạy ở local"
	@echo "  make dev-down                   - Dừng toàn bộ container local"
	@echo "  make build-prod                 - Build Docker image (mặc định tag: $(VERSION))"
	@echo "  make build-prod VERSION=v1.0.2  - Build Docker image với version tùy chọn"
	@echo "  make push-prod                  - Build và Push image lên AWS ECR (tag: $(VERSION))"
	@echo "  make push-prod VERSION=v1.0.2   - Build và Push image với version tùy chọn"

tunnel:
	@./tunnel-db.sh

dev:
	docker compose up -d app

dev-logs:
	docker compose logs -f app

dev-down:
	docker compose down

build-prod:
	@echo "🔨 Đang build image với tag: $(VERSION)..."
	docker build -f Dockerfile.prod -t $(IMAGE_NAME):$(VERSION) .

push-prod: build-prod
	@echo "🚀 Đang push image lên ECR: $(ECR_URI):$(VERSION)..."
	aws ecr get-login-password --region $(AWS_REGION) --profile $(AWS_PROFILE) | docker login --username AWS --password-stdin $(ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
	docker tag $(IMAGE_NAME):$(VERSION) $(ECR_URI):$(VERSION)
	docker push $(ECR_URI):$(VERSION)
	@echo "✅ Push thành công: $(ECR_URI):$(VERSION)"
