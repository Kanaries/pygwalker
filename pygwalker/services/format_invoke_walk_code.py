from typing import Optional, List, Any
from types import FrameType
from lib2to3 import fixer_base, refactor
import logging
import inspect
import ast

from astor.source_repr import split_lines
import astor

_MAX_LINE = 150

logger = logging.getLogger(__name__)


class StatementScraper(fixer_base.BaseFix):
    """StatementScraper"""
    PATTERN = 'simple_stmt'

    def __init__(self, lineno):
        super().__init__(None, None)
        self.lineno = lineno
        self.statement = ''

    def transform(self, node: Any, results: Any) -> Any:
        if not self.statement and self.lineno - node.get_lineno() < str(node).count('\n'):
            prev_sibling = str(node.prev_sibling)
            if prev_sibling.isspace():
                self.statement += prev_sibling.lstrip('\n')
            self.statement += str(node)
        return node


class InvokeCodeParser(refactor.RefactoringTool):
    """
    Parse the code and get the invoke code.
    TODO: temporary solution, need to be improved.
    """
    def __init__(self, frame: FrameType):
        self.source = inspect.getsource(frame)
        self.scraper = StatementScraper(frame.f_lineno)
        super().__init__(None)

    def get_fixers(self):
        return [self.scraper], []

    def __str__(self):
        self.refactor_string(self.source, '')
        return self.scraper.statement


def _find_walk_func_node(code: str) -> Optional['ast.Call']:
    node_list = [ast.parse(code)]
    while node_list:
        cur_node = node_list.pop()
        if isinstance(cur_node, ast.Call):
            if isinstance(cur_node.func, ast.Name):
                func_name = cur_node.func.id
            else:
                func_name = cur_node.func.attr
            if func_name == 'walk':
                return cur_node
        for node_info in astor.iter_node(cur_node):
            if isinstance(node_info[0], list):
                nodes = node_info[0]
            else:
                nodes = [node_info[0]]

            for children_node in nodes:
                node_list.append(children_node)


def _private_astor_pretty_source(source: List[str]) -> str:
    return "".join(split_lines(source, maxline=_MAX_LINE))


def _repalce_spec_params_code(func: 'ast.Call') -> str:
    replace_value = ast.Constant(value='____pyg_walker_spec_params____')
    spec_index = -1
    for index, keyword in enumerate(func.keywords):
        if keyword.arg == 'spec':
            spec_index = index
    if spec_index != -1:
        func.keywords[spec_index].value = replace_value
    else:
        func.keywords.insert(0, ast.keyword(arg='spec', value=replace_value))

    return astor.to_source(func, pretty_source=_private_astor_pretty_source)


def _get_default_code() -> str:
    logger.warning("parse invoke code failed, This may affect feature of export code.")
    return "pyg.walk(df, spec='____pyg_walker_spec_params____')"


def get_formated_spec_params_code(code: str) -> str:
    call_func = _find_walk_func_node(code.strip())
    if call_func is None:
        return ''
    return _repalce_spec_params_code(call_func)


def get_formated_spec_params_code_from_frame(frame: FrameType) -> str:
    try:
        source_invoke_code = get_formated_spec_params_code(
            str(InvokeCodeParser(frame))
        )
    except Exception:
        return _get_default_code()

    if source_invoke_code == '':
        return _get_default_code()

    return source_invoke_code
