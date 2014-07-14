#!/usr/bin/env bash

rm -fr var/indexdir
rm -fr var/corpusdir
python crawler.py
python add_doc_test.py
