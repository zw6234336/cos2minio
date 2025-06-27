# -*- coding: utf-8 -*-
"""
COS下载模块 - 从腾讯云COS下载文件
"""
import os
import logging
import tempfile
from qcloud_cos import CosConfig, CosS3Client
from config import COS_CONFIGS, DEFAULT_COS_CONFIG


class COSDownloader:
    """腾讯云COS下载器"""
    
    def __init__(self, cos_config_name=None):
        """
        初始化COS下载器
        
        Args:
            cos_config_name: COS配置名称，如果为None则使用默认配置
        """
        self.config_name = cos_config_name or DEFAULT_COS_CONFIG
        self.cos_config = COS_CONFIGS.get(self.config_name)
        
        if not self.cos_config:
            raise ValueError(f"未找到COS配置: {self.config_name}")
            
        # 初始化COS客户端
        config = CosConfig(
            Region=self.cos_config['region'],
            SecretId=self.cos_config['secret_id'],
            SecretKey=self.cos_config['secret_key'],
            Token='',
            Scheme='https'
        )
        self.client = CosS3Client(config)
        self.bucket_name = self.cos_config['bucket']
        
        logging.info(f"初始化COS下载器: {self.config_name}, bucket: {self.bucket_name}")
    
    def auto_detect_bucket_config(self, url, bucket_hint=None):
        """
        根据URL或bucket hint自动检测并设置正确的存储桶配置（用于COS源端）

        Args:
            url: COS文件URL
            bucket_hint: 来自Excel的bucket名称提示

        Returns:
            bool: 是否成功检测到配置
        """
        try:
            # 优先使用 bucket_hint 进行匹配
            if bucket_hint:
                for config_name, config in COS_CONFIGS.items():
                    if bucket_hint in config['bucket']:
                        self._set_client_config(config_name, config)
                        logging.info(f"通过Excel hint '{bucket_hint}' 切换到配置: {config_name}, bucket: {self.bucket_name}")
                        return True

            # 如果 hint 失败或未提供，则回退到基于URL的检测
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            
            host_parts = parsed_url.netloc.split('.')
            if len(host_parts) > 0:
                bucket_from_url = host_parts[0]
                
                for config_name, config in COS_CONFIGS.items():
                    if bucket_from_url in config['bucket']:
                        self._set_client_config(config_name, config)
                        logging.info(f"通过URL自动切换到配置: {config_name}, bucket: {self.bucket_name}")
                        return True
                        
            logging.warning(f"未找到匹配的COS源存储桶配置: {url}")
            return False
            
        except Exception as e:
            logging.error(f"自动检测COS源存储桶配置失败: {e}")
            return False

    def _set_client_config(self, config_name, config):
        """根据给定配置设置COS客户端"""
        self.config_name = config_name
        self.cos_config = config
        
        cos_config = CosConfig(
            Region=self.cos_config['region'],
            SecretId=self.cos_config['secret_id'],
            SecretKey=self.cos_config['secret_key'],
            Token='',
            Scheme='https'
        )
        self.client = CosS3Client(cos_config)
        self.bucket_name = self.cos_config['bucket']
    
    def download_file_from_url(self, url, local_path=None, temp_dir=None):
        """
        从COS URL下载文件（自动检测存储桶）
        
        Args:
            url: 完整的COS URL
            local_path: 本地保存路径，如果为None则使用临时文件
            temp_dir: 临时目录
            
        Returns:
            str: 下载后的本地文件路径，失败返回None
        """
        try:
            # 自动检测并切换到正确的存储桶配置
            if not self.auto_detect_bucket_config(url):
                logging.error(f"无法检测存储桶配置: {url}")
                return None
            
            # 从URL提取文件路径
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            cos_path = parsed_url.path.lstrip('/')
            
            if not cos_path:
                logging.error(f"无法从URL提取文件路径: {url}")
                return None
            
            # 调用原有的下载方法
            return self.download_file(cos_path, local_path, temp_dir)
            
        except Exception as e:
            logging.error(f"从URL下载文件失败: {url}, 错误: {e}")
            return None
    
    def download_file(self, cos_path, local_path=None, temp_dir=None):
        """
        从COS下载单个文件
        
        Args:
            cos_path: COS文件路径
            local_path: 本地保存路径，如果为None则使用临时文件
            temp_dir: 临时目录
            
        Returns:
            str: 下载后的本地文件路径，失败返回None
        """
        try:
            # 如果没有指定本地路径，使用临时文件
            if local_path is None:
                if temp_dir and not os.path.exists(temp_dir):
                    os.makedirs(temp_dir, exist_ok=True)
                    
                # 保持原始文件名
                filename = os.path.basename(cos_path) or 'temp_file'
                if temp_dir:
                    local_path = os.path.join(temp_dir, filename)
                else:
                    # 使用系统临时目录
                    fd, local_path = tempfile.mkstemp(suffix=f'_{filename}')
                    os.close(fd)
            
            # 确保本地目录存在
            local_dir = os.path.dirname(local_path)
            if local_dir and not os.path.exists(local_dir):
                os.makedirs(local_dir, exist_ok=True)
            
            logging.info(f"开始下载: {cos_path} -> {local_path}")
            
            # 下载文件
            self.client.download_file(
                Bucket=self.bucket_name,
                Key=cos_path,
                DestFilePath=local_path
            )
            
            # 验证文件是否下载成功
            if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                logging.info(f"下载成功: {cos_path}")
                return local_path
            else:
                logging.error(f"下载的文件为空或不存在: {local_path}")
                return None
                
        except Exception as e:
            logging.error(f"下载文件失败: {cos_path}, 错误: {e}")
            # 清理可能的残留文件
            if local_path and os.path.exists(local_path):
                try:
                    os.remove(local_path)
                except:
                    pass
            return None
    
    def check_file_exists(self, cos_path):
        """
        检查COS文件是否存在
        
        Args:
            cos_path: COS文件路径
            
        Returns:
            bool: 文件是否存在
        """
        try:
            response = self.client.head_object(Bucket=self.bucket_name, Key=cos_path)
            logging.debug(f"文件存在: {cos_path}")
            return True
        except Exception as e:
            # 检查是否是CosServiceError且包含NoSuchResource
            error_msg = str(e)
            if 'NoSuchResource' in error_msg or 'NoSuchKey' in error_msg:
                logging.warning(f"COS文件不存在: {cos_path} (bucket: {self.bucket_name})")
            else:
                logging.error(f"检查文件存在性时发生错误: {cos_path}, 错误: {e}")
            return False
    
    def get_file_info(self, cos_path):
        """
        获取COS文件信息
        
        Args:
            cos_path: COS文件路径
            
        Returns:
            dict: 文件信息，包含大小、最后修改时间等
        """
        try:
            response = self.client.head_object(Bucket=self.bucket_name, Key=cos_path)
            return {
                'size': response.get('Content-Length', 0),
                'last_modified': response.get('Last-Modified', ''),
                'etag': response.get('ETag', ''),
                'content_type': response.get('Content-Type', '')
            }
        except Exception as e:
            logging.error(f"获取文件信息失败: {cos_path}, 错误: {e}")
            return None
    
    def list_objects(self, prefix='', max_keys=1000):
        """
        列出COS存储桶中的对象
        
        Args:
            prefix: 前缀过滤
            max_keys: 最大返回数量
            
        Returns:
            list: 对象列表
        """
        try:
            response = self.client.list_objects(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            return response.get('Contents', [])
        except Exception as e:
            logging.error(f"列出对象失败: {e}")
            return []
    
    def debug_list_similar_files(self, cos_path, prefix_depth=2):
        """
        调试方法：列出与给定路径相似的文件，用于排查文件不存在的问题
        
        Args:
            cos_path: 要查找的COS文件路径
            prefix_depth: 前缀深度，用于确定搜索范围
            
        Returns:
            list: 相似的文件列表
        """
        try:
            # 获取前缀路径
            path_parts = cos_path.split('/')
            if len(path_parts) > prefix_depth:
                prefix = '/'.join(path_parts[:prefix_depth]) + '/'
            else:
                prefix = ''
            
            logging.info(f"搜索存储桶 {self.bucket_name} 中前缀为 '{prefix}' 的文件...")
            
            response = self.client.list_objects(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=20  # 限制返回数量，避免过多输出
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append(obj['Key'])
                    logging.info(f"  找到文件: {obj['Key']}")
            else:
                logging.info(f"  前缀 '{prefix}' 下没有找到任何文件")
                
            if not files:
                # 如果没有找到文件，尝试列出根目录的一些文件
                logging.info(f"尝试列出存储桶 {self.bucket_name} 根目录的前20个文件...")
                response = self.client.list_objects(
                    Bucket=self.bucket_name,
                    MaxKeys=20
                )
                if 'Contents' in response:
                    for obj in response['Contents']:
                        files.append(obj['Key'])
                        logging.info(f"  根目录文件: {obj['Key']}")
                        
            return files
            
        except Exception as e:
            logging.error(f"调试列出文件失败: {e}")
            return []
