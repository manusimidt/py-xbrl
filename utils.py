from __future__ import annotations

from typing import List


def remove_tag(text: str, tag) -> str:
    return text.split('<{}>'.format(tag), 1)[1].strip()[:-len('</{}>'.format(tag))]


class Document:
    file_name: str
    sequence: str
    contents: str

    def __init__(self, metadata_text, document_text):
        metadata = {
            k.lower():  v for k, v in [tuple(s.split('>')) for s in metadata_text.replace('<', '').split('\n') if s]
        }
        self.file_name = metadata['filename']
        self.sequence = metadata['sequence']
        self.contents = document_text

    def get_contents_without_tag(self, tag: str) -> str:
        return remove_tag(self.contents, tag)

    @staticmethod
    def get_documents_from_submission_file(complete_submission_text_file: str) -> List[Document]:
        documents = [d.strip()[:-len('</DOCUMENT>')] for d in complete_submission_text_file.split('<DOCUMENT>')]
        documents = [
            Document(m, t.strip()[:-len('</TEXT>')]) for m, t in
            [tuple(d.split('<TEXT>', 1)) for d in documents[1:]]
        ]
        return documents
