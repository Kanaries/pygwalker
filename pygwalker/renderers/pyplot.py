import base64
import io
import json
from typing import Dict

from pygwalker._typing import DataFrame
from pygwalker.renderers.base import CodeStorage, auto_mark, get_color_palette, get_fid_with_agg, get_name_with_agg, get_primary_color, get_spec_color_palette, pick_first
import matplotlib
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import itertools
import matplotlib.patches as mpatches

def change_color_string_key(color_string: str | None, new_key: str):
    if color_string:
        color_string = color_string.replace('c=', f'{new_key}=')
    return color_string

def build_code(payload: Dict[str, any], size: Dict[str, int], df_name = 'df'):
    code_storage = CodeStorage()
    instance_name = "plt"
    # code_storage.add_code(f"import matplotlib.pyplot as plt")
    config = payload.get("config")
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

    fid_color = get_fid_with_agg(pick_first(color_channel), is_aggergated)
    fid_opacity = get_fid_with_agg(pick_first(opacity_channel), is_aggergated)
    fid_size = get_fid_with_agg(pick_first(size_channel), is_aggergated)
    fid_text = get_fid_with_agg(pick_first(text_channel), is_aggergated)
    fid_shape = get_fid_with_agg(pick_first(shape_channel), is_aggergated)
    color_palette = None
    color_string = ''
    colorbar_string = ''
    primary_color = None
    color_type = 'category'
    if fid_color is None:
        primary_color = get_primary_color(payload)
        if primary_color:
            # extract rgba from primary_color string 'rgba(r,g,b,a)' like rgba(112, 0, 255, 1), transform into hex
            rgb_values = primary_color[5:-1].split(',')[:3]  # Take only RGB values
            primary_color = '#%02x%02x%02x' % tuple(map(int, rgb_values))
            color_string = f"color='{primary_color}', "
        else:
            primary_color = '#5b8ff9'
    else:
        color_field = pick_first(color_channel)
        color_palette = get_spec_color_palette(payload)
        if color_field.get("semanticType") == "quantitative" or color_field.get("semanticType") == "temporal":
            if color_palette is None:
                color_palette = get_color_palette('blues')
            code_storage.add_code(f"color_map = LinearSegmentedColormap.from_list('palette',{json.dumps(color_palette)})")
            color_string = f"c={df_name}['{fid_color}'],cmap=color_map, "
            colorbar_string = f'{instance_name}.colorbar()'
            color_type = 'linear'
        else:
            if color_palette is None:
                color_palette = get_color_palette('category10')
            code_storage.add_code(f"cp = {json.dumps(color_palette)}")
            code_storage.add_code(f"colors = {df_name}['{fid_color}']")
            code_storage.add_code("unique_color = colors.unique()")
            code_storage.add_code("color_map = dict(zip(unique_color, itertools.cycle(cp)))")
            code_storage.add_code("c = colors.map(color_map)")
            color_string = f"c=c,"
            colorbar_string = f'{instance_name}.legend([mpatches.Patch(color=color, label=label) for (label, color) in color_map.items()], unique_color)'
            color_type = 'category'


    opacity_string = f"alpha='{fid_opacity}', " if fid_opacity else ''

    def plot_single(plot_func, plot_options = ''):
        fid_x = get_fid_with_agg(x_channels[0], is_aggergated)
        fid_y = get_fid_with_agg(y_channels[0], is_aggergated)
        
        x_string = f"{df_name}['{fid_x}'], " if fid_x else ''
        y_string = f"{df_name}['{fid_y}'], " if fid_y else ''
        
        size_string = f"{'width' if mark == 'bar' else 's'}={df_name}['{fid_size}'], " if fid_size else ''

        code_storage.add_code(f"{instance_name}.{plot_func}({x_string}{y_string}{color_string}{opacity_string}{size_string}{plot_options})")
        if colorbar_string:
            code_storage.add_code(colorbar_string)
        code_storage.add_code(f"{instance_name}.xlabel('{get_name_with_agg(x_channels[0], is_aggergated)}')")
        code_storage.add_code(f"{instance_name}.ylabel('{get_name_with_agg(y_channels[0], is_aggergated)}')")
        if fid_text:
            code_storage.add_code(f"{instance_name}.text({df_name}['{fid_x}'], {df_name}['{fid_y}'], {df_name}['{fid_text}'])")
    
    def plot_box_single():
        fid_y = get_fid_with_agg(pick_first(y_channels), is_aggergated)
        fid_x = get_fid_with_agg(pick_first(x_channels), is_aggergated)
        name_x = get_name_with_agg(pick_first(x_channels), is_aggergated)
        name_y = get_name_with_agg(pick_first(y_channels), is_aggergated)
        if fid_y is None and fid_x is not None:
            code_storage.add_code(f"{instance_name}.boxplot({df_name}['{fid_x}'], patch_artist=True, vert=False, labels=['{name_x}'])")
            
        elif fid_x is None and fid_y is not None:
            code_storage.add_code(f"{instance_name}.boxplot({df_name}['{fid_y}'], patch_artist=True, labels=['{name_y}'])")
        else:
            code_storage.add_code(f"values = {df_name}['{fid_y}'].groupby({df_name}['{fid_x}'])")
            code_storage.add_code(f"{instance_name}.boxplot([group[1] for group in values], patch_artist=True, labels=[group[0] for group in values])")
            
    def plot_arc_single_only(instance_name, colorbar_string):
        theta_channel = encodings.get("theta")
        fid_theta = get_fid_with_agg(pick_first(theta_channel), is_aggergated)
        if color_type == 'category':
            color_string = f"colors=cp, " if fid_color else f'colors=["{primary_color}"]'
        elif fid_color:
            code_storage.add_code(f"norm = Normalize(vmin=df['{fid_color}'].min(), vmax=df['{fid_color}'].max())")
            code_storage.add_code(f"colors = color_map(norm(df['{fid_color}']))")
            color_string = 'colors=colors, '
            code_storage.add_code(f"ax = {instance_name}.subplot()")
            colorbar_string = f'{instance_name}.colorbar(ScalarMappable(norm=norm, cmap=color_map), ax=ax)'
            instance_name = "ax"
        else:
            color_string = f"colors=['{primary_color}'], "


        label_string = f"labels={df_name}['{fid_text}'], " if fid_text else ''
        code_storage.add_code(f"{instance_name}.pie({df_name}['{fid_theta}'], autopct='%1.1f%%', {label_string}{color_string})")
        if colorbar_string:
            code_storage.add_code(colorbar_string)


    plot_types = {
        'bar': 'bar',
        'line': 'plot',
        'area': 'fill_between',
        'point': 'scatter',
        'tick': 'scatter',
        'circle': 'scatter',
        'trail': 'plot',
        'text': 'scatter'
    }
    
    plot_options = {
        'point': 'marker="x"',
        'tick': 'marker=0',
        'circle': 'marker="o"',
        'text': 'marker="none"'
    }

    if mark in plot_types:
        if len(x_channels) == 1 and len(y_channels) == 1:
            plot_single(plot_types[mark], plot_options.get(mark, ''))
        else:
            # TODO: plot_box_multiple()
            # plot_multiple(plot_types[mark])
            return ''
            pass
    else:
        if mark == 'boxplot':
            if len(x_channels) == 1 and len(y_channels) == 1:
                plot_box_single()
            else:
                # TODO: plot_box_multiple()
                pass
        elif mark == 'arc':
            plot_arc_single_only(instance_name, colorbar_string)
        else:
            return ''
    return code_storage.output_all()


def render_image(df: DataFrame, payload: Dict[str, any], size: Dict[str, int]):
    code = build_code(payload, size)
    with plt.ioff():
        print(code)
        exec(code)
        my_stringIObytes = io.BytesIO()
        plt.savefig(my_stringIObytes, format='png')
        plt.clf()
        plt.cla()
        plt.close()
        my_stringIObytes.seek(0)
        my_base64_pngData = base64.b64encode(my_stringIObytes.read()).decode()

    return json.dumps({"image":  "data:image/png;base64," + my_base64_pngData, "size": size})


