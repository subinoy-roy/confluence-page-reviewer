"""
Shared HTML → markdown converter used by confluence_api.py and docx_parser.py.
Pure stdlib — no external dependencies.
"""

import re
from html.parser import HTMLParser


class _HtmlToMarkdown(HTMLParser):
    HEADING_TAGS = {'h1': 1, 'h2': 2, 'h3': 3, 'h4': 4, 'h5': 5, 'h6': 6}
    BLOCK_TAGS = {'p', 'div', 'ul', 'ol', 'blockquote', 'pre', 'section',
                  'article', 'header', 'footer', 'main', 'aside', 'nav'}
    SKIP_TAGS = {'style', 'script', 'head', 'meta', 'link', 'noscript'}

    def __init__(self):
        super().__init__()
        self.buf = []
        self._skip_depth = 0
        self._table_depth = 0
        self._in_cell = False
        self._cell_buf = []
        self._row_cells = []
        self._table_rows = []
        self._list_depth = 0
        self._ordered = []
        self._counters = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return

        if tag in self.HEADING_TAGS:
            level = self.HEADING_TAGS[tag]
            self.buf.append(f'\n\n{"#" * level} ')
        elif tag == 'br':
            self.buf.append('\n')
        elif tag in self.BLOCK_TAGS:
            if not self._in_cell:
                self.buf.append('\n\n')
        elif tag == 'li':
            indent = '  ' * max(self._list_depth - 1, 0)
            if self._ordered and self._ordered[-1]:
                self._counters[-1] += 1
                self.buf.append(f'\n{indent}{self._counters[-1]}. ')
            else:
                self.buf.append(f'\n{indent}- ')
        elif tag == 'ul':
            self._list_depth += 1
            self._ordered.append(False)
            self._counters.append(0)
        elif tag == 'ol':
            self._list_depth += 1
            self._ordered.append(True)
            self._counters.append(0)
        elif tag == 'table':
            self._table_depth += 1
            if self._table_depth == 1:
                self._table_rows = []
        elif tag == 'tr':
            if self._table_depth == 1:
                self._row_cells = []
        elif tag in ('td', 'th'):
            if self._table_depth == 1:
                self._in_cell = True
                self._cell_buf = []

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self._skip_depth = max(self._skip_depth - 1, 0)
            return
        if self._skip_depth:
            return

        if tag in self.HEADING_TAGS:
            self.buf.append('\n')
        elif tag in ('ul', 'ol'):
            self._list_depth = max(self._list_depth - 1, 0)
            if self._ordered:
                self._ordered.pop()
            if self._counters:
                self._counters.pop()
            self.buf.append('\n')
        elif tag in self.BLOCK_TAGS:
            if not self._in_cell:
                self.buf.append('\n\n')
        elif tag in ('td', 'th'):
            if self._table_depth == 1:
                cell_text = ''.join(self._cell_buf).replace('|', '\\|').replace('\n', ' ').strip()
                self._row_cells.append(cell_text)
                self._in_cell = False
                self._cell_buf = []
        elif tag == 'tr':
            if self._table_depth == 1 and self._row_cells:
                self._table_rows.append(self._row_cells[:])
                self._row_cells = []
        elif tag == 'table':
            if self._table_depth == 1:
                self._flush_table()
            self._table_depth = max(self._table_depth - 1, 0)

    def _flush_table(self):
        if not self._table_rows:
            return
        self.buf.append('\n\n')
        header = self._table_rows[0]
        self.buf.append('| ' + ' | '.join(header) + ' |\n')
        self.buf.append('| ' + ' | '.join('---' for _ in header) + ' |\n')
        for row in self._table_rows[1:]:
            padded = row + [''] * max(0, len(header) - len(row))
            self.buf.append('| ' + ' | '.join(padded[:len(header)]) + ' |\n')
        self.buf.append('\n')
        self._table_rows = []

    def handle_data(self, data):
        if self._skip_depth:
            return
        if self._in_cell:
            self._cell_buf.append(data)
        else:
            self.buf.append(data)

    def get_text(self):
        text = ''.join(self.buf)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()


def html_to_markdown(html):
    parser = _HtmlToMarkdown()
    parser.feed(html)
    return parser.get_text()
