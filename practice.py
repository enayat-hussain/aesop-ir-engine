import json
import os
import time

import cleanup
import extraction
import models
import porter
from document import Document

# Important paths:
RAW_DATA_PATH = 'raw_data'
DATA_PATH = 'data'
COLLECTION_PATH = os.path.join(DATA_PATH, 'my_collection.json')
STOPWORD_FILE_PATH = os.path.join(DATA_PATH, 'stopwords.json')
GROUND_TRUTH_PATH = os.path.join(RAW_DATA_PATH, 'ground_truth.txt')

# Menu choices:
(CHOICE_LIST, CHOICE_SEARCH, CHOICE_EXTRACT, CHOICE_UPDATE_STOP_WORDS, CHOICE_SET_MODEL, CHOICE_SHOW_DOCUMENT,
 CHOICE_EXIT) = 1, 2, 3, 4, 5, 6, 9
MODEL_BOOL_LIN, MODEL_BOOL_INV, MODEL_BOOL_SIG, MODEL_FUZZY, MODEL_VECTOR = 1, 2, 3, 4, 5
SW_METHOD_LIST, SW_METHOD_CROUCH = 1, 2


def load_ground_truth_inline() -> dict:  # extract data from ground_truth.txt
    ground_truth = {}
    with open(GROUND_TRUTH_PATH, 'r') as file:
        for line in file:
            # Split by '-' to separate term from document IDs
            parts = line.strip().split('-')
            if len(parts) != 2:
                continue  # Skip lines that do not split into exactly two parts

            term = parts[0].strip()
            doc_ids = parts[1].strip().split(',')

            doc_ids_processed = []
            for doc_id in doc_ids:  # subtract 1 from doc ids
                try:
                    doc_id_int = int(doc_id.strip())
                    doc_ids_processed.append(str(doc_id_int - 1))
                except ValueError:
                    continue  # Skip non-numeric IDs

            ground_truth[term] = doc_ids_processed
    return ground_truth


def calculate_precision(query: str, result_list: list[tuple]) -> float:
    # TODO: Implement this function (PR03)
    def query_to_representation(query: str):
        def get_precedence(op):
            if op == '-':
                return 3
            if op == '&':
                return 2
            if op == '|':
                return 1
            return 0

        def is_operator(c):
            return c in ['&', '|', '-']

        def convertToList(query):
            queryList = []
            i = 0
            while i < len(query):
                if query[i].isalnum():
                    word = []
                    while i < len(query) and query[i].isalnum():
                        word.append(query[i])
                        i += 1
                    queryList.append(''.join(word))
                elif query[i] == '(':
                    queryList.append(query[i])
                    i = i+1
                elif query[i] == ')':
                    queryList.append(query[i])
                    i = i+1
                elif (is_operator(query[i])):
                    queryList.append(query[i])
                    i = i+1
            return queryList

        str_query = convertToList(query)

        stack = []
        result = []

        i = 0
        while i < len(str_query):
            if str_query[i].isalpha():
                result.append(''.join(str_query[i]))
            elif str_query[i] == '(':
                stack.append(str_query[i])
            elif str_query[i] == ')':
                while stack and stack[-1] != '(':
                    result.append(stack.pop())
                stack.pop()
            else:
                while stack and is_operator(stack[-1]) and get_precedence(str_query[i]) <= get_precedence(stack[-1]):
                    result.append(stack.pop())
                stack.append(str_query[i])
            i += 1

        while stack:
            result.append(stack.pop())
        return result  # Returning as list to simulate a stack
    query_representation = query_to_representation(query)
    print("query")
    print(query)
    print("result_list")
    print(result_list)
    print("query_representation")
    print(query_representation)
    ground_truth = load_ground_truth_inline()
    print("ground_truth")
    print(ground_truth)

    def match(document_representation, query) -> list:
        universal_list = list(range(82))
        query_representation = query[:]
        if len(query_representation) > 1:
            stack = []
            while query_representation:
                query_element = query_representation.pop(0)
                if not any(op in query_element for op in ["&", "|", "-"]):
                    print("not any operator")
                    print(query_element)
                    if query_element in document_representation:
                        stack.append(document_representation[query_element])
                        print("stack at first step")
                        print(stack)
                    else:
                        stack.append(False)
                elif query_element == "&":
                    query_element1 = stack.pop() if stack else []
                    query_element2 = stack.pop() if stack else []
                    intersection_set = set(
                        query_element1) & set(query_element2)
                    and_result = list(intersection_set)
                    stack.append(and_result)
                    print(stack)
                elif query_element == "|":
                    query_element1 = stack.pop() if stack else []
                    query_element2 = stack.pop() if stack else []
                    union_set = set(query_element1) | set(query_element2)
                    or_result = list(union_set)
                    stack.append(or_result)
                elif query_element == "-":
                    query_element1 = stack.pop() if stack else []
                    negation_set = set(universal_list) - set(query_element1)
                    not_result = list(negation_set)
                    stack.append(not_result)
                else:
                    "in disasters"
            return stack[0] if stack[0] else []
        elif (len(query_representation) == 1):
            if query_representation[0] in document_representation:
                return document_representation[query_representation[0]]
        return []

    truth_result = match(ground_truth, query_representation)
    truth_result_int = [int(x) for x in truth_result]
    truth_result_int.sort()
    print("ground_truth_result")
    print(truth_result_int)

    # print("query_terms")
    # print(query_terms)

    # relevant_docs = set()

    # for term in query_terms:
    #     if term in ground_truth:
    #         relevant_docs.update(ground_truth[term])

    retrieved_docs = {document.document_id for score,
                      document in result_list if score == 1.0}

    if not retrieved_docs:
        return -1.0

    # relevant_retrieved = {
    #     int(doc_id) for doc_id in relevant_docs if int(doc_id) in retrieved_docs}
    # precision = len(relevant_retrieved) / len(retrieved_docs)

    # return precision
    return 0




        def validateExpression(query_string):
            def is_other_operator(c):
                return c in ['&', '|']

            def is_negation_operator(c):
                return c == "-"
            stack = []

            str_query = convertToList(query_string)
            length = len(str_query)-1
            i = 0
            while i < length+1:
                if str_query[i].isalpha():
                    i += 1
                    pass
                elif str_query[i] == '(':
                    if i == 0:
                        if str_query[i+1].isalpha() or is_negation_operator(str_query[i+1]) or str_query[i+1] == "(":
                            stack.append(str_query[i])
                            i = i+1
                            continue
                        else:
                            return False
                    elif i == length:
                        return False
                    else:
                        if is_other_operator(str_query[i-1]) or is_negation_operator(str_query[i-1]) or str_query[i-1] == "(":
                            if is_negation_operator(str_query[i+1]) or str_query[i+1].isalpha() or str_query[i+1] == "(":
                                stack.append(str_query[i])
                                i = i+1
                            else:
                                return False
                        else:
                            return False
                elif str_query[i] == ')':
                    if i == length:
                        if str_query[i-1].isalpha() or str_query[i-1] == ")":
                            if stack.pop(0) == "(":
                                i = i+1
                                continue
                            else:
                                return False
                        else:
                            return False
                    elif i == 0:
                        return False
                    else:
                        if str_query[i-1].isalpha() or str_query[i-1] == ")":
                            if is_other_operator(str_query[i+1]) or str_query[i+1] == ")":
                                if stack.pop(0) == "(":
                                    i = i+1
                                    continue
                                else:
                                    return False
                            else:
                                return False
                        else:
                            return False
                elif (is_other_operator(str_query[i])):
                    if (i == 0 or i == length):
                        return False
                    else:
                        if (str_query[i-1] == ")" or str_query[i-1].isalpha()):
                            if (str_query[i+1] == "(" or str_query[i+1].isalpha()) or is_negation_operator(str_query[i+1]):
                                i = i+1
                                continue
                            else:
                                return False
                        else:
                            return False
                elif (is_negation_operator(str_query[i])):
                    if i == 0:
                        if not (str_query[i+1] == "(" or str_query[i+1].isalpha()):
                            return False
                        else:
                            i = i+1
                            continue
                    elif i == (length):
                        return False
                    else:
                        if str_query[i-1] == "(" or is_negation_operator(str_query[i-1]) or is_other_operator(str_query[i-1]):
                            if str_query[i+1] == "(" or str_query[i+1].isalpha():
                                i = i+1
                                continue
                            else:
                                return False
                        else:
                            return False
            return len(stack) == 0


if not validateExpression(str_query):
    return False
