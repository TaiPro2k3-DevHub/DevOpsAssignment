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

---

## 5. Cấu hình Custom Domain & DNS với Cloudflare

Để gắn subdomain tùy chỉnh (ví dụ: `f8-devops-nuxt-example.taiphanvan.id.vn`) vào CloudFront:

### 5.1. Thêm Domain và xin SSL Certificate trên CloudFront
1. Trong CloudFront Distribution, chọn **Add domain** (hoặc mục *Alternate domain name - CNAME*).
2. Điền subdomain cần dùng: `f8-devops-nuxt-example.taiphanvan.id.vn`.
3. Tạo chứng chỉ SSL thông qua **AWS Certificate Manager (ACM)**:
   * **Lưu ý quan trọng**: Chứng chỉ SSL cho CloudFront **bắt buộc phải tạo ở Region `us-east-1` (N. Virginia)**.
   * Phương thức xác thực: Chọn **DNS validation**.
   * ACM sẽ cung cấp 1 cặp `CNAME Name` và `CNAME Value` để xác thực quyền sở hữu tên miền.

### 5.2. Thêm 2 bản ghi DNS trên Cloudflare
Truy cập trang quản trị DNS của domain trên Cloudflare và tạo **2 bản ghi CNAME**:

| STT | Loại (Type) | Tên (Name) | Đích (Target) | Proxy status | Mục đích |
| :---: | :---: | :--- | :--- | :---: | :--- |
| **1** | `CNAME` | `_15c15037...` *(copy từ ACM)* | `_bb1684c...acm-validations.aws.` | 🔘 **DNS Only** *(Xám)* | Xác thực chủ sở hữu để AWS cấp SSL |
| **2** | `CNAME` | `f8-devops-nuxt-example` | `<id>.cloudfront.net` *(Domain CloudFront)* | 🔘 **DNS Only** *(Xám)* | Điều hướng truy cập về CloudFront CDN |

### 5.3. Lưu ý quan trọng: Tại sao phải chọn "DNS Only" (Đám mây màu xám)?
* **Với bản ghi xác thực SSL (Bản ghi 1):** Nếu bật Proxy (đám mây màu cam), Cloudflare sẽ ẩn CNAME thật và chỉ trả về IP của Cloudflare. Khi đó AWS bot không tìm thấy bản ghi CNAME để xác minh, khiến chứng chỉ bị treo vĩnh viễn ở trạng thái *Pending Validation*.
* **Với bản ghi điều hướng web (Bản ghi 2):** Bản thân CloudFront đã là một CDN toàn cầu hoàn chỉnh. Nếu bật thêm Proxy cam của Cloudflare sẽ gây ra hiện tượng **Double CDN** (Cloudflare đè lên CloudFront), dễ dẫn tới lỗi SSL Handshake (Error 525/526) và tăng độ trễ mạng.

---

## 6. Kiến thức mở rộng: Hiện tượng "DNS Lag" & Negative Caching (RFC 2308)

### 6.1. Bản chất phân cấp của hệ thống DNS
1. **Authoritative DNS (Cloudflare):** Nơi trực tiếp lưu trữ và quản lý bản ghi gốc.
2. **Recursive DNS Resolver (Router nhà mạng Viettel/VNPT/FPT):** Máy chủ trung gian lưu cache để phục vụ người dùng.
3. **Local Cache:** Bộ nhớ đệm ngay trên hệ điều hành (macOS/Windows).

### 6.2. Hiện tượng Negative DNS Cache (Nguyên nhân chính gây "lag")
* Khi một tên miền vừa được tạo và chưa kịp phân giải, nếu máy tính gửi truy vấn đến DNS nhà mạng, máy chủ sẽ nhận về kết quả `NXDOMAIN` (tên miền không tồn tại).
* Theo chuẩn **RFC 2308**, để tránh spam truy vấn tên miền lỗi, DNS nhà mạng sẽ **lưu tạm câu trả lời "Không tồn tại" này vào bộ nhớ cache** trong một khoảng thời gian (gọi là *Negative Caching TTL*, quy định trong bản ghi `SOA`, thường từ 15 đến 30 phút).
* Do đó, dù bạn đã bấm Save trên Cloudflare ngay sau đó, máy tính của bạn vẫn nhận lại kết quả lỗi cũ từ cache của nhà mạng.

### 6.3. Tại sao mạng 4G/Điện thoại vào được ngay?
Mạng di động dùng cụm DNS riêng và chưa từng gửi request vào thời điểm tên miền bị lỗi, do đó nó nhận được bản ghi mới nhất từ Cloudflare ngay lập tức.

### 6.4. Best Practice cho Kỹ sư DevOps
* Đổi DNS máy tính cá nhân sang **`1.1.1.1`** (Cloudflare) hoặc **`8.8.8.8`** (Google) để nhận bản ghi gần như theo thời gian thực (real-time).
* Lệnh xóa DNS Cache trên macOS:
  ```bash
  sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
  ```
* Dùng lệnh `dig` chỉ định máy chủ DNS để kiểm tra chính xác:
  ```bash
  dig @1.1.1.1 <tên-subdomain> +short
  ```
