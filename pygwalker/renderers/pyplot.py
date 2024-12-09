import base64
import io
import json
from typing import List
from pygwalker.renderers.base import CodeStorage, auto_mark, get_color_palette, get_fid_with_agg, get_name_with_agg, get_primary_color, get_spec_color_palette, pick_first
import matplotlib
from matplotlib.colors import LinearSegmentedColormap
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import itertools
import matplotlib.patches as mpatches

def render_image(df, payload, size):
    code_storage = CodeStorage()
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
    if fid_color is None:
        primary_color = get_primary_color(payload)
        if primary_color:
            # extract rgba from primary_color string 'rgba(r,g,b,a)' like rgba(112, 0, 255, 1), transform into hex
            rgb_values = primary_color[5:-1].split(',')[:3]  # Take only RGB values
            color_hex = '#%02x%02x%02x' % tuple(map(int, rgb_values))
            color_string = f"color='{color_hex}', "
    else:
        color_field = pick_first(color_channel)
        color_palette = get_spec_color_palette(payload)
        if color_field.get("semanticType") == "quantitative" or color_field.get("semanticType") == "temporal":
            if color_palette is None:
                color_palette = get_color_palette('blues')
            code_storage.add_code(f"color_map = LinearSegmentedColormap.from_list('palette',{json.dumps(color_palette)})")
            color_string = f"c=df['{fid_color}'],cmap=color_map, "
            colorbar_string = 'plt.colorbar()'
        else:
            if color_palette is None:
                color_palette = get_color_palette('category10')
            code_storage.add_code(f"cp = {json.dumps(color_palette)}")
            code_storage.add_code(f"colors = df['{fid_color}']")
            code_storage.add_code("unique_color = colors.unique()")
            code_storage.add_code("color_map = dict(zip(unique_color, itertools.cycle(cp)))")
            code_storage.add_code("c = colors.map(color_map)")
            color_string = f"c=c,"
            colorbar_string = 'plt.legend([mpatches.Patch(color=color, label=label) for (label, color) in color_map.items()], unique_color)'


    opacity_string = f"alpha='{fid_opacity}', " if fid_opacity else ''

    def plot_single(plot_func, plot_options = ''):
        fid_x = get_fid_with_agg(x_channels[0], is_aggergated)
        fid_y = get_fid_with_agg(y_channels[0], is_aggergated)
        
        x_string = f"df['{fid_x}'], " if fid_x else ''
        y_string = f"df['{fid_y}'], " if fid_y else ''
        
        size_string = f"{'width' if mark == 'bar' else 's'}=df['{fid_size}'], " if fid_size else ''

        # code_storage.add_code(f"df.plot({x_string}{y_string}{color_string}{opacity_string}{size_string}{plot_func})")
        code_storage.add_code(f"plt.{plot_func}({x_string}{y_string}{color_string}{opacity_string}{size_string}{plot_options})")
        if colorbar_string:
            code_storage.add_code(colorbar_string)
        code_storage.add_code(f"plt.xlabel('{get_name_with_agg(x_channels[0], is_aggergated)}')")
        code_storage.add_code(f"plt.ylabel('{get_name_with_agg(y_channels[0], is_aggergated)}')")
        if fid_text:
            code_storage.add_code(f"for i, txt in enumerate(df['{fid_text}']):" + f"\n    plt.text(df['{fid_x}'][i], df['{fid_y}'][i], txt)")
    
    def plot_box_single():
        fid_y = get_fid_with_agg(pick_first(y_channels), is_aggergated)
        fid_x = get_fid_with_agg(pick_first(x_channels), is_aggergated)
        name_x = get_name_with_agg(pick_first(x_channels), is_aggergated)
        name_y = get_name_with_agg(pick_first(y_channels), is_aggergated)
        if fid_y is None and fid_x is not None:
            code_storage.add_code(f"plt.boxplot(df['{fid_x}'], patch_artist=True, vert=False, labels=['{name_x}'])")
            
        elif fid_x is None and fid_y is not None:
            code_storage.add_code(f"plt.boxplot(df['{fid_y}'], patch_artist=True, labels=['{name_y}'])")
        else:
            code_storage.add_code(f"values = df['{fid_y}'].groupby(df['{fid_x}'])")
            code_storage.add_code(f"plt.boxplot([group[1] for group in values], patch_artist=True, labels=[group[0] for group in values])")
            
    def plot_arc_single_only():
        theta_channel = encodings.get("theta")
        radius_channel = encodings.get("radius")
        fid_theta = get_fid_with_agg(pick_first(theta_channel), is_aggergated)
        fid_radius = get_fid_with_agg(pick_first(radius_channel), is_aggergated)
        
        if fid_radius is None:
            label_string = f"labels=df['{fid_color}'], " if fid_color else ''
            code_storage.add_code(f"plt.pie(df['{fid_theta}'], autopct='%1.1f%%', {label_string})")
        else:
            # df['fid_theta'] is [1,1,1]
            code_storage.add_code(f"ax = plt.subplot(projection='polar')")
            code_storage.add_code(f"ax.bar(df['{fid_theta}'], df['{fid_radius}'])")


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
            # plot_multiple(plot_types[mark])
            return ''
            pass
    else:
        if mark == 'boxplot':
            plot_box_single()
        elif mark == 'arc':
            plot_arc_single_only()
        else:
            return ''
        pass
    with plt.ioff():
        code = code_storage.output_all()
        print(code)
        exec(code)
        code_storage.add_code("plt.show()")
        my_stringIObytes = io.BytesIO()
        plt.savefig(my_stringIObytes, format='png')
        plt.clf()
        plt.cla()
        plt.close()
        my_stringIObytes.seek(0)
        my_base64_pngData = base64.b64encode(my_stringIObytes.read()).decode()

    
    return json.dumps({"image":  "data:image/png;base64," + my_base64_pngData, "size": size})


def linearmap_color(colorlist: List[str]):
    return LinearSegmentedColormap.from_list('custom', colorlist)