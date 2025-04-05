# 数据爬取模块
# filename: crawler/base_crawler.py

import requests
import time
import random
from bs4 import BeautifulSoup
import logging
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('crawler')

class BaseCrawler(ABC):
    """爬虫基类，定义通用爬虫接口"""
    
    def __init__(self, headers=None, proxies=None, retry_times=3, retry_interval=5):
        """初始化爬虫
        
        Args:
            headers: 请求头
            proxies: 代理IP
            retry_times: 重试次数
            retry_interval: 重试间隔（秒）
        """
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive'
        }
        self.proxies = proxies
        self.retry_times = retry_times
        self.retry_interval = retry_interval
        self.session = requests.Session()
    
    def _get_random_headers(self):
        """获取随机请求头，避免被反爬"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0'
        ]
        headers = self.headers.copy()
        headers['User-Agent'] = random.choice(user_agents)
        return headers
    
    def _request(self, url, method='GET', params=None, data=None, json_data=None, allow_redirects=True):
        """发送HTTP请求，带重试机制
        
        Args:
            url: 请求URL
            method: 请求方法，默认GET
            params: URL参数
            data: 表单数据
            json_data: JSON数据
            allow_redirects: 是否允许重定向
            
        Returns:
            Response对象
        """
        for i in range(self.retry_times):
            try:
                # 随机延迟，避免请求过于频繁
                time.sleep(random.uniform(0.5, 2.0))
                
                # 发送请求
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=self._get_random_headers(),
                    params=params,
                    data=data,
                    json=json_data,
                    proxies=self.proxies,
                    timeout=10,
                    allow_redirects=allow_redirects
                )
                
                # 检查响应状态
                if response.status_code == 200:
                    return response
                else:
                    logger.warning(f"请求失败，状态码: {response.status_code}，URL: {url}，重试中...")
            
            except Exception as e:
                logger.error(f"请求异常: {str(e)}，URL: {url}，重试中...")
            
            # 重试前等待
            time.sleep(self.retry_interval * (i + 1))
        
        logger.error(f"请求失败，已达到最大重试次数，URL: {url}")
        return None
    
    def get_html(self, url, params=None):
        """获取HTML内容
        
        Args:
            url: 请求URL
            params: URL参数
            
        Returns:
            BeautifulSoup对象
        """
        response = self._request(url, params=params)
        if response:
            return BeautifulSoup(response.text, 'html.parser')
        return None
    
    def get_json(self, url, params=None):
        """获取JSON数据
        
        Args:
            url: 请求URL
            params: URL参数
            
        Returns:
            JSON数据
        """
        response = self._request(url, params=params)
        if response:
            try:
                return response.json()
            except:
                logger.error(f"JSON解析失败，URL: {url}")
        return None
    
    def save_data(self, data, filename):
        """保存数据到文件
        
        Args:
            data: 要保存的数据
            filename: 文件名
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"数据已保存到: {filename}")
        except Exception as e:
            logger.error(f"保存数据失败: {str(e)}")
    
    @abstractmethod
    def crawl_product_list(self, keyword, page=1, category=None):
        """爬取产品列表
        
        Args:
            keyword: 搜索关键词
            page: 页码
            category: 产品类别
            
        Returns:
            产品列表
        """
        pass
    
    @abstractmethod
    def crawl_product_detail(self, product_id):
        """爬取产品详情
        
        Args:
            product_id: 产品ID
            
        Returns:
            产品详情
        """
        pass
    
    @abstractmethod
    def crawl_product_reviews(self, product_id, page=1):
        """爬取产品评价
        
        Args:
            product_id: 产品ID
            page: 页码
            
        Returns:
            评价列表
        """
        pass
    
    @abstractmethod
    def crawl_product_price_history(self, product_id):
        """爬取产品价格历史
        
        Args:
            product_id: 产品ID
            
        Returns:
            价格历史
        """
        pass
    
    @abstractmethod
    def crawl_product_discounts(self, product_id):
        """爬取产品优惠信息
        
        Args:
            product_id: 产品ID
            
        Returns:
            优惠信息
        """
        pass
