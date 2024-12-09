import io
from pygwalker.renderers.base import CodeStorage, auto_mark


def render_image(df, payload, size):
    code_storage = CodeStorage()
    code_storage.add_code("import matplotlib.pyplot as plt")
    config = payload.get("config")
    mark = config.get("geoms")[0]
    encodings = payload.get("encodings")
    if mark == "auto":
        mark = auto_mark([field.get("semanticType") for field in encodings.get("rows") + encodings.get("columns")])
    
    if size:
        code_storage.add_code(f"plt.figure(dpi=100, figsize=({size[0]/ 100}, {size[1] / 100}))")
        
    x_channels = encodings.get("columns")
    y_channels = encodings.get("rows")
    color_channel = encodings.get("color")
    opacity_channel = encodings.get("opacity")
    size_channel = encodings.get("size")
    shape_channel = encodings.get("shape")
    theta_channel = encodings.get("theta")
    radius_channel = encodings.get("radius")

    # 'bar', 'line', 'area', 'trail', 'point', 'circle', 'tick', 'rect', 'arc', 'text', 'boxplot'
    if mark == 'bar':
        fid_color = color_channel[0].get("fid") if color_channel else None
        fid_opacity = opacity_channel[0].get("fid") if opacity_channel else None
        fid_size = size_channel[0].get("fid") if size_channel else None
        if len(x_channels) == 1 and len(y_channels) == 1:
            fid_x = x_channels[0].get("fid")
            name_x = x_channels[0].get("name")
            fid_y = y_channels[0].get("fid")
            name_y = y_channels[0].get("name")
            color_string = f"color=df['{fid_color}'], " if fid_color else ''
            opacity_string = f"alpha=df['{fid_opacity}'], " if fid_opacity else ''
            size_string = f"width=df['{fid_size}'], " if fid_size else ''
            code_storage.add_code(f"plt.bar(df['{fid_x}'], df['{fid_y}'], {color_string}{opacity_string}{size_string})")
            code_storage.add_code(f"plt.xlabel('{name_x}')")
            code_storage.add_code(f"plt.ylabel('{name_y}')")
        else:
            # For multiple x/y channels, create faceted subplots
            code_storage.add_code(f"fig, axes = plt.subplots({len(y_channels)}, {len(x_channels)}, squeeze=False)")
            for i, y in enumerate(y_channels):
                for j, x in enumerate(x_channels):
                    fid_x = x.get("fid")
                    name_x = x.get("name")
                    fid_y = y.get("fid")
                    name_y = y.get("name")
                    color_string = f"color=df['{fid_color}'], " if fid_color else ''
                    opacity_string = f"alpha=df['{fid_opacity}'], " if fid_opacity else ''
                    size_string = f"width=df['{fid_size}'], " if fid_size else ''
                    code_storage.add_code(f"axes[{i},{j}].bar(df['{fid_x}'], df['{fid_y}'], {color_string}{opacity_string}{size_string})")
                    code_storage.add_code(f"axes[{i},{j}].set_xlabel('{name_x}')")
                    code_storage.add_code(f"axes[{i},{j}].set_ylabel('{name_y}')")
            code_storage.add_code("plt.tight_layout()")
            
    code_storage.execute_all()
    code_storage.add_code("plt.show()")
    print(code_storage.output_all())
    my_stringIObytes = io.BytesIO()
    plt.savefig(my_stringIObytes, format='png')
    plt.clf()
    plt.cla()
    my_stringIObytes.seek(0)
    my_base64_pngData = base64.b64encode(my_stringIObytes.read()).decode()
    return "data:image/png;base64," + my_base64_pngData
