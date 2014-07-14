from whoosh.index import open_dir

from whoosh.highlight import ContextFragmenter
from whoosh.qparser import QueryParser
from schema import INDEXDIR, schema

from flask import Flask, request, render_template
application = app = Flask(__name__)


ix = open_dir(INDEXDIR)
parser = QueryParser("content", ix.schema)

PAGELEN = 5


def wrap_tokens(tokens):
    last = None

    for t in tokens:
        if not t.matched:
            if last is not None:
                yield last
            last = None
            yield t
            continue

        if last is None:
            last = t.copy()
            continue

        if t.startchar < last.endchar:
            last.text += t.text[last.endchar-t.startchar:]
            last.endchar = t.endchar

        else:
            yield last
            last = t.copy()

    if last is not None:
        yield last


class MyFragmenter(ContextFragmenter):

    def fragment_tokens(self, text, tokens):
        return ContextFragmenter.fragment_tokens(self, text, wrap_tokens(tokens))


def get_page_list(cur, total):
    low = max(1, cur-5)
    high = min(total, cur+5)

    page_list = [(p, str(p)) for p in range(low, high+1)]

    if cur > low:
        page_list = [(cur-1, "prev")] + page_list

    if high > cur:
        page_list = page_list + [(cur+1, "next")]

    return page_list


@app.route('/')
def search():
    term = request.args.get('q', '')
    page = request.args.get('p', '1')

    try:
        page = int(page)
    except ValueError:
        page = 1

    if not term:
        return render_template("search.html")

    with ix.searcher() as searcher:
        query = parser.parse(term)
        page = searcher.search_page(query, page, pagelen=PAGELEN, terms=True)

        page.results.fragmenter = MyFragmenter()

        total = page.results.estimated_min_length()
        pages = get_page_list(page.pagenum, total/PAGELEN + bool(total%PAGELEN))

        return render_template(
            "search.html",
            term = term,
            page = page,
            pagenum = page.pagenum,
            pages = pages,
            results = page.results)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9090, debug=True, use_reloader=False)
