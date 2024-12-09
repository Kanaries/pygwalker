import base64
import io
import json
from pygwalker.renderers.base import CodeStorage, auto_mark, get_fid_with_agg, get_name_with_agg
import matplotlib.pyplot as plt

def render_image(df, payload, size):
    code_storage = CodeStorage()
    config = payload.get("config")
    mark = config.get("geoms")[0]
    is_aggergated = config.get("defaultAggregated")
    encodings = payload.get("encodings")
    if mark == "auto":
        mark = auto_mark([field.get("semanticType") for field in encodings.get("rows") + encodings.get("columns")])
        
    # if size:
        # width = size.get("width")
        # height = size.get("height")
        # plt.figure(dpi=100, figsize=(width / 100, height / 100))

    x_channels = encodings.get("columns")
    y_channels = encodings.get("rows")
    color_channel = encodings.get("color")
    opacity_channel = encodings.get("opacity")
    size_channel = encodings.get("size")
    
    fid_color = get_fid_with_agg(color_channel[0], is_aggergated) if color_channel and len(color_channel) > 0 else None
    fid_opacity = get_fid_with_agg(opacity_channel[0], is_aggergated)if opacity_channel and len(opacity_channel) > 0 else None
    fid_size = get_fid_with_agg(size_channel[0], is_aggergated) if size_channel and len(size_channel) > 0 else None
    # shape_channel = encodings.get("shape")
    # theta_channel = encodings.get("theta")
    # radius_channel = encodings.get("radius")
    # fid_shape = shape_channel[0].get("fid") if shape_channel and len(shape_channel) > 0 else None
    # fid_theta = theta_channel[0].get("fid") if theta_channel and len(theta_channel) > 0 else None
    # fid_radius = radius_channel[0].get("fid") if radius_channel and len(radius_channel) > 0 else None

    color_string = f"color='{fid_color}', " if fid_color else ''
    opacity_string = f"alpha='{fid_opacity}', " if fid_opacity else ''
    size_string = f"{'width' if mark == 'bar' else 'linewidth'}='{fid_size}', " if fid_size else ''

    def plot_single(plot_func):
        fid_x = get_fid_with_agg(x_channels[0], is_aggergated)
        fid_y = get_fid_with_agg(y_channels[0], is_aggergated)
        
        x_string = f"df['{fid_x}'], " if fid_x else ''
        y_string = f"df['{fid_y}'], " if fid_y else ''

        # code_storage.add_code(f"df.plot({x_string}{y_string}{color_string}{opacity_string}{size_string}{plot_func})")
        code_storage.add_code(f"plt.{plot_func}({x_string}{y_string}{color_string}{opacity_string}{size_string})")
        code_storage.add_code(f"plt.xlabel('{get_name_with_agg(x_channels[0], is_aggergated)}')")
        code_storage.add_code(f"plt.ylabel('{get_name_with_agg(y_channels[0], is_aggergated)}')")


    # plot_types = {
    #     'bar': 'kind="bar"',
    #     'line': '',
    #     'area': 'kind="area"',
    #     'trail': 'kind="scatter"',
    #     'point': 'kind="scatter", marker="."',
    #     'circle': 'kind="scatter", marker="o"',
    #     'tick': 'kind="scatter", marker="|"',
    # }
    plot_types = {
        'bar': 'bar',
        'line': 'plot'
    }

    if mark in plot_types:
        if len(x_channels) == 1 and len(y_channels) == 1:
            plot_single(plot_types[mark])
        else:
            # plot_multiple(plot_types[mark])
            return ''
            pass
    for code in code_storage.code_snippets:
        exec(code)
    code_storage.add_code("plt.show()")
    my_stringIObytes = io.BytesIO()
    plt.savefig(my_stringIObytes, format='png')
    plt.clf()
    plt.cla()
    my_stringIObytes.seek(0)
    my_base64_pngData = base64.b64encode(my_stringIObytes.read()).decode()
    print(my_base64_pngData)
    
    return json.dumps({"image":  "data:image/png;base64," + my_base64_pngData, "size": size})
