# -*- coding: utf-8 -*-
"""
MinIO上传模块 - 上传文件到MinIO服务器
"""
import os
import logging
from minio import Minio
from minio.error import S3Error
from config import MINIO_CONFIG


class MinIOUploader:
    """MinIO上传器"""
    
    def __init__(self, config=None):
        """
        初始化MinIO上传器
        
        Args:
            config: MinIO配置字典，如果为None则使用默认配置
        """
        self.config = config or MINIO_CONFIG
        
        # 初始化MinIO客户端
        try:
            self.client = Minio(
                endpoint=self.config['endpoint'],
                access_key=self.config['access_key'],
                secret_key=self.config['secret_key'],
                secure=self.config.get('secure', False)
            )
            self.bucket_name = self.config['bucket_name']  # 默认bucket
            
            # 检查默认存储桶是否存在，如果不存在则创建
            self._ensure_bucket_exists(self.bucket_name)
            
            logging.info(f"初始化MinIO上传器成功: {self.config['endpoint']}, default bucket: {self.bucket_name}")
            
        except Exception as e:
            logging.error(f"初始化MinIO客户端失败: {e}")
            raise
    
    def _ensure_bucket_exists(self, bucket_name=None):
        """确保存储桶存在"""
        bucket_name = bucket_name or self.bucket_name
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logging.info(f"创建存储桶: {bucket_name}")
            else:
                logging.debug(f"存储桶已存在: {bucket_name}")
        except S3Error as e:
            logging.error(f"检查/创建存储桶失败: {e}")
            raise
    
    def upload_file(self, local_path, object_name, bucket_name=None):
        """
        上传文件到MinIO
        
        Args:
            local_path: 本地文件路径
            object_name: MinIO中的对象名称
            bucket_name: 目标bucket名称，如果为None则使用默认bucket
            
        Returns:
            bool: 上传是否成功
        """
        try:
            # 确定目标bucket
            target_bucket = bucket_name or self.bucket_name
            
            # 确保bucket存在
            self._ensure_bucket_exists(target_bucket)
            
            # 获取文件大小
            file_size = os.path.getsize(local_path)
            
            # 检测文件类型
            content_type = self._guess_content_type(local_path)
            
            logging.info(f"开始上传: {local_path} -> {object_name} ({file_size} bytes)")
            
            # 上传文件
            result = self.client.fput_object(
                bucket_name=target_bucket,
                object_name=object_name,
                file_path=local_path,
                content_type=content_type
            )
            
            logging.info(f"上传成功: {object_name}, ETag: {result.etag}")
            return True
            
        except Exception as e:
            logging.error(f"上传文件失败: {local_path} -> {object_name}, 错误: {e}")
            return False

    def check_object_exists(self, object_name, bucket_name=None):
        """
        检查MinIO中的对象是否存在
        
        Args:
            object_name: 对象名称
            bucket_name: bucket名称，如果为None则使用默认bucket
            
        Returns:
            bool: 对象是否存在
        """
        try:
            target_bucket = bucket_name or self.bucket_name
            self.client.stat_object(target_bucket, object_name)
            return True
        except Exception:
            return False

    def get_object_info(self, object_name, bucket_name=None):
        """
        获取MinIO对象信息
        
        Args:
            object_name: 对象名称  
            bucket_name: bucket名称，如果为None则使用默认bucket
            
        Returns:
            dict: 对象信息
        """
        try:
            target_bucket = bucket_name or self.bucket_name
            stat = self.client.stat_object(target_bucket, object_name)
            return {
                'size': stat.size,
                'last_modified': stat.last_modified.isoformat() if stat.last_modified else '',
                'etag': stat.etag,
                'content_type': stat.content_type
            }
        except Exception as e:
            logging.error(f"获取对象信息失败: {object_name}, 错误: {e}")
            return None

    def _guess_content_type(self, file_path):
        """根据文件扩展名猜测内容类型"""
        import mimetypes
        content_type, _ = mimetypes.guess_type(file_path)
        return content_type or 'application/octet-stream'
    
    def delete_object(self, object_name):
        """
        删除对象
        
        Args:
            object_name: 对象名称
            
        Returns:
            bool: 删除是否成功
        """
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logging.info(f"删除对象成功: {object_name}")
            return True
        except Exception as e:
            logging.error(f"删除对象失败: {object_name}, 错误: {e}")
            return False
    
    def list_objects(self, prefix='', recursive=True, max_objects=None):
        """
        列出对象
        
        Args:
            prefix: 前缀过滤
            recursive: 是否递归列出
            max_objects: 最大返回数量
            
        Returns:
            list: 对象列表
        """
        try:
            objects = self.client.list_objects(
                self.bucket_name,
                prefix=prefix,
                recursive=recursive
            )
            object_list = [obj.object_name for obj in objects]
            if max_objects:
                return object_list[:max_objects]
            return object_list
        except Exception as e:
            logging.error(f"列出对象失败: {e}")
            return []
    
    def generate_presigned_url(self, object_name, expires_in=3600):
        """
        生成预签名URL
        
        Args:
            object_name: 对象名称
            expires_in: 过期时间(秒)
            
        Returns:
            str: 预签名URL
        """
        try:
            from datetime import timedelta
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=timedelta(seconds=expires_in)
            )
            return url
        except Exception as e:
            logging.error(f"生成预签名URL失败: {object_name}, 错误: {e}")
            return None
