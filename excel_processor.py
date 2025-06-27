# -*- coding: utf-8 -*-
"""
Excel处理模块 - 读取Excel文件中的URL链接
"""
import pandas as pd
import logging
from urllib.parse import urlparse
import os


class ExcelProcessor:
    """Excel处理器"""
    
    def __init__(self, excel_path, url_column='url', status_column='status', bucket_column='buckets'):
        """
        初始化Excel处理器
        
        Args:
            excel_path: Excel文件路径
            url_column: URL列名
            status_column: 状态列名
            bucket_column: 存储桶列名
        """
        self.excel_path = excel_path
        self.url_column = url_column
        self.status_column = status_column
        self.bucket_column = bucket_column
        self.df = None
        
    def read_excel(self):
        """读取Excel文件"""
        try:
            if not os.path.exists(self.excel_path):
                raise FileNotFoundError(f"Excel文件不存在: {self.excel_path}")
                
            # 支持多种Excel格式
            if self.excel_path.endswith('.xlsx'):
                self.df = pd.read_excel(self.excel_path, engine='openpyxl')
            elif self.excel_path.endswith('.xls'):
                self.df = pd.read_excel(self.excel_path, engine='xlrd')
            else:
                raise ValueError("不支持的文件格式，请使用.xlsx或.xls文件")
                
            # 检查必要的列是否存在
            if self.url_column not in self.df.columns:
                raise ValueError(f"Excel文件中未找到URL列: {self.url_column}")
                
            # 如果状态列不存在，创建它
            if self.status_column not in self.df.columns:
                self.df[self.status_column] = 'pending'
                
            # 检查bucket列是否存在
            if self.bucket_column not in self.df.columns:
                logging.warning(f"Excel文件中未找到bucket列: {self.bucket_column}，将使用默认bucket")
                self.df[self.bucket_column] = None  # 使用None表示使用默认bucket
                
            logging.info(f"成功读取Excel文件: {self.excel_path}, 共{len(self.df)}行数据")
            return True
            
        except Exception as e:
            logging.error(f"读取Excel文件失败: {e}")
            return False
    
    def get_urls(self, status_filter=None):
        """
        获取URL列表
        
        Args:
            status_filter: 状态过滤条件，如['pending', 'failed']
            
        Returns:
            list: URL列表，每个元素为(index, url, bucket)元组
        """
        if self.df is None:
            logging.error("请先调用read_excel()方法读取Excel文件")
            return []
            
        df_filtered = self.df.copy()
        
        # 过滤空URL
        df_filtered = df_filtered[df_filtered[self.url_column].notna()]
        df_filtered = df_filtered[df_filtered[self.url_column] != '']
        
        # 状态过滤
        if status_filter:
            df_filtered = df_filtered[df_filtered[self.status_column].isin(status_filter)]
            
        urls = []
        for index, row in df_filtered.iterrows():
            url = row[self.url_column]
            # 处理bucket值，将NaN转换为None
            bucket = row.get(self.bucket_column, None) if self.bucket_column in row else None
            if pd.isna(bucket):
                bucket = None
            if self.is_valid_url(url):
                urls.append((index, url, bucket))
            else:
                logging.warning(f"无效的URL (行{index+2}): {url}")
                
        logging.info(f"获取到{len(urls)}个有效URL")
        return urls
    
    def is_valid_url(self, url):
        """检查URL是否有效"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def extract_cos_path(self, url):
        """
        从COS URL中提取文件路径
        
        Args:
            url: COS完整URL
            
        Returns:
            str: 文件路径（去除域名部分）
        """
        try:
            parsed_url = urlparse(url)
            # 去除开头的斜杠
            path = parsed_url.path.lstrip('/')
            return path
        except Exception as e:
            logging.error(f"解析URL路径失败: {url}, 错误: {e}")
            return None
    
    def update_status(self, index, status, error_msg=None):
        """
        更新指定行的状态
        
        Args:
            index: 行索引
            status: 新状态
            error_msg: 错误信息（可选）
        """
        if self.df is None:
            return
            
        try:
            self.df.at[index, self.status_column] = status
            if error_msg and 'error_msg' in self.df.columns:
                self.df.at[index, 'error_msg'] = error_msg
        except Exception as e:
            logging.error(f"更新状态失败: {e}")
    
    def save_excel(self, output_path=None):
        """
        保存Excel文件
        
        Args:
            output_path: 输出路径，如果为None则覆盖原文件
        """
        if self.df is None:
            return False
            
        try:
            save_path = output_path or self.excel_path
            self.df.to_excel(save_path, index=False, engine='openpyxl')
            logging.info(f"Excel文件已保存: {save_path}")
            return True
        except Exception as e:
            logging.error(f"保存Excel文件失败: {e}")
            return False
    
    def get_statistics(self):
        """获取处理统计信息"""
        if self.df is None:
            return {}
            
        stats = {
            'total': len(self.df),
            'pending': len(self.df[self.df[self.status_column] == 'pending']),
            'success': len(self.df[self.df[self.status_column] == 'success']),
            'failed': len(self.df[self.df[self.status_column] == 'failed']),
            'processing': len(self.df[self.df[self.status_column] == 'processing'])
        }
        return stats
