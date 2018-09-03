# Topican - topic analyzer

```python3
topican.print_words_associated_with_common_noun_groups
```
Identifies topics by assuming a topics can be identified from Nouns and a "context" word:  
- spaCy is used to identify Nouns (including Proper nouns) in the text  
- nltk WordNet and spaCy are used to group similar nouns together (WordNet "hyponyms" are checked first; spaCy similarity is used if a hyponym is not found)  
- the top context words are found for each noun  
- Output is a list of noun groups and associated context words, in order of frequency  

For example, the text "I like python", "I love Python", and "I like C" would be analysed as having 2 topic groups:

    '_python', 2: \[('like', 1), ('love', 1),] 
    '_C', 1: [('like', 1), ] 

## Meta
Richard Smith – randkego@gmail.com

Distributed under the MIT license. See ``LICENSE`` for more information.

[https://github.com/randkego/topican](https://github.com/randkego/topican)

## Installation

Pre-requisites:

```sh
# Required packages
pip3 install pandas
pip3 install nltk
pip3 install spacy

# Install spaCy's large English language model
# ** Warning: this requires approx 1GB of disk space
python3 -m spacy download en_core_web_lg
```

Topican:

```sh
pip3 install topican
```

## Usage

```python3
topican.print_words_associated_with_common_noun_groups(
    nlp, name, free_text_Series, exclude_words, top_n_noun_groups, top_n_words, max_hyponyms, max_hyponym_depth, sim_threshold)
```
- nlp: spaCy nlp object - this must be initialised with a language model that includes the word vectors
- name: descriptive name for free_text_Series
- free_text_Series: pandas Series of text in which to find the noun groups and associated words
- exclude_words: to ignore certain words, e.g. not so useful 'stop words' or artificial words.  
  This should take one of the following values:  
&nbsp;&nbsp;&nbsp;&nbsp;- True: to ignore NTLK stop-words and their capitalizations  
&nbsp;&nbsp;&nbsp;&nbsp;- A list of words to exclude  
&nbsp;&nbsp;&nbsp;&nbsp;- False or None otherwise
- top_n_noun_groups: number of noun groups to find ('None' means find all noun/'synonym' groups)
- top_n_words: number of words that are associated with each noun group (specify 'None' for all words)
- max_hyponyms: the maximum number of hyponyms a word may have before it is ignored (this is used to
  exclude very general words that may not convey useful information)
- max_hyponym_depth: the level of hyponym to extract ('None' means find deepest)
- sim_threshold: the spaCy similarity level that words must reach to qualify as being a similar word

## Usage example

```python3
# Some text to test
import pandas as pd
test_df = pd.DataFrame({'Text_col' : ["I love Python", "I really love python", "I like python.", "python", "I like C but I prefer Python", "I don't like C any more", "I don't like python", "I really don't like C"]})

# Load spaCy's large English language model (the large model is required to be able to use similarity)
# ** Warning: this requires approx 2GB of RAM
import spacy
nlp = spacy.load('en_core_web_lg')

import topican
topican.print_words_associated_with_common_noun_groups(nlp, "test", test_df['Text_col'], False, 10, None, 100, 1, 0.7)
```
![](readme_usage_output.png)

## Release History

* 0.0.17
    * Work in progress

## Contributing

1. Fork it (<https://github.com/randkego/topican/fork>)
2. Create your feature branch (`git checkout -b feature/fooBar`)
3. Commit your changes (`git commit -am 'Add some fooBar'`)
4. Push to the branch (`git push origin feature/fooBar`)
5. Create a new Pull Request

<!-- Markdown link & img dfn's -->
[wiki]: https://github.com/randkego/topican/wiki
