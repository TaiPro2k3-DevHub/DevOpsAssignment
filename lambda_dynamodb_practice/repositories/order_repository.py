import os
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from typing import List, Optional, Dict, Any
from botocore.exceptions import ClientError
from models.order import Order

def convert_floats_to_decimals(obj: Any) -> Any:
    """DynamoDB không hỗ trợ float, cần chuyển float thành Decimal."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: convert_floats_to_decimals(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_floats_to_decimals(i) for i in obj]
    return obj

class OrderRepository:
    """
    Repository pattern đóng gói toàn bộ logic truy vấn DynamoDB cho Order entity.
    Bảng Orders có Composite Key:
      - Partition Key (HASH): userId
      - Sort Key (RANGE): orderId
    """
    def __init__(self, table_name: Optional[str] = None):
        self.table_name = table_name or os.environ.get("ORDERS_TABLE", "Orders")
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(self.table_name)

    def get_all(self) -> List[Dict[str, Any]]:
        """Lấy toàn bộ danh sách đơn hàng (Scan)"""
        try:
            response = self.table.scan()
            items = response.get("Items", [])
            while "LastEvaluatedKey" in response:
                response = self.table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
                items.extend(response.get("Items", []))
            return items
        except ClientError as e:
            raise RuntimeError(f"Lỗi khi lấy danh sách orders: {e.response['Error']['Message']}")

    def get_by_user_id(self, user_id: str) -> List[Dict[str, Any]]:
        """Lấy toàn bộ đơn hàng của 1 user (Query tối ưu theo Partition Key)"""
        try:
            response = self.table.query(
                KeyConditionExpression=Key("userId").eq(user_id)
            )
            return response.get("Items", [])
        except ClientError as e:
            raise RuntimeError(f"Lỗi khi query đơn hàng của user {user_id}: {e.response['Error']['Message']}")

    def get_by_id(self, user_id: str, order_id: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin 1 đơn hàng cụ thể theo Composite Key (userId, orderId)"""
        try:
            response = self.table.get_item(
                Key={
                    "userId": user_id,
                    "orderId": order_id
                }
            )
            return response.get("Item")
        except ClientError as e:
            raise RuntimeError(f"Lỗi khi lấy order {order_id}: {e.response['Error']['Message']}")

    def create(self, order: Order) -> Dict[str, Any]:
        """Tạo đơn hàng mới (PutItem)"""
        try:
            item = convert_floats_to_decimals(order.to_dict())
            self.table.put_item(Item=item)
            return item
        except ClientError as e:
            raise RuntimeError(f"Lỗi khi tạo order: {e.response['Error']['Message']}")

    def update(self, user_id: str, order_id: str, update_fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Cập nhật đơn hàng (UpdateItem)"""
        try:
            # Loại bỏ các trường khóa chính
            update_data = {
                k: convert_floats_to_decimals(v) for k, v in update_fields.items()
                if k not in ("userId", "orderId")
            }
            if not update_data:
                return self.get_by_id(user_id, order_id)

            update_expression = "SET " + ", ".join([f"#{k} = :{k}" for k in update_data.keys()])
            expression_attribute_names = {f"#{k}": k for k in update_data.keys()}
            expression_attribute_values = {f":{k}": v for k, v in update_data.items()}

            response = self.table.update_item(
                Key={
                    "userId": user_id,
                    "orderId": order_id
                },
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues="ALL_NEW"
            )
            return response.get("Attributes")
        except ClientError as e:
            raise RuntimeError(f"Lỗi khi cập nhật order {order_id}: {e.response['Error']['Message']}")

    def delete(self, user_id: str, order_id: str) -> bool:
        """Xóa 1 đơn hàng (DeleteItem)"""
        try:
            self.table.delete_item(
                Key={
                    "userId": user_id,
                    "orderId": order_id
                }
            )
            return True
        except ClientError as e:
            raise RuntimeError(f"Lỗi khi xóa order {order_id}: {e.response['Error']['Message']}")
