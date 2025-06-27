# -*- coding: utf-8 -*-
"""
COS到MinIO迁移工具主程序
"""
import os
import sys
import logging
import argparse
import tempfile
import shutil
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import LOG_CONFIG, EXCEL_CONFIG
from excel_processor import ExcelProcessor
from cos_downloader import COSDownloader
from minio_uploader import MinIOUploader


def setup_logging():
    """设置日志系统"""
    logging.basicConfig(
        level=getattr(logging, LOG_CONFIG['level']),
        format=LOG_CONFIG['format'],
        handlers=[
            logging.FileHandler(LOG_CONFIG['file'], encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


class COS2MinIOMigrator:
    """COS到MinIO迁移器"""
    
    def __init__(self, excel_path, cos_config_name=None, minio_config=None, 
                 temp_dir=None, max_workers=5):
        """
        初始化迁移器
        
        Args:
            excel_path: Excel文件路径
            cos_config_name: COS配置名称
            minio_config: MinIO配置
            temp_dir: 临时目录
            max_workers: 最大并发数
        """
        self.excel_path = excel_path
        self.temp_dir = temp_dir or EXCEL_CONFIG['temp_dir']
        self.max_workers = max_workers
        
        # 初始化各组件
        self.excel_processor = ExcelProcessor(
            excel_path,
            url_column=EXCEL_CONFIG['url_column'],
            status_column=EXCEL_CONFIG['status_column'],
            bucket_column=EXCEL_CONFIG['bucket_column']
        )
        
        self.cos_downloader = COSDownloader(cos_config_name)
        self.minio_uploader = MinIOUploader(minio_config)
        
        # 统计信息
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
        
        # 确保临时目录存在
        os.makedirs(self.temp_dir, exist_ok=True)
        
    def migrate_single_file(self, index, url, bucket=None):
        """
        迁移单个文件
        
        Args:
            index: Excel行索引
            url: COS文件URL
            bucket: 目标MinIO bucket名称，如果为None则使用默认bucket
            
        Returns:
            dict: 迁移结果
        """
        result = {
            'index': index,
            'url': url,
            'bucket': bucket,
            'success': False,
            'error': None,
            'cos_path': None,
            'local_path': None,
            'minio_path': None
        }
        
        try:
            # 更新状态为处理中
            self.excel_processor.update_status(index, 'processing')
            
            # 自动检测COS源端配置，优先使用Excel中的bucket作为hint
            if not self.cos_downloader.auto_detect_bucket_config(url, bucket_hint=bucket):
                raise ValueError(f"无法检测COS源存储桶配置: {url}")
            
            # 从URL提取COS路径
            cos_path = self.excel_processor.extract_cos_path(url)
            if not cos_path:
                raise ValueError(f"无法从URL提取有效路径: {url}")
            
            result['cos_path'] = cos_path
            
            # 检查COS文件是否存在
            if not self.cos_downloader.check_file_exists(cos_path):
                # 文件不存在时，运行调试功能来查看存储桶中的相似文件
                logging.warning(f"COS文件不存在，运行调试检查: {cos_path}")
                self.cos_downloader.debug_list_similar_files(cos_path)
                raise ValueError(f"COS文件不存在: {cos_path}")
            
            # 确定目标MinIO bucket（使用Excel中指定的bucket或默认bucket）
            target_bucket = bucket or self.minio_uploader.bucket_name
            
            # 检查MinIO中是否已存在该文件
            if self.minio_uploader.check_object_exists(cos_path, target_bucket):
                logging.info(f"文件已存在于MinIO，跳过: {target_bucket}/{cos_path}")
                result['success'] = True
                result['minio_path'] = cos_path
                result['bucket'] = target_bucket
                self.excel_processor.update_status(index, 'success')
                self.stats['skipped'] += 1
                return result
            
            # 下载文件到临时目录
            local_path = self.cos_downloader.download_file(
                cos_path, 
                temp_dir=self.temp_dir
            )
            
            if not local_path:
                raise ValueError(f"下载文件失败: {cos_path}")
            
            result['local_path'] = local_path
            
            # 上传到MinIO（使用Excel中指定的bucket）
            upload_success = self.minio_uploader.upload_file(
                local_path, 
                cos_path,  # 使用原始COS路径作为MinIO对象名
                bucket_name=target_bucket  # 使用Excel中指定的bucket
            )
            
            if not upload_success:
                raise ValueError(f"上传到MinIO失败: {cos_path}")
            
            result['minio_path'] = cos_path
            result['bucket'] = target_bucket
            result['success'] = True
            
            # 更新状态
            self.excel_processor.update_status(index, 'success')
            self.stats['success'] += 1
            
            logging.info(f"迁移成功: {cos_path} -> {target_bucket}/{cos_path}")
            
        except Exception as e:
            error_msg = str(e)
            result['error'] = error_msg
            
            # 更新状态
            self.excel_processor.update_status(index, 'failed', error_msg)
            self.stats['failed'] += 1
            
            logging.error(f"迁移失败 (行{index+2}): {url}, 错误: {error_msg}")
            
        finally:
            # 清理临时文件
            if result.get('local_path') and os.path.exists(result['local_path']):
                try:
                    os.remove(result['local_path'])
                except Exception as e:
                    logging.warning(f"清理临时文件失败: {result['local_path']}, 错误: {e}")
        
        return result
    
    def migrate_all(self, status_filter=None, resume=False):
        """
        迁移所有文件
        
        Args:
            status_filter: 状态过滤器
            resume: 是否恢复之前的迁移
        """
        # 读取Excel文件
        if not self.excel_processor.read_excel():
            logging.error("读取Excel文件失败")
            return False
        
        # 获取需要处理的URL
        if resume:
            # 恢复模式：只处理pending和failed状态的文件
            urls = self.excel_processor.get_urls(['pending', 'failed'])
        else:
            # 普通模式：根据status_filter获取URL
            urls = self.excel_processor.get_urls(status_filter)
        
        if not urls:
            logging.info("没有需要处理的文件")
            return True
        
        self.stats['total'] = len(urls)
        logging.info(f"开始迁移，共{len(urls)}个文件，最大并发数: {self.max_workers}")
        
        # 并发处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交任务
            future_to_url = {
                executor.submit(self.migrate_single_file, index, url, bucket): (index, url, bucket)
                for index, url, bucket in urls
            }
            
            # 处理完成的任务
            for future in as_completed(future_to_url):
                index, url, bucket = future_to_url[future]
                try:
                    result = future.result()
                    if result['success']:
                        logging.info(f"✓ 完成 ({self.stats['success'] + self.stats['skipped']}/{self.stats['total']}): {result['cos_path']}")
                    else:
                        logging.error(f"✗ 失败 ({self.stats['failed']}/{self.stats['total']}): {url}")
                except Exception as e:
                    logging.error(f"处理任务异常: {url}, 错误: {e}")
                    self.stats['failed'] += 1
        
        # 保存Excel文件
        self.excel_processor.save_excel()
        
        # 打印统计信息
        self.print_statistics()
        
        return self.stats['failed'] == 0
    
    def print_statistics(self):
        """打印统计信息"""
        total = self.stats['total']
        success = self.stats['success']
        failed = self.stats['failed']
        skipped = self.stats['skipped']
        
        logging.info("=" * 50)
        logging.info("迁移完成统计:")
        logging.info(f"总计: {total}")
        logging.info(f"成功: {success}")
        logging.info(f"失败: {failed}")
        logging.info(f"跳过: {skipped}")
        logging.info(f"成功率: {(success + skipped) / total * 100:.2f}%" if total > 0 else "0%")
        logging.info("=" * 50)
    
    def cleanup(self):
        """清理资源"""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logging.info(f"清理临时目录: {self.temp_dir}")
        except Exception as e:
            logging.warning(f"清理临时目录失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='COS到MinIO文件迁移工具')
    parser.add_argument('excel_path', help='Excel文件路径')
    parser.add_argument('--cos-config', default=None, help='COS配置名称')
    parser.add_argument('--temp-dir', default=None, help='临时目录路径')
    parser.add_argument('--max-workers', type=int, default=5, help='最大并发数')
    parser.add_argument('--resume', action='store_true', help='恢复之前的迁移')
    parser.add_argument('--status-filter', nargs='+', default=['pending'], 
                       help='状态过滤器 (pending, failed, success)')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging()
    
    # 检查Excel文件是否存在
    if not os.path.exists(args.excel_path):
        logging.error(f"Excel文件不存在: {args.excel_path}")
        return 1
    
    # 创建迁移器
    try:
        migrator = COS2MinIOMigrator(
            excel_path=args.excel_path,
            cos_config_name=args.cos_config,
            temp_dir=args.temp_dir,
            max_workers=args.max_workers
        )
        
        # 开始迁移
        success = migrator.migrate_all(
            status_filter=args.status_filter if not args.resume else None,
            resume=args.resume
        )
        
        return 0 if success else 1
        
    except Exception as e:
        logging.error(f"程序执行失败: {e}")
        return 1
    finally:
        # 清理资源
        try:
            migrator.cleanup()
        except:
            pass


if __name__ == "__main__":
    exit(main())
