import json
import sys
from contextlib import contextmanager
from pathlib import Path

import langdetect
import regex
import spacy
from argser import SubCommands
from spacy.language import Language


sub = SubCommands()


def validate_files(*files):
    for f in files:
        if not f.exists():
            raise SystemExit(f"file {f} doesn't exist")


def read_text_file(filepath: Path) -> str:
    # todo: read doc(x), pdf, etc
    return filepath.read_text()


def load_spacy(lang) -> Language:
    lookup_file = Path('.spacy_lookup')
    if lookup_file.exists():
        lookup = json.loads(lookup_file.read_text())
    else:
        lookup = {'blank': []}

    if lang in lookup['blank']:
        nlp = spacy.blank(lang)
        nlp.add_pipe(nlp.create_pipe('sentencizer'))
        return nlp

    try:
        return spacy.load(lang, disable=('tagger', 'ner'))
    except OSError as e:
        print(e, file=sys.stderr)
        try:
            spacy.cli.download(lang)
        except SystemExit:
            lookup['blank'].append(lang)
            lookup_file.write_text(json.dumps(lookup))
            return spacy.blank(lang)
        return load_spacy(lang)


@contextmanager
def open_file(output):
    if isinstance(output, (str, Path)):
        with open(output, 'w') as file:
            yield file
    else:
        yield sys.stdout


def normalize_sentence(text: str):
    text = text.strip('\n ')
    text = regex.sub(r'[^a-zA-Z\p{IsCyrillic}\s,.?!;]', '', text)
    return text


def split_compound_sentence(sent: str, nlp: Language):
    return [sent]


@sub.add(name='split', help='split provided file into sentences')
def split_sentence(file: str, output: str = None):
    """
    :param file: path to the documents
    :param output: path for output, default stdout
    :return: sentences
    """
    file, output = Path(file), Path(output)
    validate_files(file)
    text = read_text_file(file)
    lang = langdetect.detect(text[:1000])
    nlp = load_spacy(lang)
    doc = nlp(text)
    sentences = []
    with open_file(output) as f:
        for sent in doc.sents:
            norm_sent = normalize_sentence(sent.text)
            for sent_text in split_compound_sentence(norm_sent, nlp):
                print(sent_text, file=f)
                sentences.append(sent_text)
    return sentences


def main():
    sub.parse(parser_prog='ontogen')


if __name__ == '__main__':
    main()
