# --------------------------------------------------------------------------------
# Information Retrieval SS2024 - Practical Assignment Template
# --------------------------------------------------------------------------------
# This Python template is provided as a starting point for your assignments PR02-04.
# It serves as a base for a very rudimentary text-based information retrieval system.
#
# Please keep all instructions from the task description in mind.
# Especially, avoid changing the base structure, function or class names or the
# underlying program logic. This is necessary to run automated tests on your code.
#
# Instructions:
# 1. Read through the whole template to understand the expected workflow and outputs.
# 2. Implement the required functions and classes, filling in your code where indicated.
# 3. Test your code to ensure functionality and correct handling of edge cases.
#
# Good luck!


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


class InformationRetrievalSystem(object):
    def __init__(self):
        if not os.path.isdir(DATA_PATH):
            os.makedirs(DATA_PATH)

        # Collection of documents, initially empty.
        try:
            self.collection = extraction.load_collection_from_json(
                COLLECTION_PATH)
        except FileNotFoundError:
            print('No previous collection was found. Creating empty one.')
            self.collection = []

        # Stopword list, initially empty.
        try:
            with open(STOPWORD_FILE_PATH, 'r') as f:
                self.stop_word_list = json.load(f)
        except FileNotFoundError:
            print('No stopword list was found.')
            self.stop_word_list = []

        self.model = None  # Saves the current IR model in use.
        # Controls how many results should be shown for a query.
        self.output_k = 5

    def main_menu(self):
        """
        Provides the main loop of the CLI menu that the user interacts with.
        """
        while True:
            print(f'Current retrieval model: {self.model}')
            print(f'Current collection: {len(self.collection)} documents')
            print()
            print('Please choose an option:')
            print(f'{CHOICE_LIST} - List documents')
            print(f'{CHOICE_SEARCH} - Search for term')
            print(f'{CHOICE_EXTRACT} - Build collection')
            print(f'{CHOICE_UPDATE_STOP_WORDS} - Rebuild stopword list')
            print(f'{CHOICE_SET_MODEL} - Set model')
            print(f'{CHOICE_SHOW_DOCUMENT} - Show a specific document')
            print(f'{CHOICE_EXIT} - Exit')
            action_choice = int(input('Enter choice: '))

            if action_choice == CHOICE_LIST:
                # List documents in CLI.
                if self.collection:
                    for document in self.collection:
                        print(document)
                else:
                    print('No documents.')
                print()

            elif action_choice == CHOICE_SEARCH:
                # Read a query string from the CLI and search for it.

                # Determine desired search parameters:
                SEARCH_NORMAL, SEARCH_SW, SEARCH_STEM, SEARCH_SW_STEM = 1, 2, 3, 4
                print('Search options:')
                print(f'{SEARCH_NORMAL} - Standard search (default)')
                print(f'{SEARCH_SW} - Search documents with removed stopwords')
                print(f'{SEARCH_STEM} - Search documents with stemmed terms')
                print(
                    f'{SEARCH_SW_STEM} - Search documents with removed stopwords AND stemmed terms')
                search_mode = int(input('Enter choice: '))
                stop_word_filtering = (search_mode == SEARCH_SW) or (
                    search_mode == SEARCH_SW_STEM)
                stemming = (search_mode == SEARCH_STEM) or (
                    search_mode == SEARCH_SW_STEM)

                # Actual query processing begins here:
                query = input('Query: ')
                if stemming:
                    query = porter.stem_query_terms(query)

                start_time = time.time()  # Start time measurement
                if isinstance(self.model, models.InvertedListBooleanModel):
                    results = self.inverted_list_search(
                        query, stemming, stop_word_filtering)
                elif isinstance(self.model, models.VectorSpaceModel):
                    results = self.buckley_lewit_search(
                        query, stemming, stop_word_filtering)
                elif isinstance(self.model, models.SignatureBasedBooleanModel):
                    results = self.signature_search(
                        query, stemming, stop_word_filtering)
                else:
                    results = self.basic_query_search(
                        query, stemming, stop_word_filtering)

                # Output of results:
                for (score, document) in results[:self.output_k]:
                    print(f'{score}: {document}')

                end_time = time.time()  # End time measurement

                # Output of quality metrics:
                print()
                print(f'precision: {self.calculate_precision(query, results)}')
                print(f'recall: {self.calculate_recall(query, results)}')

                elapsed_time_ms = (end_time - start_time) * \
                    1000  # calculate the elapsed time
                print(f'Time taken: {elapsed_time_ms:.2f} ms')

            elif action_choice == CHOICE_EXTRACT:
                # Extract document collection from text file.

                raw_collection_file = os.path.join(
                    RAW_DATA_PATH, 'aesopa10.txt')
                self.collection = extraction.extract_collection(
                    raw_collection_file)
                assert isinstance(self.collection, list)
                assert all(isinstance(d, Document) for d in self.collection)

                if input('Should stopwords be filtered? [y/N]: ') == 'y':
                    cleanup.filter_collection(self.collection)

                if input('Should stemming be performed? [y/N]: ') == 'y':
                    porter.stem_all_documents(self.collection)

                extraction.save_collection_as_json(
                    self.collection, COLLECTION_PATH)
                print('Done.\n')

            elif action_choice == CHOICE_UPDATE_STOP_WORDS:
                # Rebuild the stop word list, using one out of two methods.

                print('Available options:')
                print(f'{SW_METHOD_LIST} - Load stopword list from file')
                print(
                    f"{SW_METHOD_CROUCH} - Generate stopword list using Crouch's method")

                method_choice = int(input('Enter choice: '))
                if method_choice in (SW_METHOD_LIST, SW_METHOD_CROUCH):
                    # Load stop words using the desired method:
                    if method_choice == SW_METHOD_LIST:
                        self.stop_word_list = cleanup.load_stop_word_list(
                            os.path.join(RAW_DATA_PATH, 'englishST.txt'))
                        print('Done.\n')
                    elif method_choice == SW_METHOD_CROUCH:
                        self.stop_word_list = cleanup.create_stop_word_list_by_frequency(
                            self.collection)
                        print('Done.\n')

                    # Save new stopword list into file:
                    with open(STOPWORD_FILE_PATH, 'w') as f:
                        json.dump(self.stop_word_list, f)
                else:
                    print('Invalid choice.')

            elif action_choice == CHOICE_SET_MODEL:
                # Choose and set the retrieval model to use for searches.

                print()
                print('Available models:')
                print(f'{MODEL_BOOL_LIN} - Boolean model with linear search')
                print(f'{MODEL_BOOL_INV} - Boolean model with inverted lists')
                print(
                    f'{MODEL_BOOL_SIG} - Boolean model with signature-based search')
                print(f'{MODEL_FUZZY} - Fuzzy set model')
                print(f'{MODEL_VECTOR} - Vector space model')
                model_choice = int(input('Enter choice: '))
                if model_choice == MODEL_BOOL_LIN:
                    self.model = models.LinearBooleanModel()
                elif model_choice == MODEL_BOOL_INV:
                    self.model = models.InvertedListBooleanModel()
                elif model_choice == MODEL_BOOL_SIG:
                    self.model = models.SignatureBasedBooleanModel()
                elif model_choice == MODEL_FUZZY:
                    self.model = models.FuzzySetModel()
                elif model_choice == MODEL_VECTOR:
                    self.model = models.VectorSpaceModel()
                else:
                    print('Invalid choice.')

            elif action_choice == CHOICE_SHOW_DOCUMENT:
                target_id = int(input('ID of the desired document:'))
                found = False
                for document in self.collection:
                    if document.document_id == target_id:
                        print(document.title)
                        print('-' * len(document.title))
                        print(document.raw_text)
                        found = True

                if not found:
                    print(f'Document #{target_id} not found!')

            elif action_choice == CHOICE_EXIT:
                break
            else:
                print('Invalid choice.')

            print()
            input('Press ENTER to continue...')
            print()

    def basic_query_search(self, query: str, stemming: bool, stop_word_filtering: bool) -> list:
        """
        Searches the collection for a query string. This method is "basic" in that it does not use any special algorithm
        to accelerate the search. It simply calculates all representations and matches them, returning a sorted list of
        the k most relevant documents and their scores.
        :param query: Query string
        :param stemming: Controls, whether stemming is used
        :param stop_word_filtering: Controls, whether stop-words are ignored in the search
        :return: List of tuples, where the first element is the relevance score and the second the corresponding
        document
        """
        query_representation = self.model.query_to_representation(query)
        document_representations = [self.model.document_to_representation(d, stop_word_filtering, stemming)
                                    for d in self.collection]

        scores = [self.model.match(dr, query_representation)
                  for dr in document_representations]
        ranked_collection = sorted(
            zip(scores, self.collection), key=lambda x: x[0], reverse=True)

        results = ranked_collection
        return results

    def inverted_list_search(self, query: str, stemming: bool, stop_word_filtering: bool) -> list:
        inverted_list_stemmed = {}
        inverted_list_stopped_words = {}
        stopped_terms = [self.model.document_to_representation(d, True, False)
                         for d in self.collection]
        stemmed_terms = [self.model.document_to_representation(d, False, True)
                         for d in self.collection]
        query_representation = self.model.query_to_representation(query)
        for sublist in stemmed_terms:
            for element in sublist:
                if len(inverted_list_stemmed) == 0:
                    inverted_list_stemmed[element] = [
                        stemmed_terms.index(sublist)]
                else:
                    if element in inverted_list_stemmed:
                        if stemmed_terms.index(sublist) not in inverted_list_stemmed[element]:
                            inverted_list_stemmed[element].append(
                                stemmed_terms.index(sublist))
                    else:
                        inverted_list_stemmed[element] = [
                            stemmed_terms.index(sublist)]

        for sublist in stopped_terms:
            for element in sublist:
                if len(inverted_list_stopped_words) == 0:
                    inverted_list_stopped_words[element] = [
                        stopped_terms.index(sublist)]
                else:
                    if element in inverted_list_stopped_words:
                        if stopped_terms.index(sublist) not in inverted_list_stopped_words[element]:
                            inverted_list_stopped_words[element].append(
                                stopped_terms.index(sublist))
                    else:
                        inverted_list_stopped_words[element] = [
                            stopped_terms.index(sublist)]
        if stemming:
            documents = [self.collection[i]
                         for i in self.model.match(inverted_list_stemmed, query_representation)]
        else:
            documents = [self.collection[i]
                         for i in self.model.match(inverted_list_stopped_words, query_representation)]
        scores = [1.0 if doc in documents else 0.0 for doc in self.collection]
        ranked_collection = sorted(
            zip(scores, self.collection), key=lambda x: x[0], reverse=True)

        # results = ranked_collection[:self.output_k]
        results = ranked_collection
        return results

    def buckley_lewit_search(self, query: str, stemming: bool, stop_word_filtering: bool) -> list:
        """
        Fast query search for the Vector Space Model using the algorithm by Buckley & Lewit.
        :param query: Query string
        :param stemming: Controls, whether stemming is used
        :param stop_word_filtering: Controls, whether stop-words are ignored in the search
        :return: List of tuples, where the first element is the relevance score and the second the corresponding
        document
        """
        # TODO: Implement this function (PR04)

        query_weights_without_log = self.model.query_to_representation(query)

        terms = [self.model.document_to_representation(d, True, False)
                 for d in self.collection]
        document_terms_weight, query_terms_weight = self.model.match(
            terms, query_weights_without_log)

        auxilary_DS = {}
        top_docs = []
        top_docs_size = 10

        def InitList(k):
            inverted_list = []
            # print("stopped_terms")
            # print(stopped_terms)
            for sublist in terms:
                if k in sublist:
                    if not k in inverted_list:
                        inverted_list.append(terms.index(sublist))
            return inverted_list

        def GetNextElementOfList(document, term):
            # return document and it's weight
            return document_terms_weight[document][term]

        def IsInDS(document):
            return True if document in auxilary_DS else False

        def InsertIntoDS(document, weight):
            auxilary_DS[document] = weight
            InsertIntoTopDocs(document, weight)
            return

        def AddToDSEntry(document, weight):
            auxilary_DS[document] += weight
            InsertIntoTopDocs(document, weight)
            return

        def GetWeightFromDS(document):

            return auxilary_DS[document]

        def InsertIntoTopDocs(document, weight):

            updated = False
            for idx, (key, value) in enumerate(top_docs):
                if key == document:
                    top_docs[idx][1] = (weight+value)
                    updated = True
                    break

            if not updated:
                top_docs.append([document, weight])

            top_docs.sort(key=lambda x: x[1], reverse=True)
            return

        def MaxRemainingWeight(index):
            remaining_weight = 0
            for idx in range((index+1), len(query_terms_weight)):
                key, value = query_terms_weight[idx]
                remaining_weight += value
            return remaining_weight

        def isTopDocsTerminate(index):
            if (len(top_docs) > (top_docs_size)):
                if top_docs[(top_docs_size-1)][1] > (top_docs[(top_docs_size)][1]+MaxRemainingWeight(index)):
                    return True
                else:
                    return False
            else:
                return False

        def buckley(query_weights):
            for index, term in enumerate(query_weights):
                inverted_list = InitList(term[0])
                for document in inverted_list:
                    term_weight_in_doc = GetNextElementOfList(
                        document, term[0])

                    weight = (term_weight_in_doc*term[1])

                    if IsInDS(document):
                        AddToDSEntry(document, weight)
                    else:
                        InsertIntoDS(document, weight)
                if isTopDocsTerminate(index):
                    return top_docs
            return top_docs

        result = buckley(query_terms_weight)

        all_docs = [[i, 0.0] for i in range(82)]

        for doc_id, score in result:
            all_docs[doc_id][1] = round(score, 4)

        scores = [score[1] for score in all_docs]
        ranked_collection = sorted(
            zip(scores, self.collection), key=lambda x: x[0], reverse=True)
        final_result = ranked_collection
        return final_result
        # raise NotImplementedError('To be implemented in PR04')

    def signature_search(self, query: str, stemming: bool, stop_word_filtering: bool) -> list:
        """
        Fast Boolean query search using signatures for quicker processing.
        :param query: Query string
        :param stemming: Controls, whether stemming is used
        :param stop_word_filtering: Controls, whether stop-words are ignored in the search
        :return: List of tuples, where the first element is the relevance score and the second the corresponding
        document
        """
        # TODO: Implement this function (PR04)

        query_representation = self.model.query_to_representation(query)
        document_representation = [self.model.document_to_representation(d, stemming, stop_word_filtering)
                                   for d in self.collection]
        scores = self.model.match(document_representation,
                                  query_representation)

        updated_scores = []

        for count, (score, document) in enumerate(zip(scores, self.collection)):

            # Determine which document attribute to check based on the flags
            if stemming:
                doc_terms = document.stemmed_terms
            elif stop_word_filtering:
                doc_terms = document.filtered_terms
            else:
                doc_terms = document.terms

            if score == 1.0 and query in doc_terms:
                updated_scores.append(1.0)
            else:
                updated_scores.append(0.0)

        results = [(score, i) for i, score in enumerate(scores)]
        # # Sort results by score in descending order
        ranked_collection = sorted(results, key=lambda x: x[0], reverse=True)

        # # Extract the top-k results and format them as (score, document)
        results = [(score, self.collection[i])
                   for score, i in ranked_collection]

        return results
        # raise NotImplementedError('To be implemented in PR04')

    def calculate_precision(self, query: str, result_list: list[tuple]) -> float:
        # TODO: Implement this function (PR03)
        operator_chars = ['&', '|', '-']
        contains_operators = any(char in query for char in operator_chars)
        contains_spaces = ' ' in query

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

            if contains_operators:
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
            elif contains_spaces:
                query_terms = query.split()
                return query_terms
            else:
                return [query]

        def match(document_representation, query) -> list:
            if contains_operators:
                universal_list = list(range(82))
                query_representation = query[:]
                if len(query_representation) > 1:
                    stack = []
                    while query_representation:
                        query_element = query_representation.pop(0)
                        if not any(op in query_element for op in ["&", "|", "-"]):
                            if query_element in document_representation:
                                stack.append(
                                    document_representation[query_element])
                            else:
                                return []
                        elif query_element == "&":
                            query_element1 = stack.pop() if stack else []
                            query_element2 = stack.pop() if stack else []
                            intersection_set = set(
                                query_element1) & set(query_element2)
                            and_result = list(intersection_set)
                            stack.append(and_result)
                        elif query_element == "|":
                            query_element1 = stack.pop() if stack else []
                            query_element2 = stack.pop() if stack else []
                            union_set = set(query_element1) | set(
                                query_element2)
                            or_result = list(union_set)
                            stack.append(or_result)
                        elif query_element == "-":
                            query_element1 = stack.pop() if stack else []
                            negation_set = set(universal_list) - \
                                set(query_element1)
                            not_result = list(negation_set)
                            stack.append(not_result)
                        else:
                            "in disasters"
                    return stack[0] if stack[0] else []
                elif (len(query_representation) == 1):
                    if query_representation[0] in document_representation:
                        return document_representation[query_representation[0]]
                return []
            elif contains_spaces:
                results = []
                for term in query:
                    if term in document_representation:
                        if results:
                            union_set = set(results).union(
                                set(document_representation[term]))
                            results = list(union_set)
                        else:
                            results = document_representation[term][:]
                    else:
                        return []
                return results
            elif len(query) == 1:
                if query[0] in document_representation:
                    return document_representation[query[0]]
                else:
                    return []
            else:
                return []
        lowercase_query = query.lower()
        query_representation = query_to_representation(lowercase_query)
        ground_truth = load_ground_truth_inline()
        truth_result = match(ground_truth, query_representation)
        if not truth_result:
            return -1

        truth_result_int = [int(x) for x in truth_result]
        # retrieved_docs = set()
        truth_result_int.sort()
        retrieved_docs = {document.document_id for score,
                          document in result_list if score > 0}
        if not retrieved_docs:
            return -1.0

        ground_truth_set = set(truth_result_int)
        relevant_docs = ground_truth_set.intersection(retrieved_docs)
        precision = len(relevant_docs) / len(retrieved_docs)
        return precision
        # raise NotImplementedError('To be implemented in PR03')

    def calculate_recall(self, query: str, result_list: list[tuple]) -> float:
        # TODO: Implement this function (PR03)
        operator_chars = ['&', '|', '-']
        contains_operators = any(char in query for char in operator_chars)
        contains_spaces = ' ' in query

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

            if contains_operators:
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
            elif contains_spaces:
                query_terms = query.split()
                return query_terms
            else:
                return [query]

        def match(document_representation, query) -> list:
            if contains_operators:
                universal_list = list(range(82))
                query_representation = query[:]
                if len(query_representation) > 1:
                    stack = []
                    while query_representation:
                        query_element = query_representation.pop(0)
                        if not any(op in query_element for op in ["&", "|", "-"]):
                            if query_element in document_representation:
                                stack.append(
                                    document_representation[query_element])
                            else:
                                return []
                        elif query_element == "&":
                            query_element1 = stack.pop() if stack else []
                            query_element2 = stack.pop() if stack else []
                            intersection_set = set(
                                query_element1) & set(query_element2)
                            and_result = list(intersection_set)
                            stack.append(and_result)
                        elif query_element == "|":
                            query_element1 = stack.pop() if stack else []
                            query_element2 = stack.pop() if stack else []
                            union_set = set(query_element1) | set(
                                query_element2)
                            or_result = list(union_set)
                            stack.append(or_result)
                        elif query_element == "-":
                            query_element1 = stack.pop() if stack else []
                            negation_set = set(universal_list) - \
                                set(query_element1)
                            not_result = list(negation_set)
                            stack.append(not_result)
                        else:
                            "in disasters"
                    return stack[0] if stack[0] else []
                elif (len(query_representation) == 1):
                    if query_representation[0] in document_representation:
                        return document_representation[query_representation[0]]
                return []
            elif contains_spaces:
                results = []
                for term in query:
                    if term in document_representation:
                        if results:
                            union_set = set(results).union(
                                set(document_representation[term]))
                            results = list(union_set)
                        else:
                            results = document_representation[term][:]
                    else:
                        return []
                return results
            elif len(query) == 1:
                if query[0] in document_representation:
                    return document_representation[query[0]]
                else:
                    return []
            else:
                return []
        lowercase_query = query.lower()
        query_representation = query_to_representation(lowercase_query)
        ground_truth = load_ground_truth_inline()
        truth_result = match(ground_truth, query_representation)

        if not truth_result:
            return -1

        truth_result_int = [int(x) for x in truth_result]
        truth_result_int.sort()
        retrieved_docs = {document.document_id for score,
                          document in result_list if score > 0}

        if not retrieved_docs:
            return -1.0

        ground_truth_set = set(truth_result_int)
        relevant_docs = ground_truth_set.intersection(retrieved_docs)
        recall = len(relevant_docs) / len(ground_truth_set)
        return recall
        # raise NotImplementedError('To be implemented in PR03')


if __name__ == '__main__':
    irs = InformationRetrievalSystem()
    irs.main_menu()
    exit(0)
