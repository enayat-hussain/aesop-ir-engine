# Contains functions that deal with the extraction of documents from a text file (see PR01)
import json

from document import Document


def extract_collection(source_file_path: str) -> list[Document]:
    print("")
    """
    Loads a text file (aesopa10.txt) and extracts each of the listed fables/stories from the file.
    :param source_file_name: File name of the file that contains the fables
    :return: List of Document objects
    """
    catalog = []  # This dictionary will store the document raw_data.

    # TODO: Implement this function. (PR02)
    pre_consecutive_empty_lines = 0
    post_consecutive_empty_lines = 0
    reading_fables = False
    store_documents = False
    store_title = False
    store_text = False
    save_in_catalog = False
    raw_text = ''
    title = ''
    doc_id = 0
    terms = ''

    with open(source_file_path, 'r') as file:
        for line in file:
            # Check if we're reading fables and count consecutive empty lines after finding "Aesop's Fables"
            if reading_fables and not store_documents:
                if post_consecutive_empty_lines == 3:
                    title = line.strip()
                    store_documents = True
                    store_text = True
                    continue
                if line.strip() == '':
                    post_consecutive_empty_lines += 1
                else:
                    post_consecutive_empty_lines = 0
            else:
                if pre_consecutive_empty_lines == 2 and line.strip() == "Aesop's Fables":
                    reading_fables = True
                if line.strip() == '':
                    pre_consecutive_empty_lines += 1
                else:
                    pre_consecutive_empty_lines = 0

            if store_documents:
                if store_title:
                    title = line.strip()
                    store_title = False
                    store_text = True
                    continue
                if store_text:
                    if line.strip():
                        raw_text = raw_text+line
                    else:
                        second_line = file.readline()
                        if second_line == '':
                            doc = Document()
                            doc.document_id = doc_id
                            doc.title = title
                            doc.raw_text = raw_text
                            terms = title.split()
                            terms = terms+raw_text.split()
                            doc.terms = terms
                            catalog.append(doc)
                        elif second_line == '\n':
                            third_line = file.readline()
                            if third_line == '\n':
                                save_in_catalog = True
                            else:
                                raw_text = raw_text+third_line
                        else:
                            raw_text = raw_text+second_line
                        if save_in_catalog:
                            doc = Document()
                            doc.document_id = doc_id
                            doc.title = title
                            doc.raw_text = raw_text
                            terms = title.split()
                            terms = terms+raw_text.split()
                            doc.terms = terms
                            catalog.append(doc)
                            store_title = True
                            store_text = False
                            save_in_catalog = False
                            raw_text = ''
                            terms = ''
                            doc_id += 1
    return catalog


def save_collection_as_json(collection: list[Document], file_path: str) -> None:
    """
    Saves the collection to a JSON file.
    :param collection: The collection to store (= a list of Document objects)
    :param file_path: Path of the JSON file
    """

    serializable_collection = []
    for document in collection:
        serializable_collection += [{
            'document_id': document.document_id,
            'title': document.title,
            'raw_text': document.raw_text,
            'terms': document.terms,
            'filtered_terms': document.filtered_terms,
            'stemmed_terms': document.stemmed_terms
        }]

    with open(file_path, "w") as json_file:
        json.dump(serializable_collection, json_file)


def load_collection_from_json(file_path: str) -> list[Document]:
    """
    Loads the collection from a JSON file.
    :param file_path: Path of the JSON file
    :return: list of Document objects
    """
    try:
        with open(file_path, "r") as json_file:
            json_collection = json.load(json_file)

        collection = []
        for doc_dict in json_collection:
            document = Document()
            document.document_id = doc_dict.get('document_id')
            document.title = doc_dict.get('title')
            document.raw_text = doc_dict.get('raw_text')
            document.terms = doc_dict.get('terms')
            document.filtered_terms = doc_dict.get('filtered_terms')
            document.stemmed_terms = doc_dict.get('stemmed_terms')
            collection += [document]

        return collection
    except FileNotFoundError:
        print('No collection was found. Creating empty one.')
        return []
