from typing import Any, List, Optional, Union

from typing_extensions import Literal

from .pygwalker import PygWalker
from pygwalker.api import webserver
from pygwalker.data_parsers.base import FieldSpec
from pygwalker.data_parsers.database_parser import Connector
from pygwalker._typing import DataFrame, IAppearance, IComputation, ISpecIOMode, IThemeKey
from pygwalker.utils.check_walker_params import check_expired_params
from pygwalker.utils.computation import resolve_computation_mode
from pygwalker.utils.runtime_env import get_current_env
from pygwalker.utils.spec import resolve_spec_input


IWalkerShowEnv = Literal[
    "auto",
    "jupyter",
    "jupyter-widget",
    "jupyter-inline",
    "jupyter-convert",
    "jupyter-preview",
    "webserver",
    "Jupyter",
    "JupyterWidget",
    "JupyterConvert",
    "JupyterPreview",
]


class Walker:
    """Core PyGWalker object shared by framework adapters."""

    def __init__(
        self,
        dataset: Union[DataFrame, Connector, str],
        gid: Optional[Union[int, str]] = None,
        *,
        field_specs: Optional[List[FieldSpec]] = None,
        theme_key: IThemeKey = "g2",
        appearance: IAppearance = "media",
        spec: str = "",
        spec_path: Optional[str] = None,
        spec_io_mode: ISpecIOMode = "rw",
        computation: Optional[IComputation] = None,
        use_kernel_calc: Optional[bool] = None,
        kernel_computation: Optional[bool] = None,
        cloud_computation: bool = False,
        show_cloud_tool: bool = True,
        kanaries_api_key: str = "",
        default_tab: Literal["data", "vis"] = "vis",
        **kwargs: Any,
    ):
        check_expired_params(kwargs)

        if field_specs is None:
            field_specs = []

        resolved_spec = resolve_spec_input(spec, spec_path)
        resolved_kernel_computation, resolved_cloud_computation = resolve_computation_mode(
            dataset,
            computation=computation,
            kernel_computation=kernel_computation,
            cloud_computation=cloud_computation,
            use_kernel_calc=use_kernel_calc,
        )

        self._dataset = dataset
        self._field_specs = field_specs
        self._theme_key = theme_key
        self._appearance = appearance
        self._spec = spec
        self._spec_path = spec_path
        self._spec_io_mode = spec_io_mode
        self._computation = computation
        self._use_kernel_calc = use_kernel_calc
        self._kernel_computation = kernel_computation
        self._cloud_computation = cloud_computation
        self._show_cloud_tool = show_cloud_tool
        self._kanaries_api_key = kanaries_api_key
        self._default_tab = default_tab
        self._kwargs = kwargs

        self._walker = PygWalker(
            gid=gid,
            dataset=dataset,
            field_specs=field_specs,
            spec=resolved_spec,
            source_invoke_code="",
            theme_key=theme_key,
            appearance=appearance,
            show_cloud_tool=show_cloud_tool,
            use_preview=True,
            kernel_computation=resolved_kernel_computation,
            use_save_tool="w" in spec_io_mode,
            gw_mode="explore",
            is_export_dataframe=True,
            kanaries_api_key=kanaries_api_key,
            default_tab=default_tab,
            cloud_computation=resolved_cloud_computation,
            **kwargs,
        )

    @property
    def core(self) -> PygWalker:
        """Return the underlying compatibility object used by existing APIs."""
        return self._walker

    def __getattr__(self, name: str) -> Any:
        return getattr(self._walker, name)

    def show(
        self,
        env: IWalkerShowEnv = "auto",
        *,
        iframe_width: Optional[str] = None,
        iframe_height: Optional[str] = None,
        port: Optional[int] = None,
        auto_open: bool = True,
        auto_shutdown: bool = True,
    ) -> "Walker":
        """Display this walker in the current environment."""
        env_aliases = {
            "Jupyter": "jupyter-inline",
            "JupyterWidget": "jupyter-widget",
            "JupyterConvert": "jupyter-convert",
            "JupyterPreview": "jupyter-preview",
        }
        resolved_env = get_current_env() if env == "auto" else env_aliases.get(env, env)
        if resolved_env == "jupyter":
            resolved_env = "jupyter-widget"
        elif resolved_env not in (
            "jupyter-widget",
            "jupyter-inline",
            "jupyter-convert",
            "jupyter-preview",
            "webserver",
        ):
            resolved_env = "webserver"

        if resolved_env == "jupyter-widget":
            self._walker.display_on_jupyter_use_widgets(iframe_width, iframe_height)
        elif resolved_env == "jupyter-inline":
            self._walker.display_on_jupyter()
        elif resolved_env == "jupyter-convert":
            self._raise_if_live_computation("JupyterConvert/static HTML output")
            self._walker.display_on_convert_html()
        elif resolved_env == "jupyter-preview":
            self._walker.display_preview_on_jupyter()
        else:
            webserver._start_server(
                self._walker,
                port,
                auto_open=auto_open,
                auto_shutdown=auto_shutdown,
            )
        return self

    def to_html(self, iframe_width: Optional[str] = None, iframe_height: Optional[str] = None) -> str:
        """Export a static HTML iframe."""
        self._raise_if_live_computation("Static HTML export")
        return self._walker.to_html(iframe_width, iframe_height)

    def to_html_without_iframe(self) -> str:
        """Export static HTML without an iframe wrapper."""
        self._raise_if_live_computation("Static HTML export")
        return self._walker.to_html_without_iframe()

    def to_streamlit(self, **kwargs: Any):
        """Create a Streamlit renderer from this walker's constructor options."""
        from pygwalker.api.streamlit import StreamlitRenderer

        computation = self._computation
        kernel_computation = self._kernel_computation
        use_kernel_calc = self._use_kernel_calc
        if computation is None and self._cloud_computation:
            computation = "cloud"
            kernel_computation = None
            use_kernel_calc = None

        options = {
            "field_specs": self._field_specs,
            "theme_key": self._theme_key,
            "appearance": self._appearance,
            "spec": self._spec,
            "spec_path": self._spec_path,
            "spec_io_mode": self._spec_io_mode,
            "computation": computation,
            "use_kernel_calc": use_kernel_calc,
            "kernel_computation": kernel_computation,
            "show_cloud_tool": self._show_cloud_tool,
            "kanaries_api_key": self._kanaries_api_key,
            "default_tab": self._default_tab,
            **self._kwargs,
            **kwargs,
        }
        return StreamlitRenderer(self._dataset, gid=self._walker.gid, **options)

    def _raise_if_live_computation(self, target: str) -> None:
        if self._walker.kernel_computation:
            raise ValueError(f"{target} does not support kernel computation. Use computation='browser'.")
        if self._walker.cloud_computation:
            raise ValueError(f"{target} does not support cloud computation. Use computation='browser'.")
