# -*- coding: utf-8 -*-
"""
配置文件 - 包含COS和MinIO的配置信息
"""
import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# 腾讯云COS配置
COS_CONFIGS = {
    'frcdap-dev': {
        'secret_id': os.getenv('COS_FRCDAP_DEV_SECRET_ID'),
        'secret_key': os.getenv('COS_FRCDAP_DEV_SECRET_KEY'),
        'region': os.getenv('COS_FRCDAP_DEV_REGION'),
        'bucket': os.getenv('COS_FRCDAP_DEV_BUCKET')
    },
    'frcdap': {
        'secret_id': os.getenv('COS_FRCDAP_SECRET_ID'),
        'secret_key': os.getenv('COS_FRCDAP_SECRET_KEY'),
        'region': os.getenv('COS_FRCDAP_REGION'),
        'bucket': os.getenv('COS_FRCDAP_BUCKET')
    },
    'dop-pro': {
        'secret_id': os.getenv('COS_DOP_PRO_SECRET_ID'),
        'secret_key': os.getenv('COS_DOP_PRO_SECRET_KEY'),
        'region': os.getenv('COS_DOP_PRO_REGION'),
        'bucket': os.getenv('COS_DOP_PRO_BUCKET')
    },
    'video': {
        'secret_id': os.getenv('COS_VIDEO_SECRET_ID'),
        'secret_key': os.getenv('COS_VIDEO_SECRET_KEY'),
        'region': os.getenv('COS_VIDEO_REGION'),
        'bucket': os.getenv('COS_VIDEO_BUCKET')
    },
    'upload': {
        'secret_id': os.getenv('COS_UPLOAD_SECRET_ID'),
        'secret_key': os.getenv('COS_UPLOAD_SECRET_KEY'),
        'region': os.getenv('COS_UPLOAD_REGION'),
        'bucket': os.getenv('COS_UPLOAD_BUCKET')
    },
    'scrm-pro': {
        'secret_id': os.getenv('COS_SCRM_PRO_SECRET_ID'),
        'secret_key': os.getenv('COS_SCRM_PRO_SECRET_KEY'),
        'region': os.getenv('COS_SCRM_PRO_REGION'),
        'bucket': os.getenv('COS_SCRM_PRO_BUCKET')
    }
}

# MinIO配置 - 请根据您的实际MinIO服务器配置修改
MINIO_CONFIG = {
    'endpoint': os.getenv('MINIO_ENDPOINT'),
    'access_key': os.getenv('MINIO_ACCESS_KEY'),
    'secret_key': os.getenv('MINIO_SECRET_KEY'),
    'secure': os.getenv('MINIO_SECURE', 'False').lower() == 'true', # 从环境变量读取时，需要转换为布尔值
    'bucket_name': os.getenv('MINIO_BUCKET_NAME')
}

# 默认使用的COS配置
DEFAULT_COS_CONFIG = 'video'

# 日志配置
LOG_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s [%(levelname)s] %(message)s',
    'file': 'cos2minio.log'
}

# Excel配置
EXCEL_CONFIG = {
    'url_column': 'url',           # Excel中URL列的名称
    'status_column': 'status',     # 状态列名称（用于记录迁移状态）
    'bucket_column': 'buckets',    # bucket列名称（用于指定MinIO目标bucket）
    'temp_dir': './temp_downloads'  # 临时下载目录
}