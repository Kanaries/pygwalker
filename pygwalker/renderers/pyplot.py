import base64
import io
import json
from typing import Dict, List

from pygwalker._typing import DataFrame
from pygwalker.renderers.base import MEA_KEY_FID, MEA_VAL_FID, CodeStorage, auto_mark, get_color_palette, get_fid_with_agg, get_fold_fields, get_name_with_agg, get_primary_color, get_spec_color_palette, pick_first
import matplotlib
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import itertools
import matplotlib.patches as mpatches
import numpy as np

def change_color_string_key(color_string: str | None, new_key: str):
    if color_string:
        color_string = color_string.replace('c=', f'{new_key}=')
    return color_string

def with_quote(str:str):
    if str:
        return json.dumps(str)
    return str

def get_field_string(key: str, df_name: str, field: Dict[str, any], is_agg: bool, fallback = ""):
    fid = get_fid_with_agg(field, is_agg)
    if fid:
        semanticType = field.get("semanticType")
        if semanticType == 'temporal':
            return f"{key}{'=' if key else ''}{df_name}[{with_quote(fid)}].astype('datetime64[s]'),"
        return f"{key}{'=' if key else ''}{df_name}[{with_quote(fid)}],"
    if fallback:
        return f"{key}{'=' if key else ''}{fallback},"
    return ""
def get_field_string_simple(df_name: str, fid: str, fallback = ""):
    if fid:
        return f"{df_name}[{with_quote(fid)}]"
    if fallback:
        return f"{fallback}"
def get_dimension_count_string(df_name: str, id: str,fields: List[Dict[str, any]], is_agg: bool):
    if len(fields) == 0:
        return (f"{id} = []\n{id}_dims = 0\n{id}_nums = 1\n{id}_fields = [('','')]", [])
    dims = [field for field in fields if field.get("analyticType") == 'dimension']
    meas = [field for field in fields if field.get("analyticType") == 'measure']
    if len(meas) > 0:
        axis_fields = meas
        facet_fields = dims
    else:
        axis_fields = [dims[-1]]
        facet_fields = dims[:-1]
    if len(facet_fields) > 0:
        dim_fields = f"{id} = list(itertools.product(" + ",".join([f"{df_name}[{with_quote(get_fid_with_agg(field, is_agg))}].unique()" for field in facet_fields]) + "))"
        dim_nums = f"{id}_dims = {len(facet_fields)}"
        dim_actual_nums = f"{id}_nums = len({id})"
    else:
        dim_fields = f"{id} = []"
        dim_nums = f"{id}_dims = 0"
        dim_actual_nums = f"{id}_nums = 1"
    return (f"{dim_fields}\n{dim_nums}\n{dim_actual_nums}", facet_fields, axis_fields)

def build_code(payload: Dict[str, any], size: Dict[str, int], df_name = 'df', numpy_name = 'np', instance_name='plt'):
    code_storage = CodeStorage()
    # code_storage.add_code(f"import matplotlib.pyplot as plt")
    config = payload.get("config")
    layout = payload.get("layout")
    mark = config.get("geoms")[0]
    is_aggergated = config.get("defaultAggregated")
    encodings = payload.get("encodings")
    if mark == "auto":
        mark = auto_mark([field.get("semanticType") for field in encodings.get("rows") + encodings.get("columns")])
        
    if size:
        width = size.get("width")
        height = size.get("height")
        if width > 0 and height > 0:
            plt.figure(dpi=100, figsize=(width / 100, height / 100))

    x_channels = encodings.get("columns")
    y_channels = encodings.get("rows")
    color_channel = encodings.get("color")
    opacity_channel = encodings.get("opacity")
    size_channel = encodings.get("size")
    text_channel = encodings.get("text")
    shape_channel = encodings.get("shape")
    
    fold_fields = get_fold_fields(payload)
    if (len(fold_fields) > 0):
        code_storage.add_code(f"folded_df = {df_name}.melt(id_vars=list(set({df_name}.columns.to_list())-set({json.dumps(fold_fields)})), value_vars={json.dumps(fold_fields)}, var_name={with_quote(MEA_KEY_FID)}, value_name={with_quote(MEA_VAL_FID)})")
        df_name = 'folded_df'
    
    stack = layout.get("stack")
    zero_scale = layout.get("zeroScale")

    fid_color = get_fid_with_agg(pick_first(color_channel), is_aggergated)
    fid_opacity = get_fid_with_agg(pick_first(opacity_channel), is_aggergated)
    fid_size = get_fid_with_agg(pick_first(size_channel), is_aggergated)
    fid_text = get_fid_with_agg(pick_first(text_channel), is_aggergated)
    fid_shape = get_fid_with_agg(pick_first(shape_channel), is_aggergated)
    color_palette = None
    colorbar_string = ''
    primary_color = None
    color_type = 'category'
    if fid_color is None:
        primary_color = get_primary_color(payload)
        if primary_color:
            # extract rgba from primary_color string 'rgba(r,g,b,a)' like rgba(112, 0, 255, 1), transform into hex
            rgb_values = primary_color[5:-1].split(',')[:3]  # Take only RGB values
            primary_color = '#%02x%02x%02x' % tuple(map(int, rgb_values))
        else:
            primary_color = '#5b8ff9'
    else:
        color_field = pick_first(color_channel)
        color_palette = get_spec_color_palette(payload)
        if color_field.get("semanticType") == "quantitative" or color_field.get("semanticType") == "temporal":
            if color_palette is None:
                color_palette = get_color_palette('blues')
            code_storage.add_code(f"color_map = LinearSegmentedColormap.from_list('palette',{json.dumps(color_palette)})")
            colorbar_string = f'{instance_name}.colorbar()'
            color_type = 'linear'
        else:
            if color_palette is None:
                color_palette = get_color_palette('category10')
            code_storage.add_code(f"cp = {json.dumps(color_palette)}")
            if mark != 'rect':
                # rect plot have a speical color map
                code_storage.add_code(f"unique_color = {df_name}[{with_quote(fid_color)}].unique()")
                code_storage.add_code(f"color_map = dict(zip(unique_color, itertools.cycle(cp)))")
            colorbar_string = f"{instance_name}.legend([mpatches.Patch(color=color, label=label) for (label, color) in color_map.items()], unique_color, loc=1, title={with_quote(get_name_with_agg(color_channel[0], is_aggergated))})"
            color_type = 'category'
    def get_color_string(df_name):
        if fid_color:
            if color_type == 'category':
                return f"c={df_name}[{with_quote(fid_color)}].map(color_map),"
            else:
                return f"c={df_name}[{with_quote(fid_color)}],cmap=color_map,"
        return f"color={with_quote(primary_color)}, "
    def get_opacity_string(df_name, ax_name):
        if fid_opacity:
            opacity_field = pick_first(opacity_channel)
            semanticType = opacity_field.get("semanticType")
            opacity_string = f""
            alpha_type = ""
            if semanticType == 'quantitative' or semanticType == 'temporal':
                code_storage.add_code(f"alpha = {df_name}[{with_quote(fid_opacity)}]")
                opacity_string = f"alpha=(alpha - alpha.min()) / (alpha.max() - alpha.min()) * 0.7 + 0.3,"
                opacity_bar_string = f"{ax_name}.figure.colorbar(ScalarMappable(norm=Normalize(vmin={df_name}[{with_quote(fid_opacity)}].min(), vmax={df_name}[{with_quote(fid_opacity)}].max()), cmap='Greys'), ax={ax_name}, label={with_quote(get_name_with_agg(opacity_field, is_aggergated))})"
                alpha_type = 'linear'
            else:
                code_storage.add_code(f"alpha = {df_name}[{with_quote(fid_opacity)}]")
                code_storage.add_code("unique_alpha = alpha.unique()")
                code_storage.add_code(f"alpha_map = dict(zip(unique_alpha, np.linspace(0.3, 1, len(unique_alpha))))")
                opacity_string = f"alpha=alpha.map(alpha_map),"
                opacity_bar_string = f"opacity_legend = {ax_name}.legend([mpatches.Patch(color='gray', label=label, alpha=alpha) for (label, alpha) in alpha_map.items() if isinstance(label, str)], unique_alpha, loc=4, title={with_quote(get_name_with_agg(opacity_field, is_aggergated))})\n{ax_name}.add_artist(opacity_legend)"
                alpha_type = 'category'
            return (opacity_string, opacity_bar_string, alpha_type)
        return ('', '', None)

    def plot_square_single(ax_name, fig_name, df_name, x_field, y_field):
        fid_x = get_fid_with_agg(x_field, is_aggergated)
        fid_y = get_fid_with_agg(y_field, is_aggergated)
        x_string = f"columns={with_quote(fid_x)}, " if fid_x else ''
        y_string = f"index={with_quote(fid_y)}, " if fid_y else ''
        color_string = ''
        colorbar_string = ''
        opacity_bar_string = ''
        imdata = "data"

        if fid_color:
            if color_type == 'category':
                code_storage.add_code(f"data = {df_name}.pivot_table({y_string}{x_string}values={with_quote(fid_color)}, aggfunc=lambda x: ','.join(sorted(set(x))))")
                code_storage.add_code(f"unique_color = data.unstack().unique()")
                code_storage.add_code(f"color_map = dict(itertools.chain(zip(unique_color, itertools.cycle(cp)), [({numpy_name}.nan, '#0000')]))")
                map_func = 'to_rgb' if fid_opacity else 'to_rgba'
                reshape = '(3,)' if fid_opacity else '(4,)'
                code_storage.add_code(f"imdata = np.array(list(data.replace(color_map).map({instance_name}.matplotlib.colors.{map_func}).map(list).values.flatten())).reshape(data.shape + {reshape})")
                colorbar_string = f"{ax_name}.legend([mpatches.Patch(color=color, label=label) for (label, color) in color_map.items() if isinstance(label, str)], [label for label in color_map if isinstance(label, str)], loc=1, title={with_quote(get_name_with_agg(color_channel[0], is_aggergated))})"
                imdata = "imdata"
            else:
                code_storage.add_code(f"data = {df_name}.pivot_table({y_string}{x_string}values={with_quote(fid_color)})")
                color_string = f"cmap=color_map, "
                colorbar_string = f"{ax_name}.figure.colorbar(im, label={with_quote(get_name_with_agg(color_channel[0], is_aggergated))})"
        else:
            group_y_string = f"{with_quote(fid_y)}," if fid_y else ''
            group_x_string = f"{with_quote(fid_x)}," if fid_x else ''
            if x_field is None:
                code_storage.add_code(f"data = {df_name}.pivot_table(index={group_y_string}aggfunc='size').to_frame()")
            elif y_field is None:
                code_storage.add_code(f"data = {df_name}.pivot_table(index={group_x_string}aggfunc='size').to_frame().T")
            else:
                code_storage.add_code(f"data = {df_name}.groupby([{group_y_string}{group_x_string}]).size().unstack(fill_value=0)")
            code_storage.add_code(f"color_map = LinearSegmentedColormap.from_list('primary', ['#0000', {with_quote(primary_color)}])")
            color_string = f"cmap=color_map, vmin=0, vmax=1,"
            
        opacity_string = ''
        if fid_opacity:
            opacity_field = pick_first(opacity_channel)
            semanticType = opacity_field.get("semanticType")
            opacity_string = f"alpha=alpha, "
            if semanticType == 'quantitative' or semanticType == 'temporal':
                code_storage.add_code(f"alpha = {df_name}.pivot_table({y_string}{x_string}values={with_quote(fid_opacity)}, fill_value=0)")
                code_storage.add_code(f"alpha = (alpha - {df_name}[{with_quote(fid_opacity)}].min()) / ({df_name}[{with_quote(fid_opacity)}].max() - {df_name}[{with_quote(fid_opacity)}].min()) * 0.7 + 0.3")
                opacity_bar_string = f"{ax_name}.figure.colorbar(ScalarMappable(norm=Normalize(vmin={df_name}[{with_quote(fid_opacity)}].min(), vmax={df_name}[{with_quote(fid_opacity)}].max()), cmap='Greys'), ax={instance_name}, label={with_quote(get_name_with_agg(opacity_field, is_aggergated))})"
            else:
                code_storage.add_code(f"alpha = {df_name}.pivot_table({y_string}{x_string}values={with_quote(fid_opacity)}, aggfunc=lambda x: ','.join(sorted(set(x))))")
                code_storage.add_code("unique_alpha = alpha.unstack().unique()")
                code_storage.add_code(f"alpha_map = dict(itertools.chain(zip(unique_alpha, np.linspace(0.3, 1, len(unique_alpha))), [({numpy_name}.nan, 0)]))")
                code_storage.add_code("alpha = alpha.replace(alpha_map)")
                opacity_bar_string = f"opacity_legend = {ax_name}.legend([mpatches.Patch(color='white', label=label, alpha=alpha) for (label, alpha) in alpha_map.items() if isinstance(label, str)], unique_alpha, loc=4, title={with_quote(get_name_with_agg(opacity_field, is_aggergated))})\n{ax_name}.add_artist(opacity_legend)"
            if imdata == 'imdata':
                opacity_string = ''
                code_storage.add_code(f"imdata = np.dstack((imdata, alpha))")

        code_storage.add_code(f"im = {ax_name}.imshow({imdata}, aspect='equal', {color_string}{opacity_string})")
        if fid_y:
            code_storage.add_code(f"{ax_name}.set_yticks(range(len(data.index)), labels=data.index)")
            code_storage.add_code(f"{ax_name}.set_yticks([x - 0.5 for x in range(len(data.index))], minor=True)")
            code_storage.add_code(f"{ax_name}.set_ylabel({with_quote(get_name_with_agg(y_field, is_aggergated))})")
        if fid_x:
            code_storage.add_code(f"{ax_name}.set_xticks(range(len(data.columns)), labels=data.columns)")
            code_storage.add_code(f"{ax_name}.set_xticks([x - 0.5 for x in range(len(data.columns))], minor=True)")
            code_storage.add_code(f"{ax_name}.set_xlabel({with_quote(get_name_with_agg(x_field, is_aggergated))})")
        code_storage.add_code(f"{ax_name}.grid(which='minor')")
        if opacity_bar_string:
            code_storage.add_code(opacity_bar_string)
        if colorbar_string:
            code_storage.add_code(colorbar_string)
            
    def plot_scatter_single(ax_name, fig_name, df_name, x_field, y_field, marker):
        fid_x = get_fid_with_agg(x_field, is_aggergated)
        fid_y = get_fid_with_agg(y_field, is_aggergated)
        x_string = get_field_string('', df_name, x_field, is_aggergated, f'[0] * len({df_name})')
        y_string = get_field_string('', df_name, y_field, is_aggergated, f'[0] * len({df_name})')
        
        color_string = ''
        
        if fid_shape:
            code_storage.add_code(f"shapes = ['o', 's', 'D', '^', 'v', '<', '>', 'p', 'h', '8', '*', 'H', 'd', 'P', 'X', '1', '2', '3', '4', 'x', '|', '_', 'o', 's', 'D', '^', 'v', '<', '>', 'p', 'h', '8', '*', 'H', 'd', 'P', 'X', '1', '2', '3', '4', 'x', '|', '_']")
            code_storage.add_code(f"shape_map = dict(zip({df_name}[{with_quote(fid_shape)}].unique(), itertools.cycle(shapes)))")
            code_storage.add_code(f"for (shape, marker) in shape_map.items():")
            code_storage.set_indent_level(1)
            code_storage.add_code(f"sub_data = {df_name}[{df_name}[{with_quote(fid_shape)}] == shape]")
            color_string = get_color_string('sub_data')
            size_string = f"s=sub_data[{with_quote(fid_size)}], " if fid_size else ''
            opacity_string, opacity_bar_string, _ = get_opacity_string('sub_data', ax_name)
            code_storage.add_code(f"{ax_name}.scatter(sub_data[{with_quote(fid_x)}], sub_data[{with_quote(fid_y)}], {size_string}marker=marker, {color_string}{opacity_string})")
            code_storage.set_indent_level(0)
            
            code_storage.add_code(f"shape_legend = {ax_name}.legend(handles=[{instance_name}.Line2D([0], [0], marker=marker, label=shape) for shape, marker in shape_map.items()],loc=7, title={with_quote(get_name_with_agg(shape_channel[0], is_aggergated))})")
            code_storage.add_code(f"{ax_name}.add_artist(shape_legend)")
            if opacity_bar_string:
                code_storage.add_code(opacity_bar_string)
                
        else:
            color_string = get_color_string(df_name)
            size_string = f"s={df_name}[{with_quote(fid_size)}], " if fid_size else ''
            opacity_string, opacity_bar_string, _ = get_opacity_string('sub_data', ax_name)
            code_storage.add_code(f"{ax_name}.scatter({x_string}{y_string}{color_string}{opacity_string}{size_string}{marker})")
            if opacity_bar_string:
                code_storage.add_code(opacity_bar_string)
        if colorbar_string:
            code_storage.add_code(colorbar_string)
        if fid_x:
            code_storage.add_code(f"{ax_name}.set_xlabel({with_quote(get_name_with_agg(x_field, is_aggergated))})")
        if fid_y:
            code_storage.add_code(f"{ax_name}.set_ylabel({with_quote(get_name_with_agg(y_field, is_aggergated))})")
        if fid_text:
            code_storage.add_code(f"for i, txt in enumerate(df[{with_quote(fid_text)}]):" + f"\n    {ax_name}.text(df[{with_quote(fid_x)}][i], df[{with_quote(fid_y)}][i], txt)")

    def plot_bar_single(ax_name, fig_name, df_name, x_field, y_field):
        if y_field and y_field.get("analyticType") == 'dimension':
            if x_field and x_field.get("analyticType") == 'dimension':
                return plot_square_single(ax_name, fig_name, df_name, x_field, y_field)
            else:
                direction = 'h'
        else:
            if x_field and x_field.get("analyticType") == 'dimension':
                direction = 'v'
            elif y_field is None:
                direction = 'h'
            else:
                direction = 'v'
        fid_x = get_fid_with_agg(x_field, is_aggergated)
        fid_y = get_fid_with_agg(y_field, is_aggergated)
        x_string = get_field_string('', df_name, x_field, is_aggergated, f'[1] * len({df_name})')
        y_string = get_field_string('', df_name, y_field, is_aggergated, f'[1] * len({df_name})')
        
        # if stacked, we should group by x_field and calculate bottom
        groups = []
        group_keys = []
        if fid_color:
            groups.append(fid_color)
            group_keys.append('color_key')
        if fid_opacity:
            groups.append(fid_opacity)
            group_keys.append('opacity_key')
        
        size_string = f"width={df_name}[{with_quote(fid_size)}], " if fid_size else ''
        if len(groups) > 0:
            opacity_bar_string = ''
            code_storage.add_code(f"groups = {df_name}.groupby({json.dumps(groups)})")
            if fid_opacity:
                _, opacity_bar_string, opacity_type = get_opacity_string(df_name, ax_name)
            if stack == 'stack':
                dimension_key = fid_x if direction == 'v' else fid_y
                measure_key = fid_y if direction == 'v' else fid_x
                if dimension_key:
                    code_storage.add_code(f"stack_map = dict((key, 0) for key in {get_field_string_simple(df_name, dimension_key, '')}.unique())")
                else:
                    code_storage.add_code(f"stack_map = dict([(0,0)])")
            code_storage.add_code(f"for indexes, group in groups:")
            code_storage.set_indent_level(1)
            if len(group_keys) == 1:
                code_storage.add_code(f"({group_keys[0]}) = indexes[0]")
            else:
                code_storage.add_code(f"{','.join(group_keys)} = indexes")
            
            if stack == 'stack':
                bottom_key = 'bottom' if direction == 'v' else 'left'
                if dimension_key:
                    bottom_string = f"{bottom_key}={get_field_string_simple('group', dimension_key, '')}.map(stack_map), "
                else:
                    bottom_string = f"{bottom_key}=stack_map[0], "
            else:
                bottom_string = ''
            
            if fid_color:
                color_string = f"color=color_map[color_key], " if color_type == 'category' else f"color=color_map(color_key), "
            else:
                color_string = ''
                
            if fid_opacity:
                if opacity_type == 'linear':
                    opacity_string = f"alpha=(opacity_key - alpha.min()) / (alpha.max() - alpha.min()) * 0.7 + 0.3, "
                else:
                    opacity_string = f"alpha=alpha_map[opacity_key], "
            else:
                opacity_string = ''
            
            x_string = get_field_string('', 'group', x_field, is_aggergated, f'[1] * len(group)')
            y_string = get_field_string('', 'group', y_field, is_aggergated, f'[1] * len(group)')
            if direction == 'h':
                code_storage.add_code(f"{ax_name}.barh({y_string}{x_string}{bottom_string}{color_string}{opacity_string}{size_string})")
            else:
                code_storage.add_code(f"{ax_name}.bar({x_string}{y_string}{bottom_string}{color_string}{opacity_string}{size_string})")
            if stack == 'stack':
                if dimension_key:
                    code_storage.add_code(f"for dim in {get_field_string_simple('group', dimension_key)}:")
                    code_storage.set_indent_level(2)
                    filtered_data = f"group[{get_field_string_simple('group', dimension_key)} == dim]"
                    value = get_field_string_simple(filtered_data, measure_key, '') + '.values[0]' if measure_key else '1'
                    code_storage.add_code(f"stack_map[dim] += {value}")
                    code_storage.set_indent_level(1)
                else:
                    code_storage.add_code(f"stack_map[0] += 1")
            code_storage.set_indent_level(0)
            if opacity_bar_string:
                code_storage.add_code(opacity_bar_string)
            if colorbar_string:
                code_storage.add_code(colorbar_string)

        else:
            if direction == 'h':
                code_storage.add_code(f"{ax_name}.barh({y_string}{x_string}{size_string}{get_color_string(df_name)})")
            else:
                code_storage.add_code(f"{ax_name}.bar({x_string}{y_string}{size_string}{get_color_string(df_name)})")
        if fid_x:
            code_storage.add_code(f"{ax_name}.set_xlabel({with_quote(get_name_with_agg(x_field, is_aggergated))})")
        if fid_y:
            code_storage.add_code(f"{ax_name}.set_ylabel({with_quote(get_name_with_agg(y_field, is_aggergated))})")
        if fid_text:
            code_storage.add_code(f"for i, txt in enumerate(df[{with_quote(fid_text)}]):" + f"\n    {ax_name}.text(df[{with_quote(fid_x)}][i], df[{with_quote(fid_y)}][i], txt)")
            
    def plot_area_single(ax_name, fig_name, df_name, x_field, y_field):
        fid_x = get_fid_with_agg(x_field, is_aggergated)
        fid_y = get_fid_with_agg(y_field, is_aggergated)
        groups = []
        group_keys = []
        if fid_color:
            groups.append(fid_color)
            group_keys.append('color_key')
        if fid_opacity:
            groups.append(fid_opacity)
            group_keys.append('opacity_key')
            
        if fid_x:
            code_storage.add_code(f"sorted_df = {df_name}.sort_values({with_quote(fid_x)})")
            df_name = f"sorted_df"
            
        if len(groups) > 0:
            if stack == 'stack':
                _, opacity_bar_string, opacity_type = get_opacity_string(df_name, ax_name)
                code_storage.add_code(f"data = {df_name}.pivot_table(index={with_quote(fid_x)}, columns=[{','.join([with_quote(item) for item in groups])}], values={with_quote(fid_y)}, fill_value=0)")
                code_storage.add_code(f"unique_stack_items = data.columns.values")
                code_storage.add_code(f"colors = []")
                code_storage.add_code(f"for indexes in unique_stack_items:")
                code_storage.set_indent_level(1)
                if len(group_keys) == 1:
                    code_storage.add_code(f"({group_keys[0]}) = indexes")
                else:
                    code_storage.add_code(f"{','.join(group_keys)} = indexes")
                if fid_color:
                    code_storage.add_code(f"colors.append({instance_name}.matplotlib.colors.to_rgb(color_map[color_key]))")
                else:
                    code_storage.add_code(f"colors.append({instance_name}.matplotlib.colors.to_rgb({with_quote(primary_color)}))")
                if fid_opacity:
                    if opacity_type == 'linear':
                        code_storage.add_code(f"colors[-1] = colors[-1] + ((opacity_key - alpha.min()) / (alpha.max() - alpha.min()) * 0.7 + 0.3,)")
                    else:
                        code_storage.add_code(f"colors[-1] = colors[-1] + (alpha_map[opacity_key],)")
                    
                        
                code_storage.set_indent_level(0)
                index_data = ".astype('datetime64[s]')" if x_field.get("semanticType") == 'temporal' else ''
                code_storage.add_code(f"{ax_name}.stackplot(data.index{index_data}, data.T, labels=data.columns, colors=colors)")
                if opacity_bar_string:
                    code_storage.add_code(opacity_bar_string)

                pass
            else:
                code_storage.add_code(f"groups = {df_name}.groupby({json.dumps(groups)})")
                _, opacity_bar_string, opacity_type = get_opacity_string(df_name, ax_name)
                code_storage.add_code(f"for indexes, group in groups:")
                code_storage.set_indent_level(1)
                if len(group_keys) == 1:
                    code_storage.add_code(f"({group_keys[0]}) = indexes[0]")
                else:
                    code_storage.add_code(f"{','.join(group_keys)} = indexes")
                
                if fid_color:
                    color_string = f"color=color_map[color_key], " if color_type == 'category' else f"color=color_map(color_key), "
                else:
                    color_string = ''
                    
                if fid_opacity:
                    if opacity_type == 'linear':
                        opacity_string = f"alpha=(opacity_key - alpha.min()) / (alpha.max() - alpha.min()) * 0.7 + 0.3, "
                    else:
                        opacity_string = f"alpha=alpha_map[opacity_key], "
                else:
                    opacity_string = ''
                
                x_string = get_field_string('', 'group', x_field, is_aggergated, f'[0] * len(group)')
                y_string = get_field_string('', 'group', y_field, is_aggergated, f'[1] * len(group)')
                code_storage.add_code(f"{ax_name}.fill_between({x_string}{y_string}{color_string}{opacity_string})")
                code_storage.set_indent_level(0)
                if opacity_bar_string:
                    code_storage.add_code(opacity_bar_string)
        else:
            x_string = get_field_string('', df_name, x_field, is_aggergated, f'[0] * len({df_name})')
            y_string = get_field_string('', df_name, y_field, is_aggergated, f'[1] * len({df_name})')
            code_storage.add_code(f"{ax_name}.fill_between({x_string}{y_string}{get_color_string(df_name)})")
        if colorbar_string:
            code_storage.add_code(colorbar_string)
        if fid_x:
            code_storage.add_code(f"{ax_name}.set_xlabel({with_quote(get_name_with_agg(x_field, is_aggergated))})")
        if fid_y:
            code_storage.add_code(f"{ax_name}.set_ylabel({with_quote(get_name_with_agg(y_field, is_aggergated))})")
        if fid_text:
            code_storage.add_code(f"for i, txt in enumerate(df[{with_quote(fid_text)}]):" + f"\n    {ax_name}.text(df[{with_quote(fid_x)}][i], df[{with_quote(fid_y)}][i], txt)")

    def plot_line_single(ax_name, fig_name, df_name, x_field, y_field):
        fid_x = get_fid_with_agg(x_field, is_aggergated)
        fid_y = get_fid_with_agg(y_field, is_aggergated)
        groups = []
        group_keys = []
        if fid_color:
            groups.append(fid_color)
            group_keys.append('color_key')
        if fid_opacity:
            groups.append(fid_opacity)
            group_keys.append('opacity_key')
            
        if fid_x:
            code_storage.add_code(f"sorted_df = {df_name}.sort_values({with_quote(fid_x)})")
            df_name = f"sorted_df"
            
        if len(groups) > 0:
            code_storage.add_code(f"groups = {df_name}.groupby({json.dumps(groups)})")
            opacity_bar_string = ''
            if fid_opacity:
                _, opacity_bar_string, opacity_type = get_opacity_string(df_name, ax_name)
            code_storage.add_code(f"for indexes, group in groups:")
            code_storage.set_indent_level(1)
            if len(group_keys) == 1:
                code_storage.add_code(f"({group_keys[0]}) = indexes[0]")
            else:
                code_storage.add_code(f"{','.join(group_keys)} = indexes")
            
            if fid_color:
                color_string = f"c=color_map[color_key], " if color_type == 'category' else f"c=color_map(color_key), "
            else:
                color_string = ''
                
            if fid_opacity:
                if opacity_type == 'linear':
                    opacity_string = f"alpha=(opacity_key - alpha.min()) / (alpha.max() - alpha.min()) * 0.7 + 0.3, "
                else:
                    opacity_string = f"alpha=alpha_map[opacity_key], "
            else:
                opacity_string = ''
            
            x_string = get_field_string('', 'group', x_field, is_aggergated, f'[0] * len(group)')
            y_string = get_field_string('', 'group', y_field, is_aggergated, f'[0] * len(group)')
            code_storage.add_code(f"{ax_name}.plot({x_string}{y_string}{color_string}{opacity_string})")
            code_storage.set_indent_level(0)
            if opacity_bar_string:
                code_storage.add_code(opacity_bar_string)
        else:
            x_string = get_field_string('', df_name, x_field, is_aggergated, f'[0] * len({df_name})')
            y_string = get_field_string('', df_name, y_field, is_aggergated, f'[0] * len({df_name})')
            code_storage.add_code(f"{ax_name}.plot({x_string}{y_string})")
        if colorbar_string:
            code_storage.add_code(colorbar_string)
        if fid_x:
            code_storage.add_code(f"{ax_name}.set_xlabel({with_quote(get_name_with_agg(x_field, is_aggergated))})")
        if fid_y:
            code_storage.add_code(f"{ax_name}.set_ylabel({with_quote(get_name_with_agg(y_field, is_aggergated))})")
        if fid_text:
            code_storage.add_code(f"for i, txt in enumerate(df[{with_quote(fid_text)}]):" + f"\n    {ax_name}.text(df[{with_quote(fid_x)}][i], df[{with_quote(fid_y)}][i], txt)")
    
    def plot_box_single(ax_name, fig_name, df_name, x_field, y_field):
        fid_x = get_fid_with_agg(x_field, is_aggergated)
        fid_y = get_fid_with_agg(y_field, is_aggergated)
        name_x = get_name_with_agg(x_field, is_aggergated)
        name_y = get_name_with_agg(y_field, is_aggergated)
        if fid_y is None and fid_x is not None:
            code_storage.add_code(f"{ax_name}.boxplot({df_name}[{with_quote(fid_x)}], patch_artist=True, vert=False, labels=[{with_quote(name_x)}])")
            
        elif fid_x is None and fid_y is not None:
            code_storage.add_code(f"{ax_name}.boxplot({df_name}[{with_quote(fid_y)}], patch_artist=True, labels=[{with_quote(name_y)}])")
        else:
            code_storage.add_code(f"values = {df_name}[{with_quote(fid_y)}].groupby({df_name}[{with_quote(fid_x)}])")
            code_storage.add_code(f"{ax_name}.boxplot([group[1] for group in values], patch_artist=True, labels=[group[0] for group in values])")
            
    def plot_arc_single_only(instance_name, colorbar_string):
        theta_channel = encodings.get("theta")
        fid_theta = get_fid_with_agg(pick_first(theta_channel), is_aggergated)
        if color_type == 'category':
            color_string = f"colors=cp, " if fid_color else f'colors=["{primary_color}"]'
        elif fid_color:
            code_storage.add_code(f"norm = Normalize(vmin=df[{with_quote(fid_color)}].min(), vmax=df[{with_quote(fid_color)}].max())")
            code_storage.add_code(f"colors = color_map(norm(df[{with_quote(fid_color)}]))")
            color_string = 'colors=colors, '
            code_storage.add_code(f"ax = {instance_name}.subplot()")
            colorbar_string = f'{instance_name}.figure.colorbar(ScalarMappable(norm=norm, cmap=color_map), ax=ax)'
        else:
            color_string = f"colors=[{with_quote(primary_color)}], "


        label_string = f"labels={df_name}[{with_quote(fid_text)}], " if fid_text else ''
        code_storage.add_code(f"{instance_name}.pie({df_name}[{with_quote(fid_theta)}], autopct='%1.1f%%', {label_string}{color_string})")
        if colorbar_string:
            code_storage.add_code(colorbar_string)
    
    scatter_options = {
        'point': 'marker="x"',
        'tick': 'marker=0',
        'circle': 'marker="o"',
        'text': 'marker="none"'
    }
    
    def plot(ax_name, fig_name, df_name, x_field, y_field):
        if mark == 'bar':
            plot_bar_single(ax_name, fig_name, df_name, x_field, y_field)
        elif mark == 'line' or mark == 'trail':
            plot_line_single(ax_name, fig_name, df_name, x_field, y_field)
        elif mark == 'area':
            plot_area_single(ax_name, fig_name, df_name, x_field, y_field)
        elif mark in scatter_options:
            plot_scatter_single(ax_name, fig_name, df_name, x_field, y_field, scatter_options[mark])
        elif mark == 'boxplot':
            plot_box_single(ax_name, fig_name, df_name, x_field, y_field)
        elif mark =='rect':
            plot_square_single(ax_name, fig_name, df_name, x_field, y_field)
        else:
            return False
        if zero_scale:
            if x_field and x_field.get("analyticType") == 'measure':
                code_storage.add_code(f"left, right = {ax_name}.get_xlim()")
                code_storage.add_code(f"if left > 0:")
                code_storage.increase_indent_level()
                code_storage.add_code(f"{ax_name}.set_xlim(left=0)")
                code_storage.decrease_indent_level()
                code_storage.add_code(f"elif right < 0:")
                code_storage.increase_indent_level()
                code_storage.add_code(f"{ax_name}.set_xlim(right=0)")
                code_storage.decrease_indent_level()
            if y_field and y_field.get("analyticType") == 'measure':
                code_storage.add_code(f"bottom, top = {ax_name}.get_ylim()")
                code_storage.add_code(f"if bottom > 0:")
                code_storage.increase_indent_level()
                code_storage.add_code(f"{ax_name}.set_ylim(bottom=0)")
                code_storage.decrease_indent_level()
                code_storage.add_code(f"elif top < 0:")
                code_storage.increase_indent_level()
                code_storage.add_code(f"{ax_name}.set_ylim(top=0)")
                code_storage.decrease_indent_level()
        return True

    if mark == 'arc':
        if len(encodings.get("theta")) > 0:
            plot_arc_single_only(instance_name, colorbar_string)
        else:
            return ''
    elif len(x_channels) <= 1 and len(y_channels) <= 1:
        if len(x_channels) == 0 and len(y_channels) == 0:
            return ''
        code_storage.add_code(f"ax = {instance_name}.subplot()")
        if plot("ax", "ax", df_name, pick_first(x_channels), pick_first(y_channels)):
            pass
        else:
            return ''
    else:
        col_code, col_dims, col_fields = get_dimension_count_string(df_name, 'col', x_channels, is_aggergated)
        code_storage.add_code(col_code)
        row_code, row_dims, row_fields = get_dimension_count_string(df_name, 'row', y_channels, is_aggergated)
        code_storage.add_code(row_code)
        code_storage.add_code(f"fig, axs = {instance_name}.subplots(row_nums * {len(row_fields)}, col_nums * {len(col_fields)})")
        code_storage.add_code(f"axs = axs.flatten()")
        if len(row_dims) + len(col_dims) == 0:
            for (i, row_field) in enumerate(row_fields):
                for (j, col_field) in enumerate(col_fields):
                    code_storage.add_code(f"ax = axs[{i * len(col_fields) + j}]")
                    plot("ax", "fig", df_name, col_field, row_field)
        else:
            code_storage.add_code(f"groups = {df_name}.groupby([{','.join([with_quote(get_fid_with_agg(field, is_aggergated)) for field in row_dims + col_dims])}])")
            code_storage.add_code(f"for indexes, group in groups:")
            code_storage.set_indent_level(1)
            code_storage.add_code(f"row_index = row.index(indexes[:row_dims]) if row_dims > 0 else 0")
            code_storage.add_code(f"col_index = col.index(indexes[row_dims:]) if col_dims > 0 else 0")
            for (i, row_field) in enumerate(row_fields):
                for (j, col_field) in enumerate(col_fields):
                    code_storage.add_code(f"ax = axs[((row_index * {len(row_fields)} + {i}) * col_nums * {len(col_fields)} + (col_index * {len(col_fields)} + {j})) ]")
                    code_storage.add_code(f"ax.set_title(indexes)")
                    plot("ax", "fig", df_name, col_field, row_field)
        code_storage.set_indent_level(0)

    return code_storage.output_all()


def render_image(df: DataFrame, payload: Dict[str, any], size: Dict[str, int]):
    code = build_code(payload, size)
    with plt.ioff():
        exec(code)
        my_stringIObytes = io.BytesIO()
        plt.tight_layout()
        plt.savefig(my_stringIObytes, format='png')
        plt.clf()
        plt.cla()
        plt.close()
        my_stringIObytes.seek(0)
        my_base64_pngData = base64.b64encode(my_stringIObytes.read()).decode()

    return json.dumps({"image":  "data:image/png;base64," + my_base64_pngData, "size": size})


