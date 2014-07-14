#!/usr/bin/python

import os

from whoosh.index import exists_in, create_in, open_dir

from schema import INDEXDIR, schema


CORPUS_DIR = 'var/corpusdir'


os.makedirs(INDEXDIR)

if not exists_in(INDEXDIR):
    create_in(INDEXDIR, schema=schema)


def add_doc(repo, head):
    ix = open_dir(INDEXDIR)
    writer = ix.writer()

    try:
        for filename in os.listdir(CORPUS_DIR):
            with open(os.path.join(CORPUS_DIR, filename)) as f:
                content = f.read()

            writer.add_document(
                repo=repo.decode("UTF-8"),
                ref=head.decode("UTF-8"),
                filename=filename.decode("UTF-8"),
                content=content.decode("UTF-8"))

        writer.commit()
    except:
        writer.cancel()
        raise


if __name__ == '__main__':
    add_doc('project', 'master')
