# -*- coding: utf-8 -*-
"""
创建示例Excel文件
"""
import pandas as pd
import os


def create_sample_excel(output_path='sample_urls.xlsx'):
    """创建示例Excel文件"""
    
    # 示例URL数据
    sample_data = [
        {
            'id': 1,
            'name': '示例视频1',
            'url': 'https://video-10074222.cos.ap-shanghai.myqcloud.com/course/video/20240124/sample1.mp4',
            'type': 'video',
            'status': 'pending'
        },
        {
            'id': 2,
            'name': '示例图片1',
            'url': 'https://video-10074222.cos.ap-shanghai.myqcloud.com/images/upload/20240125/sample1.jpg',
            'type': 'image',
            'status': 'pending'
        },
        {
            'id': 3,
            'name': '示例文档1',
            'url': 'https://video-10074222.cos.ap-shanghai.myqcloud.com/documents/pdf/sample1.pdf',
            'type': 'document',
            'status': 'pending'
        },
        {
            'id': 4,
            'name': '示例音频1',
            'url': 'https://video-10074222.cos.ap-shanghai.myqcloud.com/audio/mp3/sample1.mp3',
            'type': 'audio',
            'status': 'pending'
        },
        {
            'id': 5,
            'name': '示例视频2',
            'url': 'https://video-10074222.cos.ap-shanghai.myqcloud.com/course/video/20240124/6ef0339f03264781a5710f32daf0476b/43dfbb1ccd3142fab09c5564a61298d2/sample2.mp4',
            'type': 'video',
            'status': 'pending'
        }
    ]
    
    # 创建DataFrame
    df = pd.DataFrame(sample_data)
    
    # 保存为Excel文件
    df.to_excel(output_path, index=False, engine='openpyxl')
    print(f"示例Excel文件已创建: {output_path}")
    
    return output_path


if __name__ == "__main__":
    create_sample_excel()
