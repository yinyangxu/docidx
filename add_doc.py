#!/usr/bin/python

import os
import sys
from ConfigParser import SafeConfigParser

import psycopg2

from whoosh.index import exists_in, create_in, open_dir
from dulwich.errors import NotGitRepository

from dulwich.repo import Repo
from dulwich.objects import Tag, Tree

from schema import INDEXDIR, schema


parser = SafeConfigParser()
parser.read('docidx.conf')

DATABASE = parser.get('db', 'dbname')
HOST = parser.get('db', 'host')
USER = parser.get('db', 'user')
PASSWORD = parser.get('db', 'password')

BASE_PATH = '/srv/gitlab/repositories'


os.makedirs(INDEXDIR)

if not exists_in(INDEXDIR):
    create_in(INDEXDIR, schema=schema)


def get_gitlab():
    return psycopg2.connect(
        database=DATABASE,
        host=HOST,
        user=USER,
        password=PASSWORD)


def build_repo_path(user_repo):
    repo_path = os.path.join(BASE_PATH, user_repo)
    repo_path += '.git'

    return repo_path


def get_entry(repo, tree, stack=()):
    for entry in tree.items():
        try:
            obj = repo.get_object(entry.sha)
        except KeyError:
            err_msg = 'Bad entry at {0}: {1}'.format(repo, entry)
            print >> sys.stderr, err_msg

        if isinstance(obj, Tree):
            for entry in get_entry(repo, obj, stack+(entry.path,)):
                yield entry
        else:
            if entry.path.endswith('.md'):
                yield '/'.join(stack), entry


def add_doc(namespace_path, project_path):
    user_repo = os.path.join(namespace_path, project_path)
    repo_path = build_repo_path(user_repo)

    if not os.path.exists(repo_path):
        err_msg = "Repo path {0} not exist".format(repo_path)
        print >> sys.stderr, err_msg
        return

    ix = open_dir(INDEXDIR)
    writer = ix.writer()

    try:
        repo = Repo(repo_path)
    except NotGitRepository:
        err_msg = "No git repository was found at {0}".format(repo_path)
        print >> sys.stderr, err_msg
        return

    try:
        refs = repo.get_refs()

        for ref in refs.keys():
            if ref.startswith('refs/heads') or ref.startswith('refs/tags'):
                obj = repo.get_object(refs[ref])

                if isinstance(obj, Tag):
                    commit = repo[obj.object[1]]
                else:
                    commit = obj

                tree = repo[commit.tree]

                for path, entry in get_entry(repo, tree):
                    filename = os.path.join(ref.rsplit('/')[2],
                                            path, entry.path)
                    blob = repo[entry.sha]

                    writer.add_document(
                        repo=user_repo.decode('UTF-8', 'ignore'),
                        ref=ref.decode('UTF-8', 'ignore'),
                        filename=filename.decode('UTF-8', 'ignore'),
                        content=blob.data.decode('UTF-8', 'ignore'))

        writer.commit()
    except:
        writer.cancel()
        raise


def main():
    conn = get_gitlab()
    cur = conn.cursor()
    cur.execute("SELECT n.path, p.path FROM namespaces as n, projects as p WHERE n.id = p.namespace_id AND p.public = true")
    data = cur.fetchall()

    cur.close()
    conn.close()

    for item in data:
        add_doc(*item)


if __name__ == '__main__':
    main()
