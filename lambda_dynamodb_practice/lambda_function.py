import os
import json
import logging
from decimal import Decimal
from typing import Dict, Any

from models.user import User
from models.order import Order
from repositories.user_repository import UserRepository
from repositories.order_repository import OrderRepository

# Cấu hình logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Khởi tạo Repositories
user_repo = UserRepository()
order_repo = OrderRepository()

class DecimalEncoder(json.JSONEncoder):
    """DynamoDB lưu số dạng Decimal, encoder này chuyển đổi an toàn sang int/float."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super().default(obj)

def build_response(status_code: int, body: Any) -> Dict[str, Any]:
    """Helper hàm chuẩn hóa HTTP Response trả về cho API Gateway."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        },
        "body": json.dumps(body, cls=DecimalEncoder, ensure_ascii=False)
    }

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Entry point chính của AWS Lambda:
    Tương thích với cả API Gateway HTTP API (Payload v2) và REST API (Payload v1).
    Hỗ trợ đa thực thể: Users & Orders (CRUD + Repository Pattern).
    """
    logger.info(f"Incoming Event: {json.dumps(event)}")

    # 1. Trích xuất HTTP Method và Path
    http_method = (
        event.get("requestContext", {}).get("http", {}).get("method")  # HTTP API v2
        or event.get("httpMethod")                                       # REST API v1
        or "GET"
    ).upper()

    # Hỗ trợ CORS Preflight
    if http_method == "OPTIONS":
        return build_response(200, {"message": "OK"})

    raw_path = (event.get("rawPath") or event.get("path") or "/").rstrip("/")
    path_parameters = event.get("pathParameters") or {}

    # Parse request body (nếu có)
    body_data = {}
    if event.get("body"):
        try:
            body_data = json.loads(event["body"])
        except json.JSONDecodeError:
            return build_response(400, {"success": False, "message": "Invalid JSON body"})

    try:
        # ==============================================================
        # 0. GET / - Trang chủ giới thiệu toàn bộ API (Users & Orders)
        # ==============================================================
        if http_method == "GET" and (raw_path == "" or raw_path == "/"):
            return build_response(200, {
                "message": "User & Order Management Service API (DevOps Buổi 12+13)",
                "status": "online",
                "tables": {
                    "users_table": user_repo.table_name,
                    "orders_table": order_repo.table_name
                },
                "endpoints": {
                    "users": {
                        "get_all": "GET /users",
                        "get_by_id": "GET /users/{id}",
                        "get_orders_of_user": "GET /users/{id}/orders",
                        "create": "POST /users",
                        "update": "PUT /users/{id}",
                        "delete": "DELETE /users/{id}"
                    },
                    "orders": {
                        "get_all": "GET /orders",
                        "get_by_id": "GET /orders/{userId}/{orderId}",
                        "create": "POST /orders",
                        "update": "PUT /orders/{userId}/{orderId}",
                        "delete": "DELETE /orders/{userId}/{orderId}"
                    }
                }
            })

        # ==============================================================
        # PHẦN 1: USERS API ROUTES
        # ==============================================================
        
        # 1.1 GET /users/{id}/orders - Lấy toàn bộ đơn hàng của 1 user
        if http_method == "GET" and "/orders" in raw_path and raw_path.startswith("/users/"):
            parts = [p for p in raw_path.split("/") if p]
            user_id = path_parameters.get("id") or (parts[1] if len(parts) >= 3 else None)
            if not user_id:
                return build_response(400, {"success": False, "message": "Thiếu user ID"})
            orders = order_repo.get_by_user_id(user_id)
            return build_response(200, {
                "success": True,
                "userId": user_id,
                "count": len(orders),
                "data": orders
            })

        # 1.2 GET /users - Lấy danh sách toàn bộ Users
        if http_method == "GET" and raw_path == "/users":
            users = user_repo.get_all()
            return build_response(200, {
                "success": True,
                "message": "Lấy danh sách users thành công",
                "count": len(users),
                "data": users
            })

        # 1.3 GET /users/{id} - Lấy chi tiết 1 User
        if http_method == "GET" and raw_path.startswith("/users/"):
            user_id = path_parameters.get("id") or raw_path.split("/")[-1]
            user = user_repo.get_by_id(user_id)
            if not user:
                return build_response(404, {
                    "success": False,
                    "message": f"Không tìm thấy user với id: {user_id}"
                })
            return build_response(200, {
                "success": True,
                "data": user
            })

        # 1.4 POST /users - Tạo mới User
        if http_method == "POST" and raw_path == "/users":
            name = body_data.get("name")
            email = body_data.get("email")

            if not name or not email:
                return build_response(400, {
                    "success": False,
                    "message": "Các trường 'name' và 'email' là bắt buộc"
                })

            new_user = User(
                id=body_data.get("userId") or body_data.get("id"),
                name=name,
                email=email,
                role=body_data.get("role", "user"),
                age=body_data.get("age")
            )
            created_user = user_repo.create(new_user)
            return build_response(201, {
                "success": True,
                "message": "Tạo user mới thành công",
                "data": created_user
            })

        # 1.5 PUT /users/{id} - Cập nhật User
        if http_method == "PUT" and raw_path.startswith("/users/"):
            user_id = path_parameters.get("id") or raw_path.split("/")[-1]
            existing = user_repo.get_by_id(user_id)
            if not existing:
                return build_response(404, {
                    "success": False,
                    "message": f"Không tìm thấy user với id: {user_id}"
                })

            updated_user = user_repo.update(user_id, body_data)
            return build_response(200, {
                "success": True,
                "message": f"Cập nhật user {user_id} thành công",
                "data": updated_user
            })

        # 1.6 DELETE /users/{id} - Xóa User
        if http_method == "DELETE" and raw_path.startswith("/users/"):
            user_id = path_parameters.get("id") or raw_path.split("/")[-1]
            existing = user_repo.get_by_id(user_id)
            if not existing:
                return build_response(404, {
                    "success": False,
                    "message": f"Không tìm thấy user với id: {user_id}"
                })

            user_repo.delete(user_id)
            return build_response(200, {
                "success": True,
                "message": f"Đã xóa user {user_id} thành công"
            })

        # ==============================================================
        # PHẦN 2: ORDERS API ROUTES
        # ==============================================================

        # 2.1 GET /orders - Lấy danh sách toàn bộ Orders
        if http_method == "GET" and raw_path == "/orders":
            orders = order_repo.get_all()
            return build_response(200, {
                "success": True,
                "message": "Lấy danh sách orders thành công",
                "count": len(orders),
                "data": orders
            })

        # 2.2 GET /orders/{userId}/{orderId} - Lấy chi tiết 1 Order
        if http_method == "GET" and raw_path.startswith("/orders/"):
            parts = [p for p in raw_path.split("/") if p]
            user_id = path_parameters.get("userId") or (parts[1] if len(parts) >= 2 else None)
            order_id = path_parameters.get("orderId") or (parts[2] if len(parts) >= 3 else None)
            if not user_id or not order_id:
                return build_response(400, {"success": False, "message": "Cần cung cấp cả userId và orderId (/orders/{userId}/{orderId})"})

            order = order_repo.get_by_id(user_id, order_id)
            if not order:
                return build_response(404, {
                    "success": False,
                    "message": f"Không tìm thấy order {order_id} của user {user_id}"
                })
            return build_response(200, {
                "success": True,
                "data": order
            })

        # 2.3 POST /orders - Tạo mới Order
        if http_method == "POST" and raw_path == "/orders":
            user_id = body_data.get("userId")
            order_id = body_data.get("orderId")
            total = body_data.get("total")

            if not user_id or not order_id or total is None:
                return build_response(400, {
                    "success": False,
                    "message": "Các trường 'userId', 'orderId', 'total' là bắt buộc"
                })

            new_order = Order(
                userId=user_id,
                orderId=order_id,
                total=float(total),
                status=body_data.get("status", "pending")
            )
            created_order = order_repo.create(new_order)
            return build_response(201, {
                "success": True,
                "message": "Tạo order mới thành công",
                "data": created_order
            })

        # 2.4 PUT /orders/{userId}/{orderId} - Cập nhật Order
        if http_method == "PUT" and raw_path.startswith("/orders/"):
            parts = [p for p in raw_path.split("/") if p]
            user_id = path_parameters.get("userId") or (parts[1] if len(parts) >= 2 else None)
            order_id = path_parameters.get("orderId") or (parts[2] if len(parts) >= 3 else None)
            if not user_id or not order_id:
                return build_response(400, {"success": False, "message": "Cần cung cấp cả userId và orderId"})

            existing = order_repo.get_by_id(user_id, order_id)
            if not existing:
                return build_response(404, {
                    "success": False,
                    "message": f"Không tìm thấy order {order_id} của user {user_id}"
                })

            updated_order = order_repo.update(user_id, order_id, body_data)
            return build_response(200, {
                "success": True,
                "message": f"Cập nhật order {order_id} thành công",
                "data": updated_order
            })

        # 2.5 DELETE /orders/{userId}/{orderId} - Xóa Order
        if http_method == "DELETE" and raw_path.startswith("/orders/"):
            parts = [p for p in raw_path.split("/") if p]
            user_id = path_parameters.get("userId") or (parts[1] if len(parts) >= 2 else None)
            order_id = path_parameters.get("orderId") or (parts[2] if len(parts) >= 3 else None)
            if not user_id or not order_id:
                return build_response(400, {"success": False, "message": "Cần cung cấp cả userId và orderId"})

            existing = order_repo.get_by_id(user_id, order_id)
            if not existing:
                return build_response(404, {
                    "success": False,
                    "message": f"Không tìm thấy order {order_id} của user {user_id}"
                })

            order_repo.delete(user_id, order_id)
            return build_response(200, {
                "success": True,
                "message": f"Đã xóa order {order_id} thành công"
            })

        # Route không hỗ trợ
        return build_response(400, {
            "success": False,
            "message": f"Route hoặc method '{http_method} {raw_path}' không được hỗ trợ"
        })

    except Exception as e:
        logger.error(f"Lỗi xử lý request: {str(e)}", exc_info=True)
        return build_response(500, {
            "success": False,
            "error": str(e)
        })
