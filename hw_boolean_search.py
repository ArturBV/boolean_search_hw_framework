#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import codecs
import sys



class Index:
    def __init__(self, index_file):
        """
        index_file format
        docs splitted by rows: -- 1 row -- 1 doc
        row consists of 3 fields separated by tab:
        doc_num \t title \t doc text
        tokens (words) in title and document text splitted with space.
        """
        # Index structure:
        # self.index = {
        #     term1: { doc_i1, doc_i2, ... },
        #     term2: { doc_j1, doc_j2, ... },
        #     },
        #     ...
        # }
        self.reverse_index = dict() # dict[term] -> set of docs
        self.build_index(index_file)

    def build_index(self, index_file):
        with codecs.open(index_file, mode='r', encoding='utf-8') as index_fh:
            for line in index_fh:
                fields = line.rstrip('\n').split('\t')
                doc_num = int(fields[0][1:])
                
                title = fields[1]
                text = fields[2]

                # TODO: what about give title token more priority?
                # Process title.
                for term in title.split():
                    if term not in self.reverse_index:
                        self.reverse_index[term] = set()
                    self.reverse_index[term].add(doc_num)
                # Process text.
                for term in text.split():
                    if term not in self.reverse_index:
                        self.reverse_index[term] = set()
                    self.reverse_index[term].add(doc_num)


class Stack:
    def __init__(self):
        self.stack = []
        
    def push(self, elem):
        self.stack.append(elem)
        
    def pop(self):
        return self.stack.pop()
    
    def is_empty(self):
        return len(self.stack) == 0
    
    def top(self):
        return self.stack[-1]
    
    def __str__(self):
        return str(self.stack)

class QueryNode:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None

class QueryTree:
    def __init__(self, qid, query):
        # TODO: parse query and create query tree
        """
        query format:
        1 symbol | defines opeation OR
        2 space(blank) defines operation AND
        3 parentheses () highlight operations group (mostly OR)
        4 blank between operations OR considered as operaton AND applied to words(tokens) bounded with symbols | or )

        Example for 4:

        (ВЫХОДНОЙ|НЕРАБОЧИЙ ДЕНЬ) considered as (ВЫХОДНОЙ|(НЕРАБОЧИЙ&ДЕНЬ))
        (ВЫХОДНОЙ|НЕРАБОЧИЙ (1|ПЕРВЫЙ) ДЕНЬ) considered as (ВЫХОДНОЙ|(НЕРАБОЧИЙ&(1|ПЕРВЫЙ)&ДЕНЬ))
        """
        self.qid = qid
        self.stack = Stack()
        self.postfix = list()
        self.delimiters = {'&', '|', '(', ')'}
        self.postfix_result = self._QueryToPostfix(query)
        # self.root = self._createTree()
    
    def _isDelimiter(self, element):
        return element in self.delimiters
    
    def _getEvaluatedPostfix(self):
        return " ".join(self.postfix_result)

    def _QueryToPostfix(self, expr):
        """
        expr is string that consists of operands and operators
        operands: lonely symbols a-z
        operators: a b - concatenation, a|b - union
        the precedence from lowest to highest:  union, concatenation
        
        in input expr concatenations marks as blan(space),
        in postfix notation concatenations marks as &
        return postfix notation of expr
        """
        expr = expr.replace(" ", "&")
        for delim in self.delimiters:
            expr = expr.replace(delim, ' ' + delim + ' ')
        expr = expr.split()
        # print(expr)
        precedence = {'|': 1, '&': 2, '*': 3}
        for i in range(len(expr)):
            if expr[i] == '(':
                self.stack.push('(')
            if expr[i] == ')':
                while self.stack.top() != '(':
                    self.postfix.append(self.stack.pop())
                self.stack.pop()
            if not self._isDelimiter(expr[i]):
                self.postfix.append(expr[i])
            if expr[i] in precedence:
                while not self.stack.is_empty() and self.stack.top() != '(' and precedence[self.stack.top()] >= precedence[expr[i]]:
                    self.postfix.append(self.stack.pop())
                self.stack.push(expr[i])
        while not self.stack.is_empty():
            self.postfix.append(self.stack.pop())
        return self.postfix

    def search(self, index):
        # TODO: lookup query terms in the index and implement boolean search logic
        self.stack = Stack()
        for term in self.postfix_result:
            if term not in self.delimiters:
                if term in index.reverse_index:
                    self.stack.push(index.reverse_index[term])
                else:
                    self.stack.push(set())
            else:
                if term == '&':
                    self.stack.push(self.stack.pop() & self.stack.pop())
                elif term == '|':
                    self.stack.push(self.stack.pop() | self.stack.pop())
        # set of doc numbers
        return self.qid, self.stack.pop()


class SearchResults:
    def __init__(self):
        self.results = dict()
    
    def add(self, found):
        # TODO: add next query's results
        qid, docs = found
        self.results[qid] = docs

    def print_submission(self, objects_file, submission_file):
        # TODO: generate submission file
        with codecs.open(objects_file, mode='r', encoding='utf-8') as objects_fh:
            with codecs.open(submission_file, mode='w', encoding='utf-8') as submission_fh:
                submission_fh.write("ObjectId,Relevance\n")

                objects = objects_fh.readline() # skip header
                objects = objects_fh.readline()
                # print(int(objects[2]))
                
                while objects:
                    objId, qId, docId = objects.rstrip('\n').split(',')
                    if int(qId) in self.results:
                        relevance = 0
                        if int(docId[1:]) in self.results[int(qId)]:
                            relevance = 1
                        submission_fh.write(f"{objId},{relevance}\n")
                    objects = objects_fh.readline()


def main():
    # Command line arguments.
    parser = argparse.ArgumentParser(description='Homework: Boolean Search')
    parser.add_argument('--queries_file', required = True, help='queries.numerate.txt')
    parser.add_argument('--objects_file', required = True, help='objects.numerate.txt')
    parser.add_argument('--docs_file', required = True, help='docs.tsv')
    parser.add_argument('--submission_file', required = True, help='output file with relevances')
    args = parser.parse_args()

    # Build index.
    from time import time
    start = time()
    index = Index(args.docs_file)
    print("Index built in %.3f sec" % (time() - start))
    # Process queries.
    search_results = SearchResults()
    with codecs.open(args.queries_file, mode='r', encoding='utf-8') as queries_fh:
        for line in queries_fh:
            fields = line.rstrip('\n').split('\t')
            qid = int(fields[0])
            query = fields[1]

            # Parse query.
            query_tree = QueryTree(qid, query)

            # Search and save results.
            search_results.add(query_tree.search(index))

    # Generate submission file.
    search_results.print_submission(args.objects_file, args.submission_file)


if __name__ == "__main__":
    main()
    # pass
