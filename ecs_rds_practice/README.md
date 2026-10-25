# Hướng dẫn Deploy FastAPI + AWS RDS PostgreSQL lên AWS ECS (Fargate)

Dự án này sử dụng:
- **FastAPI** + **SQLAlchemy** + **psycopg2**
- Quản lý gói bằng **Astral `uv` hoàn toàn bên trong Docker** (không cần cài `uv` hay Python ở máy local)
- Cấu trúc thư mục chuẩn **`src/app`**
- **Docker Compose** cho môi trường phát triển (Hot-reload)
- **Dockerfile.prod** cho môi trường Production (Multi-stage build tối ưu nhẹ ~77MB để deploy lên ECS)

---

## 1. Cấu trúc thư mục

```
ecs_rds_practice/
├── Dockerfile          # Môi trường dev (chứa uv để dev & cài thư viện)
├── Dockerfile.prod     # Môi trường production (multi-stage build siêu nhẹ cho ECS)
├── docker-compose.yml  # Dùng để chạy dev & chạy lệnh uv qua container
├── pyproject.toml      # Khai báo dependency quản lý bởi uv
├── uv.lock             # Lockfile quản lý bởi uv
├── .dockerignore
├── .env.example
└── src/
    └── app/
        ├── __init__.py
        ├── database.py # Cấu hình kết nối DB & retry logic
        ├── models.py   # SQLAlchemy Model (bảng items)
        ├── schemas.py  # Pydantic Schemas
        └── main.py     # FastAPI app & giao diện demo
```

---

## 2. Cách dùng `uv` qua Docker (Không cài uv trên máy host)

### Thêm một thư viện mới:
```bash
docker compose run --rm app uv add <ten_thu_vien>
```

### Khóa phiên bản / Cập nhật lockfile:
```bash
docker compose run --rm app uv lock
```

### Chạy ứng dụng local (Dev mode có hot-reload):
```bash
docker compose up -d app
# Xem logs kiểm tra kết nối DB
docker compose logs -f app
# Tắt
docker compose down
```

---

## 3. Cơ chế kết nối Database ở Local vs trên AWS

### Ở môi trường Local (Kết nối vào DB của compose khác):
- Khi PostgreSQL đang chạy trong một Docker container khác (ví dụ container `db-1` có mở port `5432:5432` ra host):
  - Container app kết nối qua **`host.docker.internal:5432`** (tính năng của Docker Desktop để gọi ngược về máy host).
  - Phải dùng đúng thông tin xác thực của container DB đó (ví dụ container `db-1` trên máy bạn dùng `DB_USER=local`, `DB_PASSWORD=local`, `DB_NAME=db_local`).
  - Trong `docker-compose.yml`, các biến này đã được cấu hình sẵn fallback:
    ```yaml
    environment:
      - DB_HOST=${DB_HOST:-host.docker.internal}
      - DB_PORT=${DB_PORT:-5432}
      - DB_USER=${DB_USER:-local}
      - DB_PASSWORD=${DB_PASSWORD:-local}
      - DB_NAME=${DB_NAME:-db_local}
    ```

### Ở môi trường AWS (ECS Task ⇄ RDS):
- **Không dùng `host.docker.internal`** vì ECS và RDS chạy trên hạ tầng đám mây của AWS.
- **`DB_HOST`:** Thay bằng **RDS Endpoint** do AWS cấp (ví dụ: `demo-postgres.c123456.ap-southeast-1.rds.amazonaws.com`).
- **`DB_USER` / `DB_PASSWORD` / `DB_NAME`:** Là thông tin bạn đặt khi tạo database trên RDS Console.
- **Tường lửa (Security Group):** Security Group của RDS phải cho phép Inbound cổng `5432` từ chính Security Group của ECS Task.

## 4. Kiến trúc dự án (Architecture Diagram)

> **Mẹo:** Bạn có thể chụp lại sơ đồ này để nộp theo yêu cầu "kiến trúc dự án (chụp ảnh)":

```
               [Client / Trình duyệt]
                         │
                         ▼ HTTP (Port 8000)
             [Internet Gateway (VPC)]
                         │
        ┌────────────────┴──────────────────────────────────┐
        │ AWS VPC (Default VPC: 172.31.0.0/16)              │
        │                                                   │
        │   [Public Subnet]                                 │
        │   ┌───────────────────────────────────────────┐   │
        │   │ ECS Task (Fargate Container)              │   │
        │   │ - Public IP: Có thể truy cập từ Internet  │   │
        │   │ - Security Group: ecs-task-sg             │   │
        │   │   (Inbound: Allow Port 8000 from 0.0.0.0) │   │
        │   └─────────────────────┬─────────────────────┘   │
        │                         │                         │
        │                         │ Port 5432 (Internal)    │
        │                         ▼                         │
        │   [DB Subnet]                                     │
        │   ┌───────────────────────────────────────────┐   │
        │   │ AWS RDS (PostgreSQL Instance)             │   │
        │   │ - Security Group: rds-db-sg               │   │
        │   │   (Inbound: Allow Port 5432 từ            │   │
        │   │    Source = 'ecs-task-sg')                │   │
        │   │ - Endpoint: xxx.rds.amazonaws.com         │   │
        │   └───────────────────────────────────────────┘   │
        └───────────────────────────────────────────────────┘
```

---

## 5. Hướng dẫn từng bước làm bài tập và nộp bài

### Bước 1: Build & Push Image lên AWS ECR
1. Mở AWS Console, tìm dịch vụ **ECR** (Elastic Container Registry).
2. Bấm **Create repository**, đặt tên là `fastapi-ecs-rds`.
3. Nhấn nút **View push commands** ở góc phải trên.
4. Chạy lệnh đăng nhập và build (sử dụng file `Dockerfile.prod`):
   ```bash
   # 1. Đăng nhập AWS ECR
   aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <aws_account_id>.dkr.ecr.<region>.amazonaws.com

   # 2. Build production image
   docker build -f Dockerfile.prod -t fastapi-ecs-rds .

   # 3. Tag image
   docker tag fastapi-ecs-rds:latest <aws_account_id>.dkr.ecr.<region>.amazonaws.com/fastapi-ecs-rds:latest

   # 4. Push lên ECR
   docker push <aws_account_id>.dkr.ecr.<region>.amazonaws.com/fastapi-ecs-rds:latest
   ```
5. Copy đường dẫn `Image URI` vừa push.

---

### Bước 2: Tạo AWS RDS (PostgreSQL)
1. Vào **RDS Console** -> Chọn **Create database**:
   - Phương thức: **Standard create**.
   - Engine: **PostgreSQL** (chọn phiên bản 16 hoặc 15).
   - Templates: **Free Tier**.
   - Settings:
     - DB instance identifier: `demo-postgres`.
     - Master username: `postgres`.
     - Master password: `<nhập mật khẩu của bạn>` (ví dụ: `MyStrongPass123`).
   - Instance configuration: `db.t3.micro` hoặc `db.t4g.micro`.
   - Connectivity:
     - VPC: Chọn **Default VPC**.
     - Public access: **No** (an toàn nhất vì ECS cùng VPC sẽ tự kết nối nội bộ) hoặc **Yes** (nếu muốn kết nối từ DBeaver trên máy cá nhân).
     - VPC Security Group: Chọn **Create new**, đặt tên `rds-db-sg`.
   - **Additional configuration**:
     - *Rất quan trọng:* Điền **Initial database name** là `appdb` (hoặc `postgres`).
2. Bấm **Create database** (chờ 5 - 10 phút để chuyển sang trạng thái `Available`).
3. Khi xong, click vào database và copy **Endpoint** (dạng `demo-postgres.c123456.ap-southeast-1.rds.amazonaws.com`).

---

### Bước 3: Cấu hình Security Group (Chìa khóa kết nối giữa ECS & RDS)
1. Mở **EC2 Console** -> Menu bên trái chọn **Security Groups**.
2. Bấm **Create security group** cho ECS:
   - Security group name: `ecs-task-sg`.
   - VPC: Default VPC.
   - **Inbound rules**:
     - Type: `Custom TCP`
     - Port range: `8000`
     - Source: `Anywhere-IPv4` (`0.0.0.0/0`)
   - Bấm **Create security group**.
3. Tìm security group của RDS (`rds-db-sg` vừa tạo ở Bước 2):
   - Chọn tab **Inbound rules** -> Bấm **Edit inbound rules**.
   - Type: `PostgreSQL` (Port `5432`).
   - **Source:** Nhập tên hoặc ID của `ecs-task-sg`.
   - Bấm **Save rules**.

---

### Bước 4: Tạo ECS Task Definition & Service

#### 4.1. Tạo Task Definition:
1. Vào **Amazon ECS** -> Menu trái chọn **Task Definitions** -> Bấm **Create new task definition**.
2. Launch type: **AWS Fargate**.
3. Cấu hình Container:
   - Container name: `fastapi-app`.
   - Image URI: Dán link ECR đã copy ở Bước 1.
   - Port mappings: Container port: `8000`, Protocol: `TCP`, App protocol: `HTTP`.
   - **Environment variables** (Khai báo thông tin kết nối DB):
     - `DB_HOST`: `<Endpoint RDS đã copy ở Bước 2>`
     - `DB_PORT`: `5432`
     - `DB_USER`: `postgres`
     - `DB_PASSWORD`: `<Mật khẩu bạn đặt ở Bước 2>`
     - `DB_NAME`: `appdb` (hoặc tên db bạn điền)
4. Bấm **Create**.

#### 4.2. Tạo ECS Cluster & Service:
1. Vào **Clusters** -> Bấm **Create cluster** -> Đặt tên `my-cluster` -> Infrastructure chọn **AWS Fargate** -> Bấm **Create**.
2. Vào trong `my-cluster` vừa tạo -> Chọn tab **Services** -> Bấm **Create**:
   - Environment: Launch type **FARGATE**.
   - Deployment configuration: Chọn Family Task Definition vừa tạo, Service name: `fastapi-service`, Desired tasks: `1`.
   - **Networking:**
     - VPC: Default VPC.
     - Security group: Chọn **Use existing security group** -> chọn `ecs-task-sg`.
     - **Public IP: Bật Turn ON** (Bắt buộc để Task có IP công khai).
3. Bấm **Create**.

---

### Bước 5: Lấy Public IP & Kiểm tra kết quả

1. Vào tab **Tasks** trong Service `fastapi-service`.
2. Bấm vào Task đang chạy (Status: `RUNNING`).
3. Trong mục **Configuration**, tìm dòng **Public IP**.
4. Mở trình duyệt và truy cập:
   ```
   http://<PUBLIC_IP>:8000
   ```
5. Giao diện sẽ hiển thị:
   - Huy hiệu xanh: **`Connected successfully!`**
   - Tên Host RDS và tên Database đang kết nối.
   - Bạn có thể vào `http://<PUBLIC_IP>:8000/docs` để test thêm/xem dữ liệu qua Swagger UI.

---

## 6. Kết nối từ máy Local vào RDS Private qua AWS SSM (Không cần VPN)

Vì RDS nằm trong Private Subnet và không mở cổng ra Internet, chúng ta sử dụng **AWS Systems Manager (SSM) Port Forwarding** thông qua 1 máy ảo Bastion siêu nhỏ:

### Cách mở kết nối:
Chỉ cần chạy lệnh:
```bash
make tunnel
# Hoặc: ./tunnel-db.sh
```

### Thông số kết nối DBeaver / TablePlus / Navicat:
- **Host:** `localhost`
- **Port:** `5433`
- **Database:** `app_notes_db`
- **User:** `postgres`
- **Password:** `<mật khẩu bạn đã đặt khi tạo RDS>`

Sau khi dùng xong, nhấn `Ctrl + C` ở terminal để đóng đường hầm.

---

## 7. Các lệnh tiện ích với Makefile

Dự án cung cấp sẵn `Makefile` hỗ trợ quản lý **version ngữ nghĩa** (`v1.0.1`, `v1.0.2`,...):

```bash
make help                       # Xem danh sách các lệnh
make tunnel                     # Mở đường hầm SSM kết nối vào AWS RDS
make dev                        # Chạy app ở local (Docker compose + hot-reload)
make dev-logs                   # Xem logs app local
make dev-down                   # Dừng container local

# Build & Push (Mặc định dùng version khai báo trong Makefile, hiện tại là v1.0.1):
make push-prod

# Hoặc muốn tăng version khi deploy phiên bản mới:
make push-prod VERSION=v1.0.2
```
