import difflib
import pickle

def find_max_similarity(input_string, string_list):
    max_similarity = 0
    max_string = ""

    for string in string_list:
        similarity = difflib.SequenceMatcher(None, input_string, string).quick_ratio()
        if similarity > max_similarity:
            max_similarity = similarity
            max_string = string

    return max_string, max_similarity