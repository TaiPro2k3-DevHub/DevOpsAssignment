import os
import boto3
from typing import List, Optional, Dict, Any
from botocore.exceptions import ClientError
from models.user import User

class UserRepository:
    """
    Repository pattern đóng gói toàn bộ logic tương tác với DynamoDB cho User entity.
    Tự động tương thích với cả partition key 'userId' và 'id'.
    """
    def __init__(self, table_name: Optional[str] = None):
        self.table_name = table_name or os.environ.get("USERS_TABLE") or os.environ.get("TABLE_NAME", "Users")
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(self.table_name)
        
        # Xác định Partition Key (mặc định là userId hoặc lấy từ env/schema)
        self.pk_name = os.environ.get("PRIMARY_KEY", "userId")
        try:
            if hasattr(self.table, "key_schema") and self.table.key_schema:
                self.pk_name = self.table.key_schema[0]["AttributeName"]
        except Exception:
            pass

    def get_all(self) -> List[Dict[str, Any]]:
        """Lấy toàn bộ danh sách users trong bảng (Scan)"""
        try:
            response = self.table.scan()
            items = response.get("Items", [])
            # Hỗ trợ phân trang nếu bảng lớn hơn 1MB
            while "LastEvaluatedKey" in response:
                response = self.table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
                items.extend(response.get("Items", []))
            return items
        except ClientError as e:
            raise RuntimeError(f"Lỗi khi lấy danh sách users: {e.response['Error']['Message']}")

    def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin 1 user theo Partition Key (GetItem)"""
        try:
            response = self.table.get_item(Key={self.pk_name: user_id})
            return response.get("Item")
        except ClientError as e:
            raise RuntimeError(f"Lỗi khi lấy user {user_id}: {e.response['Error']['Message']}")

    def create(self, user: User) -> Dict[str, Any]:
        """Tạo mới 1 user trong DynamoDB (PutItem)"""
        try:
            item = user.to_dict(pk_name=self.pk_name)
            self.table.put_item(Item=item)
            return item
        except ClientError as e:
            raise RuntimeError(f"Lỗi khi tạo user: {e.response['Error']['Message']}")

    def update(self, user_id: str, update_fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Cập nhật các trường thông tin của user (UpdateItem)"""
        try:
            # Loại bỏ partition key và id nếu client vô tình gửi kèm
            update_data = {
                k: v for k, v in update_fields.items()
                if k not in (self.pk_name, "id", "userId")
            }
            if not update_data:
                return self.get_by_id(user_id)

            update_expression = "SET " + ", ".join([f"#{k} = :{k}" for k in update_data.keys()])
            expression_attribute_names = {f"#{k}": k for k in update_data.keys()}
            expression_attribute_values = {f":{k}": v for k, v in update_data.items()}

            response = self.table.update_item(
                Key={self.pk_name: user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues="ALL_NEW"
            )
            return response.get("Attributes")
        except ClientError as e:
            raise RuntimeError(f"Lỗi khi cập nhật user {user_id}: {e.response['Error']['Message']}")

    def delete(self, user_id: str) -> bool:
        """Xóa 1 user theo id (DeleteItem)"""
        try:
            self.table.delete_item(Key={self.pk_name: user_id})
            return True
        except ClientError as e:
            raise RuntimeError(f"Lỗi khi xóa user {user_id}: {e.response['Error']['Message']}")
