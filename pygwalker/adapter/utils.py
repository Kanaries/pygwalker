def is_notebook() -> bool:
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False      # Probably standard Python interpreter

def can_open_window() -> bool:
    import os
    import platform

    # Check if running in SSH session
    if 'SSH_CONNECTION' in os.environ:
        return False

    system = platform.system()
    
    if system == 'Darwin':  # macOS
        # macOS can typically always open windows unless in remote session
        return True
    elif system == 'Linux':
        # Check for X11 or Wayland display
        return bool(os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'))
    elif system == 'Windows':
        # Windows can typically always open windows unless in remote session
        return True
    else:
        return False  # Unknown OS, assume no GUI capability
