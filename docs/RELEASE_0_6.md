# PyGWalker 0.6 Release Notes

PyGWalker 0.6 introduces the new public computation model and the reusable `Walker` API while keeping the 0.5 user-facing computation flags available for compatibility.

## API Direction

Use `computation` to choose where queries run:

```python
pyg.walk(df, computation="auto")
pyg.walk(df, computation="browser")
pyg.walk(df, computation="kernel")
pyg.walk(df, computation="cloud")
```

For code that renders the same data in more than one environment, prefer a reusable `Walker`:

```python
w = pyg.Walker(df, computation="kernel")
w.show()
w.to_html()
w.to_streamlit()
```

`kernel_computation`, `cloud_computation`, and `use_kernel_calc` are deprecated in 0.6 but remain supported. They emit `DeprecationWarning` and are scheduled for removal in PyGWalker 0.7.0. Do not mix an explicit non-auto `computation` value with enabled legacy computation flags.

## Jupyter Rendering

The anywidget path is the preferred and default Jupyter rendering path. `Jupyter` and `JupyterWidget` remain accepted as legacy aliases in 0.6, but they warn and resolve to the anywidget transport. These aliases are scheduled for removal in PyGWalker 0.7.0.

## Static HTML

Static HTML export is browser-only. Exporting static HTML from `computation="kernel"` or `computation="cloud"` raises an error instead of producing output that cannot execute live kernel or cloud computation.

## Privacy

The default privacy mode is `update-only`. Event telemetry is sent only when privacy is set to `events`, and the frontend Segment tracker opens only for that `events` setting.

## Tested Support

The 0.6 release line is validated against Python 3.10, 3.11, 3.12, and 3.13. The frontend and publish workflows build with Node.js 22.x, and CI runs the frontend build plus Playwright smoke tests before packaging.
