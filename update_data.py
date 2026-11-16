# -*- coding: utf-8 -*-
"""
抓取 3d_asc.txt，生成两个文件供页面读取：
  3d_asc.txt  —— 纯文本原样数据（raw / jsDelivr 带 CORS，页面可直接 fetch）
  3d_data.js  —— 包成 JS 变量的同一份数据（<script src> 加载，完全不受 CORS 限制）
由 .github/workflows/update.yml 定时调用，无需任何第三方库。
"""
import re
import json
import urllib.request

UPSTREAMS = [
    'https://data.17500.cn/3d_asc.txt',
    'http://data.17500.cn/3d_asc.txt',
]
HEADERS = {
    # 源站对裸请求会返回 429，带常规浏览器标识才能稳定拿到全量数据
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://data.17500.cn/',
    'Accept': 'text/plain,*/*',
}
PAT = re.compile(r'^\d{7}\s+\d{4}-\d{2}-\d{2}\s')


def fetch():
    last = None
    for url in UPSTREAMS:
        for attempt in range(2):
            try:
                req = urllib.request.Request(url, headers=HEADERS)
                with urllib.request.urlopen(req, timeout=30) as r:
                    txt = r.read().decode('utf-8', errors='replace')
                rows = [l.strip() for l in txt.splitlines()
                        if PAT.match(l.strip()) and len(l.strip().split()) == 17]
                if len(rows) < 100:
                    raise RuntimeError('有效数据行过少：%d' % len(rows))
                return '\n'.join(rows) + '\n', rows
            except Exception as e:
                last = e
                print('  %s 第 %d 次失败：%s' % (url, attempt + 1, e))
    raise RuntimeError('全部上游抓取失败：%s' % last)


def main():
    clean, rows = fetch()
    # 校验期号递增
    for i in range(1, len(rows)):
        if int(rows[i].split()[0]) <= int(rows[i - 1].split()[0]):
            raise RuntimeError('期号顺序异常，停止写入')

    with open('3d_asc.txt', 'w', encoding='utf-8', newline='\n') as f:
        f.write(clean)
    with open('3d_data.js', 'w', encoding='utf-8') as f:
        f.write('window.__FC3D_TEXT__ = ' + json.dumps(clean, ensure_ascii=False) + ';\n')

    print('已生成 3d_asc.txt / 3d_data.js')
    print('期数：%d' % len(rows))
    print('最新：%s' % rows[-1][:60])


if __name__ == '__main__':
    main()
