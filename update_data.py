# -*- coding: utf-8 -*-
"""
定时抓取源站的 3d_asc.txt，生成 3d_data.js 供页面读取。

3d_data.js 的内容是：
    window.__FC3D_TEXT__ = "期号 日期 百 十 个 ...\n..."
即把同一份 17 列纯文本包进一个 JS 字符串变量。页面用 fetch 拿到文本后
会拆开这层包装再解析，因此文件放在 GitHub raw 上即可被本地 HTML 读到。

由 .github/workflows/update.yml 定时调用，只用 Python 标准库。
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
    # 校验期号递增，避免写坏数据
    for i in range(1, len(rows)):
        if int(rows[i].split()[0]) <= int(rows[i - 1].split()[0]):
            raise RuntimeError('期号顺序异常，停止写入')

    with open('3d_data.js', 'w', encoding='utf-8') as f:
        f.write('window.__FC3D_TEXT__ = ' + json.dumps(clean, ensure_ascii=False) + ';\n')

    print('已生成 3d_data.js')
    print('期数：%d' % len(rows))
    print('最新：%s' % rows[-1][:60])


if __name__ == '__main__':
    main()
