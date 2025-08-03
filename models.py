# Contains all retrieval models.
from pyparsing import Word, alphas, alphanums, oneOf, infixNotation, opAssoc, Group, ParseException
from pyparsing import ParseResults

from abc import ABC, abstractmethod
import random
from document import Document
from extraction import extract_collection
from cleanup import filter_collection
from cleanup import remove_symbols
import math


class RetrievalModel(ABC):
    @abstractmethod
    def document_to_representation(self, document: Document, stopword_filtering=False, stemming=False):
        """
        Converts a document into its model-specific representation.
        This is an abstract method and not meant to be edited. Implement it in the subclasses!
        :param document: Document object to be represented
        :param stopword_filtering: Controls, whether the document should first be freed of stopwords
        :param stemming: Controls, whether stemming is used on the document's terms
        :return: A representation of the document. Data type and content depend on the implemented model.
        """
        pass

    @abstractmethod
    def query_to_representation(self, query: str):
        """
        Determines the representation of a query according to the model's concept.
        :param query: Search query of the user
        :return: Query representation in whatever data type or format is required by the model.
        """
        pass

    @abstractmethod
    def match(self, document_representation, query_representation) -> float:
        """
        Matches the query and document presentation according to the model's concept.
        :param document_representation: Data that describes one document
        :param query_representation:  Data that describes a query
        :return: Numerical approximation of the similarity between the query and document representation. Higher is
        "more relevant", lower is "less relevant".
        """
        pass


class LinearBooleanModel(RetrievalModel):
    # TODO: Implement all abstract methods and __init__() in this class. (PR02)
    def document_to_representation(self, document: Document, stopword_filtering=False, stemming=False):
        if stemming:
            return document.stemmed_terms
        elif stopword_filtering:
            return document.filtered_terms
        else:
            return document.terms
        # raise ValueError("The stopword list is empty. Cannot process an empty list.")

    def query_to_representation(self, query: str):
        # print("query")
        # print(query)

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

        lowercase_query = query.lower()
        str_query = convertToList(lowercase_query)
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

    def match(self, document_representation, query) -> float:
        # print(query)
        # print(document_representation)
        query_representation = query[:]
        if len(query_representation) > 1:
            stack = []
            while query_representation:
                query_element = query_representation.pop(0)
                if not any(op in query_element for op in ["&", "|", "-"]):
                    if query_element in document_representation:
                        stack.append(True)
                    else:
                        stack.append(False)
                elif query_element == "&":
                    query_element1 = stack.pop() if stack else []
                    query_element2 = stack.pop() if stack else []
                    and_result = (query_element1 and query_element2)
                    stack.append(and_result)
                elif query_element == "|":
                    query_element1 = stack.pop() if stack else []
                    query_element2 = stack.pop() if stack else []
                    or_result = (query_element1 or query_element2)
                    stack.append(or_result)
                elif query_element == "-":
                    query_element1 = stack.pop() if stack else []
                    not_result = (not query_element1)
                    stack.append(not_result)
                else:
                    "in disasters"
            return 1.0 if stack[0] else 0.0
        elif (len(query_representation) == 1):
            if query_representation[0] in document_representation:
                return 1.0
        return 0.0
        # return 1.0 if query_representation in document_representation else 0.0

    def __init__(self):
        pass

    def __str__(self):
        return 'Boolean Model (Linear)'


class InvertedListBooleanModel(RetrievalModel):
    # TODO: Implement all abstract methods and __init__() in this class. (PR03)
    def document_to_representation(self, document: Document, stopword_filtering=True, stemming=False):
        if stemming:
            # print("ASKING FOR STEMMING")
            # print(document.stemmed_terms)
            return document.stemmed_terms
        elif stopword_filtering:
            return document.filtered_terms
        else:
            return document.terms

    def query_to_representation(self, query: str):

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

        lowercase_query = query.lower()
        str_query = convertToList(lowercase_query)

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

    def match(self, document_representation, query_representation) -> list:
        if len(query_representation) > 1:
            stack = []
            total_documents = 82
            while query_representation:
                query_element = query_representation.pop(0)
                if not any(op in query_element for op in ["&", "|", "-"]):
                    for key, value in document_representation.items():
                        if key == query_element:
                            stack.append(value)
                            break
                elif query_element == "&":
                    query_element1 = stack.pop() if stack else []
                    query_element2 = stack.pop() if stack else []
                    query_element1.sort()
                    query_element2.sort()
                    and_result = []
                    i, j = 0, 0
                    while i < len(query_element1) and j < len(query_element2):
                        if query_element1[i] == query_element2[j]:
                            and_result.append(query_element1[i])
                            i += 1
                            j += 1
                        elif query_element1[i] < query_element2[j]:
                            i += 1
                        else:
                            j += 1
                    stack.append(and_result)
                elif query_element == "|":
                    query_element1 = stack.pop() if stack else []
                    query_element2 = stack.pop() if stack else []
                    query_element1.sort()
                    query_element2.sort()
                    or_result = []
                    i, j = 0, 0
                    added_elements = set()  # Set to store elements that have already been added
                    while i < len(query_element1) or j < len(query_element2):
                        if i < len(query_element1) and (j >= len(query_element2) or query_element1[i] < query_element2[j]):
                            # Check if element has already been added
                            if query_element1[i] not in added_elements:
                                or_result.append(query_element1[i])
                                # Add element to set
                                added_elements.add(query_element1[i])
                            i += 1
                        elif j < len(query_element2):
                            # Check if element has already been added
                            if query_element2[j] not in added_elements:
                                or_result.append(query_element2[j])
                                # Add element to set
                                added_elements.add(query_element2[j])
                            j += 1

                    stack.append(or_result)
                elif query_element == "-":
                    query_element1 = stack.pop() if stack else []
                    query_element1.sort()
                    all_documents = set(range(total_documents))
                    stack.append(list(all_documents - set(query_element1)))
                else:
                    "in disasters"
            return stack[0]
        else:
            query_element = query_representation.pop()
            for key, value in document_representation.items():
                if key == query_element:
                    return value
        return []

    def __init__(self):
        pass

    def __str__(self):
        return 'Boolean Model (Inverted List)'
# models.py


class VectorSpaceModel(RetrievalModel):
    # TODO: Implement all abstract methods. (PR04)
    def __init__(self):
        # TODO: Remove this line and implement the function.
        pass

    def __str__(self):
        return 'Vector Space Model'

    def document_to_representation(self, document: Document, stopword_filtering=True, stemming=False):
        if stemming == True:
            return document.stemmed_terms
        elif stopword_filtering == True:
            return document.filtered_terms
        else:
            return document.terms

    def query_to_representation(self, query: str):
        query_representation = query.split()
        unique_query_terms = list(set(query_representation))
        query_terms_initials = {}  # at [2]
        query_weights_without_log = {}
        for element in unique_query_terms:
            query_terms_initials[element] = (
                query_representation.count(element))

        frequency_list = []

        for value in query_terms_initials.values():
            frequency_list.append(value)

        max_term_frequency = max(frequency_list) if frequency_list else 1
        for key, value in query_terms_initials.items():
            query_weights_without_log[key] = (
                0.5+((0.5*value)/max_term_frequency))
        return query_weights_without_log

    def match(self, document_representation, query_representation) -> list:
        N = 82
        stopped_terms = document_representation

        unique_query_terms = query_representation.keys()
        inverted_stop_word_list = {}

        for term in unique_query_terms:
            for sublist in stopped_terms:
                if term in sublist:
                    if not term in inverted_stop_word_list:
                        inverted_stop_word_list[term] = [
                            stopped_terms.index(sublist)]
                    else:
                        if stopped_terms.index(sublist) not in inverted_stop_word_list[term]:
                            inverted_stop_word_list[term].append(
                                stopped_terms.index(sublist))

        query_nks = {}
        query_terms_weight = []

        for key, value in inverted_stop_word_list.items():
            query_nks[key] = len(value)

        for key, value in query_nks.items():
            query_terms_weight.append(
                (key, (query_representation[key] * math.log(N/value))))

        query_terms_weight.sort(key=lambda x: x[1], reverse=True)

        document_tfs = [{} for _ in range(82)]
        # We will store each document with the tfdk score of each query term

        for term in unique_query_terms:
            for key, values in inverted_stop_word_list.items():
                if term == key:
                    for value in values:
                        document_tfs[value][key] = stopped_terms[value].count(
                            key)

        document_idfs = {}
        for key, value in query_nks.items():
            document_idfs[key] = math.log(N/value)

        document_normalizer = [0] * 82

        for index, value in enumerate(stopped_terms):
            summation_result = 0
            for term in unique_query_terms:
                if (term in inverted_stop_word_list):
                    summation_result += ((value.count(
                        term)*(math.log((N/(len(inverted_stop_word_list[term]))))))**2)
            document_normalizer[index] = math.sqrt(summation_result)

        document_terms_weight = [{} for _ in range(82)]
        for index, document in enumerate(document_tfs):
            for tf_key, tf_value in document.items():
                document_terms_weight[index][tf_key] = (
                    document_idfs[tf_key]*tf_value)/document_normalizer[index]

        return document_terms_weight, query_terms_weight


class SignatureBasedBooleanModel(RetrievalModel):

    def __init__(self):
        """
        Initialize the hash function generator and the size of the bit signatures.
        """
        self.D = 4  # Number of hash functions (overlay factor)
        self.F = 64  # Size of the bit signature
        self.m = 12  # Signature weight

    def hash_function(self, word):
        """
        A hash function to generate a 512-bit vector with exactly 16 ones.
        """

        hash_value = 0
        prime = 31  # A prime number for hash function
        mod = 2 ** 64  # To ensure the hash value fits within 64-bit unsigned integer

        for char in word:
            hash_value = (hash_value * prime + ord(char.lower())) % mod

        # Initialize a zero vector of length F
        vector = [0] * self.F

        random.seed(hash_value)

        positions = random.sample(range(self.F), self.m)

        for pos in positions:
            vector[pos] = 1

        return vector

    def document_to_representation(self, document, stemming=False, stopword_filtering=False):
        if stemming:
            terms = document.stemmed_terms
        elif stopword_filtering:
            terms = document.filtered_terms
        else:
            terms = document.terms

        total_words = len(terms)
        num_blocks = (total_words + self.D - 1) // self.D
        bit_signatures = [[0] * self.F for _ in range(num_blocks)]

        for i, term in enumerate(terms):
            block_index = i // self.D
            term_signature = self.hash_function(term)
            for j in range(self.F):
                bit_signatures[block_index][j] |= term_signature[j]
        return bit_signatures

    def query_to_representation(self, query: str):
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

        lowercase_query = query.lower()
        str_query = convertToList(lowercase_query)
        stack = []
        result = []

        i = 0
        while i < len(str_query):
            if str_query[i].isalpha():
                bit_signature = [0] * self.F
                term_signature = self.hash_function(str_query[i])
                for j in range(self.F):
                    bit_signature[j] |= term_signature[j]
                result.append(bit_signature)
            elif str_query[i] == '(':
                stack.append(str_query[i])
            elif str_query[i] == ')':
                while stack and stack[-1] != '(':
                    result.append(stack.pop())
                stack.pop()
            else:
                while stack and is_operator(stack[-1]) and get_precedence(str_query[i]) <= get_precedence(stack[-1]):
                    # print(stack.pop)
                    result.append(stack.pop())
                stack.append(str_query[i])
            i += 1
        while stack:
            result.append(stack.pop())
        return result

    def compute_match_score(self, query_signature, doc_signature):
        """
        Compute the match score between the query signature and the document signatures.
        """
        if not isinstance(query_signature, list):
            query_signature = list(query_signature)
        if not isinstance(doc_signature, list):
            doc_signature = list(doc_signature)
        # Compute the intersection and union
        intersection = [q & d for q, d in zip(query_signature, doc_signature)]
        is_present = intersection == query_signature

        return 1.0 if is_present else 0.0

    def match(self, document_representation, query_representation):
        match_results = []
        if len(query_representation) > 1:
            stack = []
            while query_representation:
                query_element = query_representation.pop(0)
                if not any(op in query_element for op in ["&", "|", "-"]):

                    match_results = []
                    for document in document_representation:
                        match_score = max(self.compute_match_score(
                            query_element, doc_signature) for doc_signature in document)
                        match_results.append(match_score)
                    stack.append(match_results)
                elif query_element == "&":
                    query_element1 = stack.pop() if stack else []
                    query_element2 = stack.pop() if stack else []
                    bitwise_and_result = [int(a) & int(b) for a, b in zip(
                        query_element1, query_element2)]
                    bitwise_and_result_float = [
                        float(result) for result in bitwise_and_result]
                    stack.append(bitwise_and_result_float)
                elif query_element == "|":
                    query_element1 = stack.pop() if stack else []
                    query_element2 = stack.pop() if stack else []
                    bitwise_or_result = [int(a) | int(b) for a, b in zip(
                        query_element1, query_element2)]
                    bitwise_or_result_float = [
                        float(result) for result in bitwise_or_result]
                    stack.append(bitwise_or_result_float)
                elif query_element == "-":
                    query_element1 = stack.pop() if stack else []
                    negation_result = [~int(a) & 1 for a in query_element1]
                    negation_result_float = [
                        float(result) for result in negation_result]

                    stack.append(negation_result_float)
                else:
                    "in disasters"
            return stack[0]
        elif len(query_representation) == 1:
            query_element = query_representation.pop()
            for document in document_representation:
                match_score = max(self.compute_match_score(
                    query_element, doc_signature) for doc_signature in document)
                match_results.append(match_score)
            return match_results
        return []

    def __str__(self):
        return 'Boolean Model (Signatures)'


class FuzzySetModel(RetrievalModel):
    # TODO: Implement all abstract methods. (PR04)
    def __init__(self):
        # TODO: Remove this line and implement the function.
        raise NotImplementedError()

    def __str__(self):
        return 'Fuzzy Set Model'


class Document:
    def __init__(self, terms, filtered_terms=None, stemmed_terms=None):
        self.terms = terms
        self.filtered_terms = filtered_terms if filtered_terms else terms
        self.stemmed_terms = stemmed_terms if stemmed_terms else terms
