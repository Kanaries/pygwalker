from pygwalker.utils.format_invoke_walk_code import get_formated_spec_params_code


def test_get_formated_spec_params_code():
    empty_code = ""
    assert get_formated_spec_params_code(empty_code) == ""

    normal_code = "pygwalker.walk(df, env='Streamlit')"
    normal_code_result = "pygwalker.walk(df, spec='____pyg_walker_spec_params____', env='Streamlit')\n"
    assert get_formated_spec_params_code(normal_code) == normal_code_result

    new_line_code = "\t\n\npygwalker.walk(df, \n\tenv='Streamlit')\n\n"
    new_line_code_result = "pygwalker.walk(df, spec='____pyg_walker_spec_params____', env='Streamlit')\n"
    assert get_formated_spec_params_code(new_line_code) == new_line_code_result
