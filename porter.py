# Contains all functions related to the porter stemming algorithm.
import re
from document import Document


def get_measure(term: str) -> int:
    """
    Returns the measure m of a given term [C](VC){m}[V].
    :param term: Given term/word
    :return: Measure value m
    """
    vowels = 'aeiou'
    consonants = 'bcdfghjklmnpqrstvwxyz'
    measure = -1
    is_vc_sequence = False
    prev_letter = ''

    for letter in term.lower():
        if letter in consonants:
            if is_vc_sequence:  # If we were in a VC sequence and now we hit a consonant
                measure += 1
                is_vc_sequence = False
        if letter in vowels or letter == 'y' and prev_letter in consonants:
            is_vc_sequence = True
        prev_letter = letter

    return measure

    # TODO: Implement this function. (PR03)
    # raise NotImplementedError('This function was not implemented yet.')

def condition_v(stem: str) -> bool:
    """
    Returns whether condition *v* is true for a given stem (= the stem contains a vowel).
    :param stem: Word stem to check
    :return: True if the condition *v* holds
    """
    vowels = 'aeiou'
    prev_letter = ''
    consonants = 'bcdfghjklmnpqrstvwxyz'

    for letter in stem.lower():
        if letter in vowels or (letter == 'y' and prev_letter in consonants):
            return True
        prev_letter = letter

    return False

    # TODO: Implement this function. (PR03)
    # raise NotImplementedError('This function was not implemented yet.')

def condition_d(stem: str) -> bool:
    """
    Returns whether condition *d is true for a given stem (= the stem ends with a double consonant (e.g. -TT, -SS)).
    :param stem: Word stem to check
    :return: True if the condition *d holds
    """
    consonants = 'bcdfghjklmnpqrstvwxyz'
    if len(stem) < 2:
        return False  # Stem is too short to contain a double consonant

    # Get the last two characters of the stem
    last_two_chars = stem[-2:].lower()

    # Check if both characters are consonants
    if last_two_chars[0] in consonants and last_two_chars[1] in consonants:
        if last_two_chars[0] == last_two_chars[1]:
            return True
        else: return False
    else:
        return False
    # TODO: Implement this function. (PR03)
    # raise NotImplementedError('This function was not implemented yet.')

def cond_o(stem: str) -> bool:
    """
    Returns whether condition *o is true for a given stem (= the stem ends cvc, where the second c is not W, X or Y
    (e.g. -WIL, -HOP)).
    :param stem: Word stem to check
    :return: True if the condition *o holds
    """
    vowels = 'aeiouy'
    consonants = 'bcdfghjklmnpqrstvwxyz'
    if len(stem) < 3:
        return False

        # Extract the last three characters of the stem
    last_three_chars = stem[-3:].lower()

    # Check if the pattern matches CVC and the second consonant is not 'w', 'x', or 'y'
    if (last_three_chars[0] in consonants and
            last_three_chars[1] in vowels and
            last_three_chars[2] not in 'aeiouwyx'):
        return True

    return False
    # TODO: Implement this function. (PR03)
    # raise NotImplementedError('This function was not implemented yet.')

def stem_term(term: str) -> str:
    """
    Stems a given term of the English language using the Porter stemming algorithm.
    :param term:
    :return:
    """
    word = term.lower()
    # Step 1a
    if word.endswith("sses"):
        return word[:-2]
    if word.endswith("ies"):
        return word[:-2]

    # Step 1b
    def step1b_helper(word):
        if word.endswith("at") or word.endswith("bl") or word.endswith("iz"):
            return word + "e"
        if condition_d(word) and not word[-1] in "lsz":
            return word[:-1]
        if get_measure(word) == 1 and cond_o(word):
            return word + "e"
        return word

    if word.endswith("eed") and get_measure(word) > 0:
        stem = word[:-3]
        return stem + "ee"
    if word.endswith("ed") and get_measure(word) > 0:
        stem = word[:-2]
        if condition_v(stem):
            return step1b_helper(stem)
        return stem
    if word.endswith("ing") and get_measure(word) > 0:
        stem = word[:-3]
        if condition_v(stem):
            return step1b_helper(stem)
        return stem

    # Step 1c
    if word.endswith("y"):
        stem = word[:-1]
        if condition_v(stem):
            return stem + "i"

    # We read the porter.txt file and found the hidden note in line 354.
    # Step 2
    suffixes = {
        "ational": "ate",
        "tional": "tion",
        "enci": "ence",
        "anci": "ance",
        "izer": "ize",
        "abli": "able",
        "alli": "al",
        "entli": "ent",
        "eli": "e",
        "ousli": "ous",
        "ization": "ize",
        "ation": "ate",
        "ator": "ate",
        "alism": "al",
        "aliti": "al",
        "iviti": "ive",
        "biliti": "ble",
        "xflurti": "xti",
        "iveness": "ive",
        "fulness": "ful",
        "ousness": "ous",
    }
    for suffix, replacement in suffixes.items():
        if word.endswith(suffix) and get_measure(word) > 0:
            stem = word[:-len(suffix)]
            return stem + replacement

    # Step 3
    suffixes = {
        "icate": "ic",
        "ative": "",
        "alize": "al",
        "iciti": "ic",
        "ical": "ic",
        "ful": "",
        "ness": ""
    }
    for suffix, replacement in suffixes.items():
        if word.endswith(suffix) and get_measure(word) > 0:
            stem = word[:-len(suffix)]
            return stem + replacement

    # step 4
    suffixes = {
        "al": "",
        "ance": "",
        "ence": "",
        "er": "",
        "ic": "",
        "able": "",
        "ible": "",
        "ant": "",
        "ement": "",
        "ment": "",
        "ent": "",
        "ion": "",
        "ou": "",
        "ism": "",
        "ate": "",
        "iti": "",
        "ous": "",
        "ive": "",
        "ize": ""
    }

    for suffix, replacement in suffixes.items():
        if word.endswith(suffix) and get_measure(word) > 1:
            stem = word[:-len(suffix)]
            if suffix == "ion" and (stem.endswith("s") or stem.endswith("t")):
                return stem
            elif suffix != "ion":
                return stem

    # Step 5a
    if word.endswith("e") and get_measure(word) > 1:
        stem = word[:-1]
        if get_measure(stem) == 1 and not cond_o(stem):
            return stem

    # Step 5b
    if get_measure(word) > 1 and condition_d(word) and word.endswith("l"):
        return word[:-1]

    return word
    # TODO: Implement this function. (PR03)
    # Note: See the provided file "porter.txt" for information on how to implement it!
    # raise NotImplementedError('This function was not implemented yet.')

def stem_all_documents(collection: list[Document]):
    """
    For each document in the given collection, this method uses the stem_term() function on all terms in its term list.
    Warning: The result is NOT saved in the document's term list, but in the extra field stemmed_terms!
    :param collection: Document collection to process
    """
    for doc in collection:
        stemmed_words = []
        for word in doc.filtered_terms:
            stemmed_words.append(stem_term(word))
        doc.stemmed_terms = stemmed_words

    # TODO: Implement this function. (PR03)
    # raise NotImplementedError('This function was not implemented yet.')

def stem_query_terms(query: str) -> str:
    """
    Stems all terms in the provided query string.
    :param query: User query, may contain Boolean operators and spaces.
    :return: Query with stemmed terms
    """
    # TODO: Implement this function. (PR03)

    query.lower()

    # Tokenize the query into individual words and non-word tokens
    tokens = re.findall(r'\w+|\s+|[^\w\s]+', query)

    # List of Boolean operators to ignore
    boolean_operators = {'&', '|', '-'}

    # Stem each token if it's a word and not a Boolean operator
    stemmed_tokens = []
    for token in tokens:
        if token.isalpha() and (token[0] not in boolean_operators and token[-1] not in boolean_operators):
            # Stem the token if it's a word and not enclosed by boolean operators
            stemmed_tokens.append(stem_term(token))
        else:
            # Leave the token unchanged if it's not a word or is enclosed by operators
            stemmed_tokens.append(token)

    # Reconstruct the query from stemmed tokens
    stemmed_query = ''.join(stemmed_tokens)

    return stemmed_query
    # raise NotImplementedError('This function was not implemented yet.')


