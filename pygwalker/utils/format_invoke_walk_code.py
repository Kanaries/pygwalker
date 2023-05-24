from typing import Optional
import ast

import astor


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

    return astor.to_source(func)


def get_formated_spec_params_code(code: str) -> str:
    call_func = _find_walk_func_node(code)
    if call_func is None:
        return ''
    return _repalce_spec_params_code(call_func)
