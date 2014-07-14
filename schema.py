# -*- coding: utf-8 -*-

from whoosh.fields import *
from whoosh.formats import Positions, Characters
from whoosh.analysis import StandardAnalyzer, Tokenizer, RegexTokenizer, NgramFilter
from whoosh.analysis.filters import Filter, PassFilter
from whoosh.analysis.filters import LowercaseFilter
from whoosh.analysis.filters import StopFilter, STOP_WORDS
from whoosh.analysis.acore import Token
from whoosh.util.text import rcompile
from whoosh.query import And, Or, Term, FuzzyTerm


INDEXDIR = 'var/indexdir'

ENGLISH = rcompile(r"[a-zA-Z0-9_]+(\.?[a-zA-Z0-9_]+)*")

tokenizer = RegexTokenizer(r"[a-zA-Z0-9_]+(\.?[a-zA-Z0-9_]+)*|\w+")
ngram = NgramFilter(minsize=2, maxsize=2)
lower = LowercaseFilter()


class StreamSplitter(object):

    def __init__(self, tokens):
        self.tokens = tokens

        try:
            self.current = self.tokens.next()
            self.end = False
        except StopIteration:
            self.end = True

    def is_en(self):
        return bool(ENGLISH.match(self.current.text))

    def __iter__(self):
        is_en = self.is_en()

        while self.is_en() == is_en:
            yield self.current

            try:
                self.current = self.tokens.next()
            except StopIteration:
                self.end = True
                break


class MixedFilter(Filter):

    __inittypes__ = dict()


    def __init__(self, cn_filter):
        self.cn_filter = cn_filter

    def __call__(self, tokens):
        stream = StreamSplitter(tokens)

        while not stream.end:
            if stream.is_en():
                for t in stream:
                    yield t
            else:
                for t in self.cn_filter(stream):
                    yield t


class Content(FieldType):

    __inittypes__ = dict()

    def __init__(self):
        self.analyzer = tokenizer | lower | MixedFilter(ngram)
        self.search_analyzer = tokenizer | lower
        self.format = Characters(field_boost=1.0)
        self.stored = True
        self.queryor = False
        self.set_sortable(False)


    def self_parsing(self):
        return True


    def parse_query(self, fieldname, qstring, boost=1.0):
        terms = []

        for t in self.search_analyzer(qstring, mode='query'):
            text = t.text

            if ENGLISH.match(text):
                terms.append(Term(fieldname, text))
            elif len(text) == 1:
                terms.append(FuzzyTerm(fieldname, text))
            else:
                bigrams = [Term(fieldname, b.text) for b in ngram([t])]
                terms.append(And(bigrams, boost=boost))

        cls = Or if self.queryor else And
        return cls(terms, boost=boost)


schema = Schema(
    repo = ID(stored=True),
    ref = ID(stored=True),
    filename = ID(stored=True),
    content = Content())
