### 1. Region, AZ
- Chọn Region tại: ap-northeast-1
- Region này có 4 AZ, ta chọn 2 AZ (AZ-A, AZ-B) để tăng khả năng chịu lỗi
- VPC chọn CIDR block: 10.0.0.0/16
- Có 2 AZ, bên trong mỗi AZ có 4 subnet bao gồm:
  + 1 Public subnet
  + 1 Private Order subnet
  + 1 Private Payment subnet
  + 1 Private database subnet

=> Do đó VPC có tổng cộng 8 subnet. Có thể chia subnet dạng có prefix /19 (vừa khít), nhưng để dự phòng sau này có bổ sung thêm AZ-C/AZ-D vào VPC, chúng ta đã chia dải CIDR cho các subnet có prefix /20 như sau:

- AZ-A:
  + Public subnet: `10.0.0.0/20` có dải IP (10.0.0.0 -> 10.0.15.255)
  + Private Order subnet: `10.0.16.0/20` có dải IP (10.0.16.0 -> 10.0.31.255)
  + Private Payment subnet: `10.0.32.0/20` có dải IP (10.0.32.0 -> 10.0.47.255)
  + Private database subnet: `10.0.48.0/20` có dải IP (10.0.48.0 -> 10.0.63.255)
- AZ-B:
  + Public subnet: `10.0.64.0/20` có dải IP (10.0.64.0 -> 10.0.79.255)
  + Private Order subnet: `10.0.80.0/20` có dải IP (10.0.80.0 -> 10.0.95.255)
  + Private Payment subnet: `10.0.96.0/20` có dải IP (10.0.96.0 -> 10.0.111.255)
  + Private database subnet: `10.0.112.0/20` có dải IP (10.0.112.0 -> 10.0.127.255)

### 2. Route table

| AZ | Subnet Name | CIDR Block | Destination | Target |
| :--- | :--- | :--- | :--- | :--- |
| **AZ-A** | Order Private Subnet | `10.0.16.0/20` | `10.0.0.0/16` | `local` |
| **AZ-A** | Order Private Subnet | `10.0.16.0/20` | `0.0.0.0/0` | `NAT Gateway A` |
| **AZ-A** | Payment Private Subnet | `10.0.32.0/20` | `10.0.0.0/16` | `local` |
| **AZ-A** | Payment Private Subnet | `10.0.32.0/20` | `0.0.0.0/0` | `NAT Gateway A` |
| **AZ-B** | Order Private Subnet | `10.0.80.0/20` | `10.0.0.0/16` | `local` |
| **AZ-B** | Order Private Subnet | `10.0.80.0/20` | `0.0.0.0/0` | `NAT Gateway B` |
| **AZ-B** | Payment Private Subnet | `10.0.96.0/20` | `10.0.0.0/16` | `local` |
| **AZ-B** | Payment Private Subnet | `10.0.96.0/20` | `0.0.0.0/0` | `NAT Gateway B` |

