#!/usr/bin/env python3
# coding: utf-8
"""
Package: Topican - Topic Analyser
Module: topican_by_nouns_on_csv.py

Identifies topics in a text file of a CSV file by assuming topics can be identified from Nouns and a "context" word:  
- spaCy is used to identify Nouns (including Proper nouns) in the text  
- nltk WordNet and spaCy are used to group similar nouns together (WordNet "hyponyms" are checked first; spaCy similarity is used if a hyponym is not found)  
- the top context words are found for each noun  
- Output is a list of noun groups and associated context words, in order of frequency  

Requirements:
(1) Approx 1.8GB of RAM is required to load spaCy's large English language model (to be able to use spaCy's similarity function)

See README.md and topican.print_words_associated_with_common_noun_groups for more information
"""

import argparse
import sys, os
import pandas as pd
import nltk
import spacy
import topican

def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument("filepath", help="path of CSV file")
    parser.add_argument("text_col", help="name of text column in CSV file")
    parser.add_argument("exclude_words", help="words to exclude: list of words | True to just ignore NLTK stop-words | False | None")
    parser.add_argument("top_n_noun_groups", help="number of noun groups to find (0 to find all noun/'synonym' groups)", type=int)
    parser.add_argument("top_n_words", help="number of associated words to print for each noun group (0 to print all words)", type=int)
    parser.add_argument("max_hyponyms", help="maximum number of hyponyms a word may have before it is ignored - use this to exclude very general words that may not convey useful information (0 to have no limit on the number of hyponyms a word may have)", type=int)
    parser.add_argument("max_hyponym_depth", help="level of hyponym to extract (0 to extract all hyponyms)", type=int)
    parser.add_argument("sim_threshold", help="spaCy similarity level that words must reach to qualify as being similar", type=float)
    
    args = parser.parse_args(argv)

    if os.path.exists(args.filepath):
        df = pd.read_csv(args.filepath)
    else:
        print("File '" + args.filepath + "' not found")
        sys.exit(2)
    
    if args.exclude_words == "None": args.exclude_words = None
    elif args.exclude_words == "True":
        args.exclude_words = True
        import nltk
        nltk.download('stopwords')
    elif args.exclude_words == "False": args.exclude_words = False
    if args.top_n_noun_groups == 0: args.top_n_noun_groups = None
    if args.top_n_words == 0: args.top_n_words = None
    if args.max_hyponyms == 0: args.max_hyponyms = None
    if args.max_hyponym_depth == 0: args.max_hyponym_depth = None
    descrip = args.filepath + " " + args.text_col

    spacy_model = "en_core_web_lg"
    print("Loading spaCy's language model '" + spacy_model + "' - this requires approx 1.8GB of RAM")
    nlp = spacy.load(spacy_model)
    
    topican.print_words_associated_with_common_noun_groups(
        nlp, descrip, df[args.text_col], args.exclude_words, args.top_n_noun_groups, args.top_n_words, args.max_hyponyms, args.max_hyponym_depth, args.sim_threshold)

if __name__ == "__main__":
   main()
