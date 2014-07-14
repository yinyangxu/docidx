#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import urllib
import html2text

CORPUS_DIR = 'var/corpusdir'
BASE_URL = 'http://djangobook.py3k.cn/2.0/'
MAX_NUM = 20


os.makedirs(CORPUS_DIR)

for num in xrange(1, MAX_NUM+1):
    if num < 10:
        chapter = 'chapter0{num}'.format(num=str(num))
    else:
        chapter = 'chapter{num}'.format(num=str(num))

    url = BASE_URL + chapter

    f = urllib.urlopen(url)
    text = html2text.html2text(f.read().decode('UTF-8'))

    print 'Downloading {0}'.format(chapter)

    with open(os.path.join(CORPUS_DIR, chapter), 'w') as f:
        f.write(text.encode('UTF-8'))
