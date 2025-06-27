# -*- coding: utf-8 -*-
"""
创建带有buckets字段的示例Excel文件
"""
import pandas as pd
import os

def create_sample_excel_with_buckets():
    """创建包含buckets字段的示例Excel文件"""
    
    # 示例数据 - 模拟实际的COS文件URL和对应的bucket配置
    sample_data = {
        'id': [1, 2, 3, 4, 5, 6],
        'name': ['课程视频1', '产品图片1', '用户文档', '系统配置', '营销图片', '数据报表'],
        'url': [
            'https://video-10074222.cos.ap-shanghai.myqcloud.com/course/video/20240124/lesson1.mp4',
            'https://upload-10051630.cos.ap-shanghai.myqcloud.com/2022/products/phone.jpg',
            'https://dop-pro-1251973116.file.myqcloud.com/upload/docs/user-manual.pdf',
            'https://scrm-pro-1251973116.file.myqcloud.com/config/system-config.json',
            'https://upload-10051630.cos.ap-shanghai.myqcloud.com/2023/marketing/banner.png',
            'https://dop-pro-1251973116.file.myqcloud.com/reports/2024/monthly-report.xlsx'
        ],
        'type': ['video', 'image', 'document', 'config', 'image', 'document'],
        'buckets': [
            'video-storage',      # 视频文件专用bucket
            'product-images',     # 产品图片专用bucket  
            'documents',          # 文档专用bucket
            None,                 # 使用默认bucket
            'marketing-assets',   # 营销素材专用bucket
            'reports'             # 报表专用bucket
        ],
        'status': ['pending', 'pending', 'pending', 'pending', 'pending', 'pending']
    }
    
    # 创建DataFrame
    df = pd.DataFrame(sample_data)
    
    # 保存到Excel文件
    excel_path = 'sample_urls_with_buckets.xlsx'
    df.to_excel(excel_path, index=False, engine='openpyxl')
    
    print(f"✅ 创建示例Excel文件: {excel_path}")
    print("\n📋 文件内容预览:")
    print(df.to_string(index=False, max_colwidth=80))
    
    print(f"\n📊 buckets分布:")
    bucket_counts = df['buckets'].value_counts(dropna=False)
    for bucket, count in bucket_counts.items():
        if pd.isna(bucket):
            print(f"  默认bucket: {count} 个文件")
        else:
            print(f"  {bucket}: {count} 个文件")
    
    print(f"\n📁 将创建的bucket列表:")
    unique_buckets = df['buckets'].dropna().unique()
    for bucket in sorted(unique_buckets):
        print(f"  - {bucket}")
    
    print(f"\n🔧 使用方法:")
    print(f"  python cos2minio.py {excel_path}")
    
    return excel_path

def analyze_path_mapping():
    """分析路径映射关系"""
    print("\n🗺️  路径映射分析:")
    print("="*60)
    
    mappings = [
        {
            'original': 'https://video-10074222.cos.ap-shanghai.myqcloud.com/course/video/20240124/lesson1.mp4',
            'bucket': 'video-storage',
            'path': 'course/video/20240124/lesson1.mp4'
        },
        {
            'original': 'https://upload-10051630.cos.ap-shanghai.myqcloud.com/2022/products/phone.jpg',
            'bucket': 'product-images', 
            'path': '2022/products/phone.jpg'
        },
        {
            'original': 'https://dop-pro-1251973116.file.myqcloud.com/upload/docs/user-manual.pdf',
            'bucket': 'documents',
            'path': 'upload/docs/user-manual.pdf'
        }
    ]
    
    for i, mapping in enumerate(mappings, 1):
        print(f"\n{i}. 映射示例:")
        print(f"   原始COS URL: {mapping['original']}")
        print(f"   目标bucket: {mapping['bucket']}")
        print(f"   文件路径: {mapping['path']}")
        print(f"   MinIO路径: {mapping['bucket']}/{mapping['path']}")
        print(f"   访问URL: http://minio-server:9000/{mapping['bucket']}/{mapping['path']}")

if __name__ == "__main__":
    excel_path = create_sample_excel_with_buckets()
    analyze_path_mapping()
    
    print(f"\n🎯 总结:")
    print(f"  ✅ 已创建示例Excel文件: {excel_path}")
    print(f"  ✅ 支持buckets字段指定目标bucket")
    print(f"  ✅ 保持原始URL域名后的完整路径结构")
    print(f"  ✅ 兼容空bucket值（使用默认bucket）")
