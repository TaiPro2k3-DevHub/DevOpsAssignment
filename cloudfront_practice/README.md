# Nuxt 4 Practice với Docker, AWS S3 & CloudFront

Dự án thực hành xây dựng ứng dụng Nuxt 4, quản lý môi trường phát triển hoàn toàn thông qua Docker và triển khai tĩnh (Static Site Generation) lên AWS S3 kết hợp AWS CloudFront CDN.

---

## 1. Khởi tạo dự án ban đầu (Chỉ chạy 1 lần)

Nếu cần khởi tạo dự án từ đầu mà không cần cài Node.js/pnpm trên máy host:

```bash
# 1. Build image builder từ Dockerfile
docker build -t nuxt-builder .

# 2. Khởi tạo Nuxt vào thư mục hiện tại thông qua container
docker run --rm -it -v "$(pwd)":/app nuxt-builder sh
# Trong container chạy:
# pnpm dlx nuxi@latest init . --packageManager pnpm --gitInit false
```

---

## 2. Phát triển hàng ngày (Development với Docker Compose)

Toàn bộ quá trình code được chạy qua Docker Compose:

* **Khởi động Dev Server:**
  ```bash
  docker compose up
  ```
  *(Truy cập: `http://localhost:3000`)*

* **Chạy ngầm (background):**
  ```bash
  docker compose up -d
  ```

* **Dừng Dev Server:**
  ```bash
  docker compose down
  ```

* **Cài đặt thêm package mới:**
  ```bash
  # Cài runtime dependency
  docker compose run --rm app pnpm add <package-name>

  # Cài dev dependency
  docker compose run --rm app pnpm add -D <dev-package-name>
  ```

* **Mở shell vào trong container:**
  ```bash
  docker compose run --rm app sh
  ```

---

## 3. Build dự án (Static Site Generation - SSG)

Dự án được cấu hình xuất toàn bộ static assets vào thư mục `dist/` (trong `nuxt.config.ts`):

```bash
docker compose run --rm app pnpm run generate
```

---

## 4. Deploy lên AWS S3 & CloudFront

### 4.1. Upload lên S3 Bucket
Đồng bộ toàn bộ nội dung trong thư mục `dist/` lên S3 Bucket:

```bash
aws s3 sync dist/ s3://f8-devops-nuxt-example-taiphanvan2403 --delete
```

### 4.2. Làm mới Cache CloudFront (Invalidation)
Khi có phiên bản build mới, xoá cache tại các Edge Location để người dùng nhận code mới ngay lập tức:

```bash
aws cloudfront create-invalidation --distribution-id <DISTRIBUTION_ID> --paths "/*"
```
