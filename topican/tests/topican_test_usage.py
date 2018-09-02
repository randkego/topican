# coding: utf-8

# topican_test_usage.py
# =====================
#
# Python script to show topican usage

import pandas as pd
df = pd.DataFrame({'Text_col' : ["I love Python!", "I like python.", "python", "I like C++ but I prefer Python", "I don't like C++ any more", "C++"]})

# Load spaCy's large English language model (the large model is required to be able to use similarity)
# Warning: this requires approx 2GB of RAM
import spacy
nlp = spacy.load('en_core_web_lg')

import topican
topican.print_words_associated_with_common_noun_groups(nlp, "test", df['Text_col'], True, 10, None, 100, 1, 0.7)
