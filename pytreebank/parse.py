import codecs
import os

from collections import OrderedDict

from .labeled_trees import LabeledTree
from .download import download_sst
from .utils import makedirs, normalize_string

class ParseError(ValueError):
    pass

def attribute_text_label(node, current_word):
    node.text = normalize_string(current_word)
    node.text = node.text.strip(" ")
    node.udepth = 1
    if len(node.text) > 0 and node.text[0].isdigit():
        split_sent = node.text.split(" ", 1)
        label = split_sent[0]
        if len(split_sent) > 1:
            text = split_sent[1]
            node.text = text

        if all(c.isdigit() for c in label):
            node.label = int(label)
        else:
            text = label + " " + text
            node.text = text

    if len(node.text) == 0:
        node.text = None


def create_tree_from_string(line):
    depth         = 0
    current_word  = ""
    root          = None
    current_node  = root

    for char in line:
        if char == '(':
            if current_node is not None and len(current_word) > 0:
                attribute_text_label(current_node, current_word)
                current_word = ""
            depth += 1
            if depth > 1:
                # replace current head node by this node:
                child = LabeledTree(depth=depth)
                current_node.add_child(child)
                current_node = child
                root.add_general_child(child)
            else:
                root = LabeledTree(depth=depth)
                root.add_general_child(root)
                current_node = root

        elif char == ')':
            # assign current word:
            if len(current_word) > 0:
                attribute_text_label(current_node, current_word)
                current_word = ""

            # go up a level:
            depth -= 1
            if current_node.parent != None:
                current_node.parent.udepth = max(current_node.udepth+1, current_node.parent.udepth)
            current_node = current_node.parent
        else:
            # add to current read word
            current_word += char
    if depth != 0:
        raise ParseError("Not an equal amount of closing and opening parentheses")

    return root



class LabeledTreeCorpus(list):
    """
    Read in the Stanford Sentiment Treebank using the original serialization format:

    > (3 (2 this) (3 (2 is) (3 good ) )

    """
    def labels(self):
        labelings = OrderedDict()
        for tree in self:
            for label, line in tree.to_labeled_lines():
                labelings[line] = label
        return labelings

    def to_file(self, path, mode = "w"):
        with open(path, mode = mode) as f:
            for tree in self:
                for label, line in tree.to_labeled_lines():
                    f.write(line + "\n")



def import_tree_corpus(trees):
    tree_list = LabeledTreeCorpus()
    with codecs.open(trees, "r", "UTF-8") as f:
        for line in f:
            tree_list.append(create_tree_from_string(line))
    return tree_list


def load_sst(path=None,
             url='http://nlp.stanford.edu/sentiment/trainDevTestTrees_PTB.zip'):
    if path is None:
        # find a good temporary path
        path = os.path.expanduser("~/stanford_sentiment_treebank/")
        makedirs(path, exist_ok=True)
    fnames = download_sst(path, url)
    return {key: import_tree_corpus(value) for key, value in fnames.items()}

