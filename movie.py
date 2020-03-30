# -*- coding:utf-8 -*-
"""
Company:SELLMORE
Author:Pengjinfu
Language:Python3.7
Date:2020.3.30
"""
import os

import aiohttp
import asyncio
from fake_useragent import UserAgent
from tqdm import tqdm
from lxml import etree


class SXTMovie():
    """
    1.请求目标网址，获取视频分类，创建分类目录，获取视频标题，视频地址
    2.请求视频获取视频长度
    3.根据视频长度下载视频
    """

    def __init__(self):
        self.url = 'https://www.bjsxt.com/down/11812.html'
        self.headers = {'user-agent': UserAgent().random}

    async def handle_request(self, url, flag, session=None, filepath=None, headers=None, du=None):
        if flag == 1:
            print('一般请求处理！')
            async with aiohttp.ClientSession() as sessions:
                async with sessions.get(url, headers=self.headers, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        return html

        elif flag == 2:
            if headers:
                async with session.get(url, headers=headers) as response:
                    with open(filepath, 'ab') as file:
                        while True:
                            chunk = await response.content.read(2048)
                            if not chunk:
                                break
                            file.write(chunk)
                            du.update(2048)
                    du.close()
            else:
                async with session.get(url, headers=self.headers, timeout=5) as response:
                    return response

    async def down_movie(self, url, filepath):
        async with aiohttp.ClientSession() as session:
            # 获取视频响应
            response = await self.handle_request(url, 2, session=session, filepath=filepath)
            # 获取视频大小
            file_size = int(response.headers['content-length'])
            print(f"获取{filepath}视频总长度:{file_size}")
            if os.path.exists(filepath):
                first_byte = os.path.getsize(filepath)
            else:
                first_byte = 0
            if first_byte >= file_size:
                return file_size
            header = {"Range": f"bytes={first_byte}-{file_size}"}
            du = tqdm(
                total=file_size, initial=first_byte,
                unit='B', unit_scale=True, desc=filepath)
            await self.handle_request(url, 2, session=session, filepath=filepath, headers=header, du=du)

    async def mkdir(self, path):
        if os.path.exists(path):
            pass
        else:
            os.mkdir(path)

    async def get_info(self):
        html = await self.handle_request(self.url, 1)
        res = etree.HTML(html)
        infos = res.xpath('//div[@class="dlinfo dlinfo2"]/div[@class="div_xlbtn"]')

        for i in range(1, 11):
            path = infos[i].xpath('./p/text()')
            url_tiltes = infos[i].xpath('./a/@onclick')
            root_path = path[0].replace('\r', '').replace('\n', '').replace('\t', '').replace(' ', '')
            await self.mkdir(root_path)
            for info in url_tiltes:
                url_tilte = info.replace("plays('", "").replace("');", "").replace("'", "").split(',')
                url = url_tilte[0]
                title = url_tilte[2]
                path = './' + root_path + '/' + title
                await self.down_movie(url,path)

    def run(self):
        task = [asyncio.ensure_future(self.get_info())]
        return task


if __name__ == '__main__':
    movie = SXTMovie()
    task = movie.run()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(task))
    loop.close()
