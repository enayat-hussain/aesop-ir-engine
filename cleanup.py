# Contains all functions that deal with stop word removal.
import json
import os
from document import Document

# Important paths:
RAW_DATA_PATH = 'raw_data'
DATA_PATH = 'data'


def remove_symbols(text_string: str) -> str:
    """
    Removes all punctuation marks and similar symbols from a given string.
    Occurrences of "'s" are removed as well.
    :param text:
    :return:
    """
    punctuation = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
    singular_terms = [
        "as", "is", "its", "has", "was", "does", "this",
        "his", "hers", "theirs", "ours", "yours", "thus"
    ]

    # Remove punctuation
    cleaned_text = ''
    for char in text_string:
        if char not in punctuation:
            cleaned_text += char

    # Convert to lowercase
    cleaned_text = cleaned_text.lower()

    # Remove trailing 's if it's not a singular term
    if cleaned_text.endswith('s') and cleaned_text not in singular_terms:
        cleaned_text = cleaned_text[:-1]

    return cleaned_text


def is_stop_word(term: str, stop_word_list: list[str]) -> bool:
    """
    Checks if a given term is a stop word.
    :param stop_word_list: List of all considered stop words.
    :param term: The term to be checked.
    :return: True if the term is a stop word.
    """
    return term.lower() in stop_word_list


def remove_stop_words_from_term_list(term_list: list[str]) -> list[str]:
    """
    Takes a list of terms and removes all terms that are stop words.
    :param term_list: List that contains the terms
    :return: List of terms without stop words
    """
    cleaned_term_list = []
    stop_word_file = os.path.join(DATA_PATH, 'stopwords.json') if os.path.exists(
        os.path.join(DATA_PATH, 'stopwords.json')) else os.path.join(RAW_DATA_PATH, 'englishST.txt')
    # reads stop word file
    if stop_word_file.split('.')[-1] == 'json':
        with open(stop_word_file, 'r') as file:
            stop_words_list = json.load(file)
    else:
        with open(stop_word_file, 'r') as file:
            file_lines = file.readlines()
            stop_words_list = [word.strip() for word in file_lines]

    # removes stop words from the list
    for word in term_list:
        new_word = remove_symbols(word)
        # print(new_word)
        if not is_stop_word(new_word, stop_words_list):
            if new_word.strip():
                cleaned_term_list.append(new_word.lower())
    return cleaned_term_list


def filter_collection(collection: list[Document]):
    """
    For each document in the given collection, this method takes the term list and filters out the stop words.
    Warning: The result is NOT saved in the documents term list, but in an extra field called filtered_terms.
    :param collection: Document collection to process
    """
    for doc in collection:
        # print(doc.filtered_terms)
        doc.filtered_terms = remove_stop_words_from_term_list(doc.terms)
    # print("Going to print filtered terms")
    # print(collection[0].filtered_terms)
# TEST


# dummy_doc = Document()
# dummy_doc.document_id = 7
# dummy_doc.title = "The Fox and the Crow"
# dummy_doc.terms = ["a", "tree.", "\"That's", "for", "me,", "as", "I", "am", "a", "Fox,\"", "said", "Master", "Reynard,", "and", "tree.", "\"Good-day,", "Mistress", "Crow,\"", "he", "cried.", "\"How", "well", "looking", "to-day:", "how", "glossy", "your", "feathers;", "how", "your", "eye.", "I", "other", "birds,", "just", "as", "your",
#                    "figure", "does;",  "the", "Queen", "of", "Birds.\"", "The", "Crow", "lifted", "Master", "Fox.", "\"That", "will", "do,\"", "said", "he.", "\"That", "was", "all", "I", "wanted.", "the", "future", ".\"Do", "not", "trust", "flatterers.\""]
# documents = [dummy_doc]
# filter_collection(documents)


def load_stop_word_list(raw_file_path: str) -> list[str]:
    """
    Loads a text file that contains stop words and saves it as a list. The text file is expected to be formatted so that
    each stop word is in a new line, e. g. like englishST.txt
    :param raw_file_path: Path to the text file that contains the stop words
    :return: List of stop words
    """
    # TODO: Implement this function. (PR02)
    # reads stop word file
    with open(raw_file_path, 'r') as file:
        file_lines = file.readlines()
        stop_words_list = [word.strip() for word in file_lines]
    return stop_words_list


def create_stop_word_list_by_frequency(collection: list[Document]) -> list[str]:
    """
    Uses the method of J. C. Crouch (1990) to generate a stop word list by finding high and low frequency terms in the
    provided collection.
    :param collection: Collection to process
    :return: List of stop words
    """
    # TODO: Implement this function. (PR02)
    term_counts = {}
    stop_word = []
    merged_list = [item for sublist in collection for item in sublist.terms]
    # Count the occurrence of each term
    for token in merged_list:
        if token in term_counts:
            term_counts[token] += 1
        else:
            term_counts[token] = 1

    for term, count in term_counts.items():
        if count > 12:
            stop_word.append(term.lower())
    return stop_word
