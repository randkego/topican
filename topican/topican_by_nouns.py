# coding: utf-8
"""
Package: Topican - Topic Analyser
Module: topican_by_nouns.py
Identify topics by finding the top noun groups (nouns with 'synonyms') in free-text pandas and the top words
words associated with them.
 
Citations:
(1) Uses spaCy - a free, open-source package for "Industrial Strength NLP" (Natural Language Processing)
(2) spaCy uses gloVe - Global Vectors for Word Representation Ref: Jeffrey Pennington, Richard Socher, and
Christopher D. Manning. 2014. https://nlp.stanford.edu/pubs/glove.pdf
"""

# Name for group containings words that are not known in the language model (potentially spelling errors)
_UNKNOWN_GROUP_ROOT_WORD = "_Unknown/Spelling_Error"

# Name for group containings words that are not known in the language model but were not grouped
_OTHER_GROUP_ROOT_WORD = "_OTHER"

import string
import re
import pandas as pd
from collections import Counter
from collections import OrderedDict
import nltk
from nltk.corpus import wordnet as wn
from nltk.corpus.reader.wordnet import WordNetError
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import stopwords
import spacy

class SpaCyFreeText():
    """
    Class to perform some spaCy operations on a free-text Panda Series object.
    
    spaCy has many powerful features, including Part-Of-Speech tagging (POS) and Dependency Trees to yield a deeper
    understanding of text. 

    Any NaN values in the text are replaced by the empty string.
    To aid Part Of Speech and dependency tree parsing, a full-stop is added to any items in the Series
    that do not already end in punctuation.
    
    As the size of the text data is not very small, spaCy’s `pipe` is used to iterate over the text. This 
    improves speed by accumulating a buffer and operating on the text in parallel (NB the argument
    'n_threads' appears to make no difference).

    Warning: At the time of coding, spaCy token.similarity(other) has a bug when 'other' has length 1, 
    producing the following error:
        "TypeError: 'spacy.tokens.token.Token' object does not support indexing"
        
    The work-around used is to ignore tokens with length 1.
    """

    def __init__(self, nlp, name, free_text_Series):
        """
        Instantiate the class with the specified spaCy nlp object.
        """
        self.nlp = nlp
        self.name = name
        
        self.free_text_list = []
        for value in free_text_Series.fillna(""):
            if len(value) > 0:
                if value[-1] not in string.punctuation: value += "."
            self.free_text_list.append(value)
        free_text_Series = pd.Series(self.free_text_list)

        # Create a spaCy document for each item in the free-text
        self.doc_list = []
        for doc in self.nlp.pipe(free_text_Series):
            self.doc_list.append(doc)

    def get_name(self): return self.name

    def get_free_text_list(self): return self.free_text_list
    
    def get_doc_list(self): return self.doc_list

    def get_most_common_pos(self, pos, top_n = 10, exclude_words=[]):
        """
        Get top_n most common Parts Of Speech (top n nouns, verbs etc.)
        Specify pos as 'None' to match all parts-of-speech
        Specify top_n as 'None' to print all words
        Use exclude_words to ignore certain words, e.g. not so useful 'stop words' or artificial words.
        """
        word_list = []
        for doc in self.doc_list:
            for token in doc:
                # Allow for matching multiple POS, e.g. "NOUN,PROPN" or all POS if pos=None
                if not pos or token.pos_ in pos.split(","):
                    token_no_end_punc = token.lower_.rstrip(string.punctuation)
                    if token_no_end_punc not in exclude_words:
                        word_list.append(token_no_end_punc)
                    # ??? TODO: make use of lower_ and rstrip configurable?
        most_common_pos = Counter(word_list).most_common(top_n)
        return(most_common_pos)

    def print_most_common_pos(self, pos, top_n = 10, exclude_words=[]):
        if top_n:
            print("Top", top_n, end='')
        else:
            print("All", end='')
        print(" " + pos + "s for", self.name)
        most_common_pos = self.get_most_common_pos(pos, top_n, exclude_words)
        print(most_common_pos)
        
    def print_most_common_pos_with_words_before(self, pos, top_n = 10, exclude_words=[]):
        """
        Print top_n words with the specified part-of-speech and their preceeding word (if any).
        Specify pos as 'None' to match all parts-of-speech
        Specify top_n as 'None' to print all words
        Use exclude_words to ignore certain words, e.g. not so useful 'stop words' or artificial words.
        """
        NO_WORD_BEFORE = "no_word_before" 
        
        ## For debugging, create a fixed-size buffer to hold the top_n words_before
        ##import collections
        ##debug_prev_words_deque = collections.deque(maxlen=top_n)
        ##for i in range(top_n): debug_prev_words_deque.append(NO_WORD_BEFORE)
        
        word_list = [] # List of words used to determine the top_n
        word_dict = {} # Dictionary of words used to hold their preceding words
        token_before = ""
        for doc in self.doc_list:
            for token in doc:
                token_no_end_punc = token.lower_.rstrip(string.punctuation)
                
                # Allow for matching multiple POS, e.g. "NOUN,PROPN" or all POS if pos=None
                if not pos or token.pos_ in pos.split(","):
                    if token_no_end_punc not in exclude_words:
                        word_list.append(token_no_end_punc)
                        ##if token_no_end_punc == "<some anomaly>": print("DEBUG: '<some anomaly>' was preceded by: ", debug_prev_words_deque)

                        if token_no_end_punc not in word_dict:
                            word_dict[token_no_end_punc] = []

                        if not token_before or token_before in string.punctuation:
                            token_before = NO_WORD_BEFORE

                        # Add the word before the specified part-of-speech word to the list of words found before it
                        word_dict[token_no_end_punc].append(token_before)
                        
                token_before = token_no_end_punc
                ##debug_prev_words_deque.append(token_before)
        most_common_words = Counter(word_list).most_common(top_n)
        if top_n:
            print("Top", top_n, end='')
        else:
            print("All", end='')
        print(pos + "s and top preceeding words for", self.name)
        for word, word_count in most_common_words:
            print("['" + word + "', " + str(word_count) + "]", "has top preceding words (freq>1): ", end=(''))
            
            most_common_words_before = Counter(word_dict[word]).most_common(top_n)
            for word_before, word_before_count in most_common_words_before:
                if word_before_count > 1:
                    print("('" + word_before + "', " + str(word_before_count) + ") ", end=(''))
            print()
        
    def get_most_common_nouns(self, top_n = 10, exclude_words=[]):
        return self.get_most_common_pos("NOUN", top_n, exclude_words)

    def print_most_common_nouns(self, top_n = 10, exclude_words=[]):
        self.print_most_common_pos("NOUN", top_n, exclude_words)

    def get_most_common_nouns_and_propns(self, top_n = 10, exclude_words=[]):
        return self.get_most_common_pos("NOUN,PROPN", top_n, exclude_words)

    def print_most_common_nouns_and_propns(self, top_n = 10, exclude_words=[]):
        self.print_most_common_pos("NOUN,PROPN", top_n, exclude_words)

    def get_most_common_adjs(self, top_n = 10, exclude_words=[]):
        return self.print_most_common_pos("ADJ", top_n, exclude_words)
        
    def print_most_common_adjs(self, top_n = 10, exclude_words=[]):
        self.print_most_common_pos("ADJ", top_n, exclude_words)

    def get_most_common_verbs(self, top_n = 10, exclude_words=[]):
        return self.print_most_common_pos("VERB", top_n, exclude_words)

    def print_most_common_verbs(self, top_n = 10, exclude_words=[]):
        self.print_most_common_pos("VERB", top_n, exclude_words)
        
    def get_most_common_adverbs(self, top_n = 10, exclude_words=[]):
        return self.print_most_common_pos("ADV", top_n, exclude_words)
        
    def print_most_common_adverbs(self, top_n = 10, exclude_words=[]):
        self.print_most_common_pos("ADV", top_n, exclude_words)
        
    def print_most_common_noun_chunks(self, top_n = 10, exclude_list=[]):
        """
        Print top_n noun chunks (noun phrases) - potentially giving more context to nouns;
        specify 'None' for all.
        ??? TODO: ** possibly make lower_ and rstrip configurable?
        """
        noun_chunk_list = []
        for doc in self.doc_list:
            for chunk in doc.noun_chunks:
                noun_chunk_str = ''
                if exclude_list == None:
                    noun_chunk_str = chunk.lower_.rstrip(string.punctuation)
                else:
                    for w in chunk.lower_.split():
                        w_no_end_punc = w.rstrip(string.punctuation)
                        if w_no_end_punc not in exclude_list:
                            noun_chunk_str += w_no_end_punc + ' '
                noun_chunk_str = noun_chunk_str.strip()
                if len(noun_chunk_str) > 0:
                    noun_chunk_list.append(noun_chunk_str)
        most_common_noun_chunks = Counter(noun_chunk_list).most_common(top_n)
        print(most_common_noun_chunks)
        
    def print_most_common_dep_trees(self, top_n = 10, exclude_list=[]):
        """
        Print top_n sentence dependency trees - potentially giving more context to text.
        top_n is the number of items to print; specify 'None' for all
        TODO: tidy the output for more meaning.
        """

        if exclude_list != None:
            print("** exclude_list not implemented in order to preserve sentence structure")
        dep_tree_list = []
        for doc in self.doc_list:
            for token in doc:
                if token.lower_ not in string.punctuation:
                    dep_tree_str = " ".join(
                        [token.text, token.dep_, token.head.text, token.head.pos_, "["])
                    child_list = []
                    for child in token.children:
                        if child.lower_ not in string.punctuation:
                            child_list.append(child.lower_.rstrip(string.punctuation))
                    dep_tree_str += ','.join(child_list) + "]"
                    dep_tree_list.append(dep_tree_str)
        most_common_dep_trees = Counter(dep_tree_list).most_common(top_n)
        if top_n:
            print("Top", top_n, end='')
        else:
            print("All", end='')
        print(" dep trees for", self.name, most_common_dep_trees)

def make_synset(word, category='n', number='01'):
    """Conveniently make a synset"""
    number = int(number)
    synset = wn.synset('%s.%s.%02i' % (word, category, number))
    return synset
    
def _recurse_all_hypernyms(synset, all_hypernyms):
    synset_hypernyms = synset.hypernyms()
    if synset_hypernyms:
        all_hypernyms += synset_hypernyms
        for hypernym in synset_hypernyms:
            _recurse_all_hypernyms(hypernym, all_hypernyms)

def all_hypernyms(synset):
    """Get the set of hypernyms of the hypernym of the synset etc.
       Nouns can have multiple hypernyms, so we can't just create a depth-sorted
       list."""
    hypernyms = []
    _recurse_all_hypernyms(synset, hypernyms)
    return set(hypernyms)

def _recurse_all_hyponyms(synset, all_hyponyms, max_depth=None):
    synset_hyponyms = synset.hyponyms()
    if synset_hyponyms:
        all_hyponyms += synset_hyponyms
        if max_depth:
            for level, hyponym in enumerate(synset_hyponyms):
                if (level < max_depth-1):
                    _recurse_all_hyponyms(hyponym, all_hyponyms)
                else: break
        else:
            for hyponym in synset_hyponyms:
                _recurse_all_hyponyms(hyponym, all_hyponyms)
            
def all_hyponyms(synset, max_depth=None):
    """Get the set of the tree of hyponyms under the synset"""
    hyponyms = []
    _recurse_all_hyponyms(synset, hyponyms, max_depth)
    return set(hyponyms)

def all_peers(synset):
    """Get the set of all peers of the synset (including the synset).
       If the synset has multiple hypernyms then the peers will be hyponyms of
       multiple synsets."""
    hypernyms = synset.hypernyms()
    peers = []
    for hypernym in hypernyms:
        peers += hypernym.hyponyms()
    return set(peers)

def synset_word(synset):
    return synset.name().split('.')[0]

def synsets_words(synsets):
    """Get the set of strings for the words represented by the synsets"""
    return set([synset_word(synset) for synset in synsets])

def get_hypernyms(word):
    """
    Get hypernyms for the specified word.
    """
    synset = make_synset(word)
    if synset:
        hypernyms = synsets_words(all_hypernyms(synset))
    else:
        hypernyms = None
    return hypernyms

def get_hyponyms_and_for_peers(word):
    """
    Get hyponyms for the specified word and hyponyms of the word's peers.
    Output appears much too general e.g. for such words as 'work'
    """
    synset = make_synset(word)
    if synset:
        hyponyms = synsets_words(all_hyponyms(synset))
        peers = synsets_words(all_peers(synset))
        hyponyms_of_peers = set()
        for s in all_peers(synset):
            hyponyms_of_peers |= synsets_words(all_hyponyms(s))
        hyponyms_and_for_peers = hyponyms | peers | hyponyms_of_peers
    else:
        hyponyms_and_for_peers = None
    return hyponyms_and_for_peers

def get_hyponyms(word, max_depth=None):
    """
    Get hyponyms for the specified word.
    Use max_depth to specify the level of hyponym to extract
    """
    synset = make_synset(word)
    if synset:
        hyponyms = synsets_words(all_hyponyms(synset, max_depth))
    else:
        hyponyms = None
    return hyponyms

def get_top_word_groups_by_synset_then_similarity(
    nlp, word_freqs, n_word_groups, max_hyponyms, max_hyponym_depth, sim_threshold, user_defined_groups):
    """
    Function to print the top 'n' word "synonym" groups using WordNet synsets followed by
    spaCy similarity:
    - nlp: spaCy object pre-initialised with the required langauge model
    - word_freqs: list of (word,count) tuples in (decreasing) order of frequency
    - n_word_groups: number of word groups to find (specify 'None' means find all word/'synonym' groups)
    - max_hyponyms: the maximum number of hyponyms a word may have before it is ignored (this is used to
      exclude very general words that may not convey useful information - specify 'None' to exclude none)
    - max_hyponym_depth specifies the level of hyponym to extract ('None' means find deepest)
    - sim_threshold: the spaCy similarity level that words must reach to qualify as being a 'synonym'
    - user_defined_groups: initial user-defined groupings. Note that "synonyms" for artificial words, such as
      'love_it', that are not known in the language model (either WordNet or spaCy) can only be matched exactly (as
      clearly no synonym can be found). An additional restriction, is that artifical words must be listed as root
      words and may not have pre-set "synonyms". An alternative where the "synonyms" of each root word is searched 
      for equivalence (or even "synonymity") might be possible but this would come with performance cost.
    Returns list of tuples:
    - (root-word word frequency tuple, list of root and synonym word frequency tuples)
    - (OTHER-word frequency tuple if any are not matched, list of other word frequency tuples)
    - (UNKNOWN-word frequency tuple if any are not found in the language model, list of unknown word frequency tuples)

    Some considerations:
    - The use of WordNet synsets or spaCy similarity by themselves are as useful as required. This is for 2 reasons:
      (1) Some free-text may contain both formal and informal language.
      The advantage of using spaCY with language model 'en_core_web_lg' is that this model was trained on both formal and informal
      language. However, the word vectors in this spaCy language model incorporate all senses of a word and each part of speech. 
    - Hence a combination of WordNet synsets and spaCy similarity is used. WordNet synsets are applied first to parse
      formally defined words, then spaCy similarity is used to catch some other words. A possible further
      refinement might be to take user-defined groupings.
    - It is assumed that 'stop' words and certain artificial words have been removed if required *before* the
      function call (very common words such as "I" that may not be very useful in the word grouping)
    - The language model may contain country-specific, e.g. in the US 'pissed' as the meaning 'angry' but a different meaning in
      UK English.

    Note: spaCy internally uses gloVe word vectors - see citations above.
        
    """

    # Word "lemmatization" is necessary as plurals are not stored in the WordNet synsets
    Lem = WordNetLemmatizer()
    
    # Create a dictionary containing the spaCy token for each word
    # - for later use with spaCy similarity
    document = ''
    for word_freq in word_freqs:
        word, count = word_freq
        document += word + ' '        
    spacy_dict = {}
    for spacy_token in nlp(document):
        word = spacy_token.lower_
        spacy_dict[word] = spacy_token
    #for item in spacy_dict: print("DEBUG: spacy_dict[" + item + "]: " + spacy_dict[item])
    
    # Build a list of most-common word "groups", grouping words that are WordNet "hyponyms"
    most_common = OrderedDict()        # The most common words and their synonyms.
                                       # Note: this needs to be in order of insertion in order to retain the
                                       # frequency order from word_freqs (insertion order is only guaranteed in the
                                       # default dictionaries from CPython 3.6+)
    potential_spelling_errors = set()
    already_grouped = set()            # Words already grouped - either a root word or one of its hyponyms
    first_was_stored = False
    
    if user_defined_groups:
        # Add the user-defined "synonym" groups
        for _tuple in user_defined_groups:
            root_word_tuple, root_and_syn_tuple_list = _tuple
            root_word, root_and_syn_count = root_word_tuple
            root_word = root_word.lower()
            if root_word[0] == '_': root_word = root_word[1:]
            ##print("DEBUG: Adding pre-defined root word '" + root_word + "' with root_and_syn_tuple_list:",
            ##      root_and_syn_tuple_list)
            try:
                lemword = Lem.lemmatize(root_word)
                hyponyms = get_hyponyms(lemword, max_hyponym_depth)
            except WordNetError:
                # Word not known in the WordNet synsets but store it anyway as it's a pre-defined word
                # but mark it as a potential spelling error
                ##print("DEBUG: pre-defined word not known in the WordNet synsets: '" + root_word + "'")
                lemword = root_word
                hyponyms = []
                potential_spelling_errors.add(root_word)
            most_common[root_word] = {}
            most_common[root_word]['root_and_syn_count'] = 0
            most_common[root_word]['root_and_syns'] = root_and_syn_tuple_list
            most_common[root_word]['hyponyms'] = hyponyms
            ##print("DEBUG: with hyponyms:", hyponyms)
            most_common[root_word]['lemmatization'] = lemword
            ##print("DEBUG: and lemmatization:", lemword)
            try:
                most_common[root_word]['root_token'] = spacy_dict[root_word]
            except KeyError:
                # No spaCy token found for the root token so create one
                spaCy_doc_root_word = nlp(root_word)
                spaCy_token_root_word = None
                for item in spaCy_doc_root_word:
                    spaCy_token_root_word = item                        
                most_common[root_word]['root_token'] = spaCy_token_root_word
            already_grouped.add(root_word)
            first_was_stored = True
            for word_tuple in root_and_syn_tuple_list:
                word, word_count = word_tuple
                ##print("DEBUG: with pre-defined synonym: '" + word + "'")
            
    for word_freq in word_freqs:
        word, count = word_freq
        word = word.lower()
        if word not in already_grouped:
            ##print("DEBUG: word: '" + word + "', count: " + str(count))
            if (not first_was_stored):
                try:
                    lemword = Lem.lemmatize(word)
                    hyponyms = get_hyponyms(lemword, max_hyponym_depth)
                    if hyponyms and (max_hyponyms and len(hyponyms) > max_hyponyms):
                        continue
                        ##print("DEBUG: Word '" + word + "'" + "(lemmatized as '" + lemword + "') exceeds hyponym limit")
                    else:
                        # Store the first most common word as the 'root' of the first word group
                        ##print("DEBUG: Adding root word '" + word + "' with hyponyms:", hyponyms)
                        most_common[word] = {}
                        most_common[word]['root_and_syn_count'] = count
                        most_common[word]['root_and_syns'] = [word_freq]
                        most_common[word]['hyponyms'] = hyponyms
                        most_common[word]['lemmatization'] = lemword
                        most_common[word]['root_token'] = spacy_dict[word]
                        already_grouped.add(word)
                        first_was_stored = True
                except WordNetError:
                    ##print("DEBUG: Word not known in the WordNet synsets: '" + word + "'")
                    potential_spelling_errors.add(word)
            else:
                # Store the common word as a new word group if there are no existing "synonyms" in the most_common dictionary
                synonym_or_match_found = False
                for common in most_common:
                    if common == word:
                        # word is already a 'root' word group
                        synonym_or_match_found = True
                    else:
                        if common not in potential_spelling_errors:
                            if word not in already_grouped:
                                lemword = Lem.lemmatize(word)
                                if (lemword == most_common[common]['lemmatization'] or
                                    lemword in most_common[common]['hyponyms']):
                                    # synonym found - incorporate it under the 'root' synonym
                                    synonym_or_match_found = True
                                    most_common[common]['root_and_syn_count'] += count
                                    most_common[common]['root_and_syns'].append(word_freq)
                                    already_grouped.add(word)

                if not synonym_or_match_found:
                    try:
                        lemword = Lem.lemmatize(word)
                        hyponyms = get_hyponyms(lemword, max_hyponym_depth)
                        if hyponyms and (max_hyponyms and len(hyponyms) > max_hyponyms):
                            continue
                            ##print("DEBUG: Word '" + word + "'" + "(lemmatized as '" + lemword + "') exceeds hyponym limit")
                        else:
                            ##print("DEBUG: Adding root word '" + word + "' with hyponyms:", hyponyms)
                            most_common[word] = {}
                            most_common[word]['root_and_syn_count'] = count
                            most_common[word]['root_and_syns'] = [word_freq]
                            most_common[word]['hyponyms'] = hyponyms
                            most_common[word]['lemmatization'] = lemword
                            most_common[word]['root_token'] = spacy_dict[word]
                            already_grouped.add(word)
                    except WordNetError:
                        ##print("DEBUG: Word not known in the WordNet synsets: '" + word + "'")
                        potential_spelling_errors.add(word)

    # Create a spaCy token for a common word such as 'the' - for later use in detecting unknown words
    spaCy_doc_the = nlp("the")
    spaCy_token_the = None
    for item in spaCy_doc_the:
        spaCy_token_the = item                        

    # Now apply spaCy similarity to try to group words for which a hyponym was not found or
    # which were not known in the WordNet synsets ...
    other_words = set()
    for word_freq in word_freqs:
        word, count = word_freq
        if word not in already_grouped:
            other_words.add(word)
            ##print("DEBUG: Adding '" + word + "' not in already_grouped to other_words")
    for word in potential_spelling_errors:
        other_words.add(word)
        ##print("DEBUG: Adding '" + word + "' in potential_spelling_errors to other_words")

    # ... i.e. update the list of most-common word "groups" formed from WordNet synsets with words that have similar
    # enough spaCy token.similarity. Words that were not known in synsets may be known in spaCy so reset the list of
    # potential spelling errors. Note that tokens with a length of 1 are ignored as a work-around for a spaCy
    # token.similarity(other) bug

    potential_spelling_errors = set()
    already_grouped = set()
    first_was_stored = False
    for word_freq in word_freqs:
        word, count = word_freq
        if word in other_words:
            ##print("DEBUG: word in other_words: '" + word + "', count: " + str(count))
            if word not in already_grouped:
                ##print("DEBUG: word not in already_grouped: '" + word + "', count: " + str(count))
                if len(word) > 1: # Work-around for bug in spaCy if token has length of 1
                    synonym_or_match_found = False
                    best_match = None
                    best_match_similarity = 0
                    for common in most_common:
                        if len(common) > 1:    # Work-around for bug in spaCy if token has length of 1
                            common_token = most_common[common]['root_token']
                            try:
                                token = spacy_dict[word]
                            except KeyError:
                                # No spaCy token found for the word so create one
                                spaCy_doc_word = nlp(word)
                                spaCy_token_word = None
                                for item in spaCy_doc_word:
                                    spaCy_token_word = item                        
                                    token = spaCy_token_word
                            ##print("DEBUG: Similarity between token '", token, "' and common item '",
                            ##      common, "' is:", token.similarity(common_token))
                            if (common_token.lower_ == token.lower_):
                                # word is already a 'root' word group
                                synonym_or_match_found = True
                                break
                            else:
                                # check "word" is not a potential spelling error/unknown to spaCy
                                if common_token.lower_ not in potential_spelling_errors:
                                    similarity = token.similarity(common_token)
                                    if similarity >= sim_threshold:
                                        if similarity > best_match_similarity:
                                            best_match = common
                                            best_match_similarity = similarity
                                    elif similarity == 0:
                                        if word not in potential_spelling_errors:
                                            # Check similarity of word against a known word such as'the' in case
                                            # common_token is a word that is known by WordNet but not by spaCy
                                            if token.similarity(spaCy_token_the) == 0:
                                                ##print("DEBUG: Adding potential spelling error for '" + word,
                                                ##      "' - common_token was '" + common_token.lower_ +
                                                ##      "' similarity was " + str(similarity))
                                                potential_spelling_errors.add(word)
                                                break
                    if best_match:
                        # incorporate the word under the 'root' synonym with the best similarity match
                        synonym_or_match_found = True
                        most_common[best_match]['root_and_syn_count'] += count
                        most_common[best_match]['root_and_syns'].append(word_freq)
                        already_grouped.add(word)
                        
    top_word_groups = []
    other_words = []
    for index, word in enumerate(most_common):
        ##print("DEBUG: most_common: index " + str(index) + " word: '" + word + "'")
        if n_word_groups is None or index < n_word_groups:
            word_group_tuple = ("_" + word, most_common[word]['root_and_syn_count'])
            root_and_syns_list = []
            for word_freq in most_common[word]['root_and_syns']:
                root_and_syns_list.append(word_freq)
            top_word_groups.append((word_group_tuple, root_and_syns_list))
        elif word not in potential_spelling_errors:
            other_words.append(word)
    
    if other_words:
        # Words that were not potential spelling errors that did not make it into a word group
        total_other_words = 0
        other_word_freqs = []
        for word in other_words:
            word_count = 0
            for word_freq in word_freqs:
                w, count = word_freq
                if w == word:
                    word_count = count
                    other_word_freqs.append(word_freq)
                    break;
            total_other_words += word_count
        other_word_group_tuple = (_OTHER_GROUP_ROOT_WORD, total_other_words)
        top_word_groups.append((other_word_group_tuple, other_word_freqs))
        
    if len(potential_spelling_errors) > 0:
        # Potential spelling errors / words not in the spaCy model that (may) have been ignored
        total_unknown_words = 0
        unknown_word_freqs = []
        for word in potential_spelling_errors:
            word_count = 0
            for word_freq in word_freqs:
                w, count = word_freq
                if w == word:
                    word_count = count
                    unknown_word_freqs.append(word_freq)
                    break;
            total_unknown_words += word_count
        unknown_word_group_tuple = (_UNKNOWN_GROUP_ROOT_WORD, total_unknown_words)
        top_word_groups.append((unknown_word_group_tuple, unknown_word_freqs))
    
    # Check all words were accounted for
    for word in already_grouped:
        word_found = False
        for word_group in most_common:
            for word_freq in most_common[word_group]['root_and_syns']:
                w, count = word_freq
                if word == w: word_found = True
        if not word_found: print("*** Error: " + word + " not found in most_common")
    
    return top_word_groups


# Print topics by finding words associated with each noun group
def get_words_around(target, text, n_words):
    """
    Helper function for print_words_associated_with_common_noun_groups to return n_words before or
    after each occurence of a word in some text.
    The function returns a list (or lists) of the n_words before and after the 'target' word.
    """
    words = text.lower().rstrip(string.punctuation).split()
    for i,w in enumerate(words):
        if w == target:
            if (i<n_words): yield words[0:i], words[i+1:i+1+n_words]
            else: yield words[i-n_words:i], words[i+1:i+1+n_words]
    
def print_words_associated_with_common_noun_groups(
    nlp, name, free_text_Series, exclude_words, top_n_noun_groups, top_n_words,
    max_hyponyms, max_hyponym_depth, sim_threshold):
    """
    Find the top noun groups (nouns with 'synonyms') in free_text_Series and print the top_n_words associated
    with them:
    - nlp: spaCy object pre-initialised with the required langauge model
    - name: descriptive name for free_text_Series
    - free_text_Series: pandas Series of free_text in which to find the noun groups and associated words
    - exclude_words: to ignore certain words, e.g. not so useful 'stop words' or artificial words.
      This should take one of the following values:
      - True: to ignore NTLK stop-words
      - A list of words to exclude
      - False or None otherwise
    - top_n_noun_groups: number of noun groups to find (specify 'None' means find all noun/'synonym' groups)
    - top_n_words: number of words that are associated with each noun group (specify 'None' for all words)
    - max_hyponyms: the maximum number of hyponyms a word may have before it is ignored (this is used to
      exclude very general words that may not convey useful information)
    - max_hyponym_depth: the the level of hyponym to extract ('None' means find deepest)
    - sim_threshold: the spaCy similarity level that words must reach to qualify as being a 'synonym'
    Notes:
    (1) For best results, stop words should be excluded
    (2) If stop words are excluded, negations such as "no", "not" and words ending with "n't" are still considered
        in the parsing (within the limits of the word context length NUM_CONTEXT_WORDS)
    (3) If no associated word is found, it is assumed the word itself is the only context for the text. For example,
        with noun group "_work", the following free text items would result in the noun itself ('work') being
        reported as an associated word: 'The work that I do', 'Work', 'work.'
        This seems to work in the majority of cases but has not been exhaustively tested. In
        particular, this might give surprising results if the "synonym" matching does not actually give the desired
        synonyms and may give incorrect results if NUM_CONTEXT_WORDS is too short to capture significant context.
        
    Known restrictions/issues:
    (a) The parsing of associated words looks only at words that are up to NUM_CONTEXT_WORDS words before or after
        each noun, inclusive of any exclude words. This limit could be parameterised in this function (it already is
        in helper function 'get_words_around')
    (b) The context words before the noun are parsed first since in the samples tested it appears the "before-words"
        usually give more context than words proceeding a nound. Clearly. this may give sub-optimal results for text
        where the main context for the noun comes in the words following it.
    (c) The parsing of hyphenated words may not always work correctly.
    (d) Spelling mistakes or grammatical errors in the original text may give surprising results.
    (e) See also notes in helper function get_top_word_groups_by_synset_then_similarity and class SpaCyFreeText
    (f) Significantly more testing is required to verify usefulness and robusteness.

    Possible enhancements:
    (i)   NUM_CONTEXT_WORDS could be parameterised, as described above
    (ii)  The output of associated words could be limited to those having a frequency>1
    (iii) Words associated with each noun could be additionally grouped in "valence" sub-groups
    (iv)  For large text, parallelisation would help performance.
    """
    
    text_spaCy = SpaCyFreeText(nlp, name, free_text_Series)
    free_text_list = text_spaCy.get_free_text_list()
    
    exclude_word_list = []
    if exclude_words==True:
        # Exclude 'stop' words and their capitalisations
        stop_words = stopwords.words('english')
        for word in stop_words: exclude_word_list.append(word)
        capitalized_stop_words = [w.capitalize() for w in stop_words]
        for word in capitalized_stop_words: exclude_word_list.append(word)
    elif exclude_words:
        exclude_word_list = exclude_words
    ##if exclude_words:
    ##    print("DEBUG: Words that will be excluded:", exclude_word_list)
    
    # Get frequencies of all nouns and proper nouns in the free-text Series
    all_noun_and_propn_freqs = text_spaCy.get_most_common_nouns_and_propns(None, exclude_word_list)
    print(str(len(all_noun_and_propn_freqs)), "unique nouns/proper nouns found")
    
    # Get "synonym" groupings of the nouns and proper nouns (either wordnet hyponyms or spaCy similarity)"
    top_word_groups = get_top_word_groups_by_synset_then_similarity(
        nlp, all_noun_and_propn_freqs, top_n_noun_groups, max_hyponyms, max_hyponym_depth, sim_threshold, None)
    
    NUM_CONTEXT_WORDS = 4
    if top_n_words:
        print("Top", top_n_words, "words", end='')
    else:
        print("Words", end='')
    print(" associated with nouns/proper noun groupings, looking at up to",
          str(NUM_CONTEXT_WORDS), "words before or after each noun:")

    ##print("DEBUG: top_word_groups", top_word_groups)
    for item in top_word_groups:
        root_word_freq, group_word_freqs = item
        root_word, root_word_count = root_word_freq
        if root_word != _OTHER_GROUP_ROOT_WORD and root_word != _UNKNOWN_GROUP_ROOT_WORD:
            NO_WORD = "no_word"
            assoc_word_list = [] # List of associated words for each noun/proper nount group
            for word_freq in group_word_freqs:
                word, count = word_freq
                for free_text in free_text_list:
                    if word in free_text.lower().rstrip(string.punctuation).split():
                        ##print("DEBUG:--------------------------------------------------------------------------------")
                        ##print("DEBUG: free_text: '" + free_text + "'")
                        for before_words, after_words in get_words_around(word, free_text, NUM_CONTEXT_WORDS):
                            ##print("DEBUG: word(s) before '" + word + "': ", before_words)
                            ##print("DEBUG: word(s) after '" + word + "': ", after_words)
                            # First try to find an associated word in words before the noun word
                            assoc_word = None
                            before_words_len = len(before_words)
                            for index in range(before_words_len):
                                before_word = before_words[before_words_len-index-1]
                                if not before_word or before_word in string.punctuation: break
                                elif before_word == "not" or before_word[-3:] == "n't":
                                    negation = "not"
                                    if index != 0 and before_words[before_words_len-index] != word:
                                        negation = negation + "_" + before_words[before_words_len-index]
                                    assoc_word = negation
                                    ##print("DEBUG: negation '" + negation + "' added to assoc_word_list for word '" +
                                    ##      word + "' in free_text '" + free_text + "'")
                                    break
                                elif before_word == "no":
                                    negation = "no"
                                    if index != 0 and before_words[before_words_len-index] != word:
                                        negation = negation + "_" + before_words[before_words_len-index]
                                    assoc_word = negation
                                    ##print("DEBUG: negation '" + negation + "' added to assoc_word_list for word '" +
                                    ##      word + "' in free_text '" + free_text + "'")
                                    break
                                elif before_word not in exclude_word_list:
                                    word_before_before_word = before_words[before_words_len-index-2]
                                    if word_before_before_word:
                                        if word_before_before_word == "not" or word_before_before_word[-3:] == "n't":
                                            negation = "not_" + before_word
                                            assoc_word = negation
                                            ##print("DEBUG: negation of before_word '" + negation + "' added to assoc_word_list for word '" +
                                            ##      word + "' in free_text '" + free_text + "'")
                                            break
                                        else:
                                            assoc_word = before_word
                                            ##print("DEBUG: before_word '" + before_word + "' added to assoc_word_list for word '" +
                                            ##      word + "' in free_text '" + free_text + "'")
                                            break
                            if not assoc_word:
                                # Try to find an associated word following the noun word
                                after_words_len = len(after_words)
                                for index in range(after_words_len):
                                    after_word = after_words[index]
                                    if not after_word or after_word in string.punctuation: break
                                    elif after_word == "not" or after_word[-3:] == "n't":
                                        if (index+1 < after_words_len):
                                            word_after_after_word = after_words[index+1]
                                            negation = "not_" + word_after_after_word
                                            assoc_word = negation
                                            ##print("DEBUG: negation '" + negation + "' added to assoc_word_list for word '" +
                                            ##      word + "' in free_text '" + free_text + "'")
                                        break
                                    elif after_word == "no":
                                        if (index+1 < after_words_len):
                                            word_after_after_word = after_words[index+1]
                                            negation = "no_" + word_after_after_word
                                            assoc_word = negation
                                            ##print("DEBUG: negation '" + negation + "' added to assoc_word_list for word '" +
                                            ##      word + "' in free_text '" + free_text + "'")
                                        break
                                    elif after_word not in exclude_word_list:
                                        assoc_word_list.append(after_word)
                                        assoc_word = after_word
                                        ##print("DEBUG: after_word '" + after_word + "' added to assoc_word_list for word '" +
                                        ##      word + "' in free_text '" + free_text + "'")
                                        break
                        if not assoc_word:
                            # Assume the word itself is the only context for the text - see Notes above
                            assoc_word = word
                            ##if word == root_word:
                            ##    print("DEBUG: Topic identified: " + root_word + " for '" + free_text + "'")
                            ##else:
                            ##    print("DEBUG: Topic identified: " + root_word + ": " + word + " for '" + 
                            ##          free_text + "'")
                        ##else:
                        ##    print("DEBUG: Topic identified: " + root_word + ": " + assoc_word + "_" + word
                        ##          + " for '" + free_text + "'")
                        assoc_word_list.append(assoc_word)
                        
            most_common_words = Counter(assoc_word_list).most_common(top_n_words)
            ##print("DEBUG: assoc_word_list:", assoc_word_list)
            print("'" + root_word + "', " + str(root_word_count) + ": ", end='')
            print(most_common_words, end='')
            print("    {", end='')
            for word_freq in group_word_freqs:
                word, count = word_freq
                print("('" + word + "', " + str(count) + "), ", end='')
            print("}")