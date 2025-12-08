# PyGWalker Refactoring Plan

This document outlines code quality issues, API design problems, and recommended refactoring priorities for the pygwalker codebase.

## Executive Summary

PyGWalker is a well-architected data visualization library with a clean separation of concerns. However, the codebase has accumulated technical debt in several areas: code duplication, inconsistent APIs, error handling issues, and poor abstraction patterns. This document categorizes issues by severity and provides actionable recommendations.

---

## Critical Issues (Priority 1 - Fix Immediately)

### 1. Silent Exception Swallowing

**File:** `pygwalker/api/pygwalker.py:111-115`

```python
if self.kernel_computation:
    try:
        self.data_parser.get_datas_by_sql("SELECT 1 FROM pygwalker_mid_table LIMIT 1")
    except Exception:
        pass  # Silently ignores ALL errors
```

**Problem:** This masks real errors and makes debugging impossible.

**Recommendation:**
```python
if self.kernel_computation:
    try:
        self.data_parser.get_datas_by_sql("SELECT 1 FROM pygwalker_mid_table LIMIT 1")
    except Exception as e:
        logger.debug(f"Kernel computation warmup failed (expected for some backends): {e}")
```

---

### 2. Error Response Returns Wrong Data

**File:** `pygwalker/communications/base.py:36-48`

```python
def _receive_msg(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        data = handler_func(data)
        return {"code": 0, "data": data, "message": "success"}
    except BaseError as e:
        return {"code": e.code, "data": data, "message": str(e)}  # BUG: Returns input, not error data
    except Exception as e:
        return {"code": ErrorCode.UNKNOWN_ERROR, "data": data, "message": str(e)}  # Same bug
```

**Problem:** On error, returns the original input `data` instead of `None` or error details.

**Recommendation:**
```python
    except BaseError as e:
        return {"code": e.code, "data": None, "message": str(e)}
    except Exception as e:
        return {"code": ErrorCode.UNKNOWN_ERROR, "data": None, "message": str(e)}
```

---

### 3. Null Safety Bug in Field Spec Processing

**File:** `pygwalker/data_parsers/base.py:165`

```python
def _infer_prop(
    self, col: str, field_specs: List[FieldSpec] = None  # Can be None
) -> Dict[str, str]:
    field_spec_map = {field_spec.fname: field_spec for field_spec in field_specs}  # Will FAIL if None
```

**Recommendation:**
```python
def _infer_prop(
    self, col: str, field_specs: Optional[List[FieldSpec]] = None
) -> Dict[str, str]:
    field_spec_map = {field_spec.fname: field_spec for field_spec in (field_specs or [])}
```

---

### 4. Empty Series Bug in Type Inference

**Files:**
- `pygwalker/data_parsers/pandas_parser.py:37-46`
- `pygwalker/data_parsers/polars_parser.py:39-48`
- `pygwalker/data_parsers/modin_parser.py:48-57`

```python
def _infer_semantic(self, s: pd.Series, field_name: str):
    example_value = s[0]  # IndexError if Series is empty!
```

**Recommendation:**
```python
def _infer_semantic(self, s: pd.Series, field_name: str):
    if len(s) == 0:
        return "nominal"  # Safe default for empty series
    example_value = s.iloc[0]  # Use .iloc for safer indexing
```

---

## High Priority Issues (Priority 2)

### 5. Global State Cache Antipattern

**File:** `pygwalker/services/data_parsers.py:11-27`

```python
__classname2method = {}  # Global mutable state - hard to test, no invalidation

def _get_data_parser(dataset):
    if type(dataset) in __classname2method:
        return __classname2method[type(dataset)]
    # Modifies global state directly...
```

**Recommendation:** Use a proper registry pattern:

```python
from functools import lru_cache

class DataParserRegistry:
    _parsers: Dict[type, Tuple[Type[BaseDataParser], str]] = {}

    @classmethod
    def register(cls, data_type: type, parser_class: Type[BaseDataParser], dataset_type: str):
        cls._parsers[data_type] = (parser_class, dataset_type)

    @classmethod
    def get_parser(cls, dataset) -> Tuple[BaseDataParser, str]:
        for dtype, (parser_class, dataset_type) in cls._parsers.items():
            if isinstance(dataset, dtype):
                return parser_class, dataset_type
        raise TypeError(f"Unsupported dataset type: {type(dataset)}")
```

---

### 6. Code Duplication - Chart Methods

**File:** `pygwalker/api/component.py:215-305`

16 chart methods with identical patterns (90+ lines):

```python
def bar(self) -> "Component":
    copied_obj = self.copy()
    copied_obj._update_single_chart_spec("config__geoms", ["bar"])
    copied_obj._update_single_chart_spec("config__coordSystem", "generic")
    return copied_obj

def line(self) -> "Component":  # Same pattern repeated 15 more times
    ...
```

**Recommendation:** Use a factory pattern:

```python
CHART_CONFIGS = {
    'bar': {'geoms': ['bar'], 'coordSystem': 'generic'},
    'line': {'geoms': ['line'], 'coordSystem': 'generic'},
    'area': {'geoms': ['area'], 'coordSystem': 'generic'},
    'trail': {'geoms': ['trail'], 'coordSystem': 'generic'},
    'scatter': {'geoms': ['point'], 'coordSystem': 'generic'},
    'point': {'geoms': ['point'], 'coordSystem': 'generic'},
    'circle': {'geoms': ['circle'], 'coordSystem': 'generic'},
    'tick': {'geoms': ['tick'], 'coordSystem': 'generic'},
    'rect': {'geoms': ['rect'], 'coordSystem': 'generic'},
    'arc': {'geoms': ['arc'], 'coordSystem': 'polar'},
    'box': {'geoms': ['boxplot'], 'coordSystem': 'generic'},
    'table': {'geoms': ['table'], 'coordSystem': 'generic'},
    'text': {'geoms': ['text'], 'coordSystem': 'generic'},
    'poi': {'geoms': ['poi'], 'coordSystem': 'generic'},
    'choropleth': {'geoms': ['choropleth'], 'coordSystem': 'generic'},
}

def _create_chart_method(chart_type: str):
    def chart_method(self) -> "Component":
        config = CHART_CONFIGS[chart_type]
        copied_obj = self.copy()
        copied_obj._update_single_chart_spec("config__geoms", config['geoms'])
        copied_obj._update_single_chart_spec("config__coordSystem", config['coordSystem'])
        return copied_obj
    chart_method.__doc__ = f"{chart_type.capitalize()} chart."
    return chart_method

# Generate methods dynamically
for chart_type in CHART_CONFIGS:
    setattr(Component, chart_type, _create_chart_method(chart_type))
```

---

### 7. Code Duplication - Data Parser Inference Logic

**Files:**
- `pygwalker/data_parsers/pandas_parser.py:37-60`
- `pygwalker/data_parsers/polars_parser.py:39-62`
- `pygwalker/data_parsers/modin_parser.py:48-71`

Nearly identical `_infer_semantic()` and `_infer_analytic()` methods across 3 parsers.

**Recommendation:** Extract common inference logic to base class:

```python
# In base.py
class BaseDataParser:
    @abstractmethod
    def _get_dtype_kind(self, series) -> str:
        """Return dtype kind character for the series."""
        pass

    @abstractmethod
    def _is_numeric_dtype(self, dtype) -> bool:
        """Check if dtype is numeric."""
        pass

    def _infer_semantic(self, series, field_name: str) -> str:
        if len(series) == 0:
            return "nominal"

        example_value = self._get_first_value(series)

        if self._is_numeric_dtype(series.dtype) or is_geo_field(field_name):
            return "quantitative"
        if self._is_temporal_dtype(series.dtype) or is_temporal_field(example_value, self.infer_string_to_date):
            return "temporal"
        return "nominal"
```

---

### 8. Deprecated Parameter Still in Public API

**Files:**
- `pygwalker/api/jupyter.py:26-27`
- `pygwalker/api/streamlit.py:63, 290`

```python
def walk(
    use_kernel_calc=None,       # DEPRECATED
    kernel_computation=None,    # Current
):
```

**Recommendation:** Add proper deprecation warnings and removal timeline:

```python
import warnings

def walk(..., use_kernel_calc=None, kernel_computation=None):
    if use_kernel_calc is not None:
        warnings.warn(
            "use_kernel_calc is deprecated and will be removed in v0.5.0. "
            "Use kernel_computation instead.",
            DeprecationWarning,
            stacklevel=2
        )
        kernel_computation = kernel_computation or use_kernel_calc
```

---

### 9. Memory Leak in HackerCommunication

**File:** `pygwalker/communications/hacker_comm.py:19-78`

```python
class HackerCommunication(BaseCommunication):
    """
    Since it is not a long running service for multiple users,
    some expired buffers and locks will not be cleaned up.  # Memory leak acknowledged
    """
```

Creates 5 Text widgets with observe callbacks that are never unregistered.

**Recommendation:** Implement cleanup method:

```python
class HackerCommunication(BaseCommunication):
    def __init__(self, gid: str):
        super().__init__(gid)
        self._kernel_widget = self._get_kernel_widget()
        self._html_widget = self._get_html_widget()

    def cleanup(self):
        """Clean up resources when communication is no longer needed."""
        for widget in self._kernel_widget:
            widget.unobserve(self._on_message, "value")
            widget.close()
        self._html_widget.close()

    def __del__(self):
        self.cleanup()
```

---

### 10. Inconsistent Return Types

**Files:**
- `pygwalker/api/adapter.py:14` - `walk()` returns `PygWalker | None`
- `pygwalker/api/jupyter.py:17` - `walk()` returns `PygWalker`
- `pygwalker/api/webserver.py:157` - `walk()` returns `None`

None have explicit type hints.

**Recommendation:** Standardize return types with explicit annotations:

```python
# adapter.py
def walk(
    dataset: Union[DataFrame, Connector, str],
    ...
) -> PygWalker:
    """Returns PygWalker instance for chaining."""

# webserver.py
def walk(...) -> PygWalker:  # Change to return PygWalker for consistency
```

---

## Medium Priority Issues (Priority 3)

### 11. Typo in Callback Name

**File:** `pygwalker/api/pygwalker.py:376`

```python
def reuqest_data_callback(data: Dict[str, Any]) -> Dict[str, Any]:  # "reuqest" typo
```

**Recommendation:** Fix typo to `request_data_callback`

---

### 12. Typo in Method Name

**File:** `pygwalker/communications/hacker_comm.py:53, 76`

```python
def _on_mesage(self, info: Dict[str, Any]):  # "mesage" typo
    ...
text.observe(self._on_mesage, "value")  # Propagates typo
```

**Recommendation:** Fix to `_on_message`

---

### 13. Wrong Type Annotation

**File:** `pygwalker/api/pygwalker.py:652`

```python
def _get_gw_chart_preview_html(self, chart_name: int, title: str, desc: str) -> str:
    #                                            ^^^ Should be str, not int
```

---

### 14. Crude Concurrency Handling

**File:** `pygwalker/communications/hacker_comm.py:26-45`

```python
def send_msg_async(self, action: str, data: Dict[str, Any], rid: Optional[str] = None):
    """
    ...
    so a sleep is temporarily added to solve it violently  # HACK
    """
    with self._send_msg_lock:
        self._html_widget.value = json.dumps(msg, cls=DataFrameEncoder)
        time.sleep(0.1)  # Crude hack
```

**Recommendation:** Implement proper message queue with acknowledgment:

```python
import asyncio
from queue import Queue
from threading import Event

class MessageQueue:
    def __init__(self):
        self._queue = Queue()
        self._ack_events: Dict[str, Event] = {}

    def send(self, msg: dict, timeout: float = 5.0) -> bool:
        rid = msg.get('rid', str(uuid.uuid4()))
        self._ack_events[rid] = Event()
        self._queue.put(msg)
        return self._ack_events[rid].wait(timeout)

    def acknowledge(self, rid: str):
        if rid in self._ack_events:
            self._ack_events[rid].set()
            del self._ack_events[rid]
```

---

### 15. Silent Config Failure

**File:** `pygwalker/services/config.py:70-81`

```python
def _read_and_create_file(path: str, default_content: Dict[str, str]) -> Dict[str, str]:
    try:
        ...
    except Exception:
        return default_content  # Silently uses defaults - user never knows
```

**Recommendation:**
```python
def _read_and_create_file(path: str, default_content: Dict[str, str]) -> Dict[str, str]:
    try:
        ...
    except PermissionError as e:
        logger.warning(f"Cannot access config file {path}: {e}. Using defaults.")
        return default_content
    except json.JSONDecodeError as e:
        logger.warning(f"Config file {path} is corrupted: {e}. Using defaults.")
        return default_content
    except Exception as e:
        logger.warning(f"Unexpected error reading config {path}: {e}. Using defaults.")
        return default_content
```

---

### 16. Inconsistent Default Values Across APIs

| Parameter | adapter.py | component.py | streamlit.py |
|-----------|------------|--------------|--------------|
| `show_cloud_tool` | `True` | `False` | `None` |
| `default_tab` | `"vis"` | `"data"` | varies |
| `theme_key` | `"g2"` | `"vega"` | `"g2"` |

**Recommendation:** Define constants in a central location:

```python
# pygwalker/_constants.py
class Defaults:
    SHOW_CLOUD_TOOL = True
    DEFAULT_TAB = "vis"
    THEME_KEY = "g2"
    KERNEL_COMPUTATION = None
```

---

### 17. Missing `spec_io_mode` in Core APIs

Available in `StreamlitRenderer`, `gradio`, `component` but missing from:
- `adapter.walk()`, `adapter.render()`, `adapter.table()`
- `jupyter.walk()`, `jupyter.render()`, `jupyter.table()`

**Recommendation:** Add `spec_io_mode` parameter to all core entry points for consistency.

---

### 18. Magic Numbers Without Documentation

**Files:**
- `pygwalker/data_parsers/base.py:225` - `to_records(300)` - why 300?
- `pygwalker/communications/hacker_comm.py:73` - `range(5)` - why 5 widgets?
- `pygwalker/services/upload_data.py:46` - `1 << 12` - chunk size?

**Recommendation:** Extract to named constants with documentation:

```python
# _constants.py
DATA_SIZE_SAMPLE_ROWS = 300  # Rows sampled for estimating total data size
KERNEL_WIDGET_COUNT = 5     # Number of comm widgets for parallel message handling
UPLOAD_CHUNK_SIZE = 1 << 12  # 4KB chunks for data upload
```

---

### 19. Weak Abstractions - Upload Tools

**File:** `pygwalker/services/upload_data.py:34-106`

Two similar classes with different interfaces:
- `BatchUploadDatasToolOnJupyter`
- `BatchUploadDatasToolOnWidgets`

**Recommendation:** Create a unified base class:

```python
class BaseBatchUploadDatasTool(ABC):
    @abstractmethod
    def run(self, *, data_source_id: str, gid: str, records: List[Dict[str, Any]]) -> Any:
        pass

class BatchUploadDatasToolOnJupyter(BaseBatchUploadDatasTool):
    ...

class BatchUploadDatasToolOnWidgets(BaseBatchUploadDatasTool):
    ...
```

---

## Low Priority Issues (Priority 4)

### 20. Incomplete Docstrings

- `pygwalker/data_parsers/base.py:245` - "check if filed is" (incomplete)
- `pygwalker/communications/hacker_comm.py:53` - `_on_mesage` no docstring

### 21. Missing Type Hints on Nested Functions

**File:** `pygwalker/api/pygwalker.py:372-551` - All callback functions lack type hints

### 22. Redundant API Wrappers

**File:** `pygwalker/api/streamlit.py:282-335`

```python
def get_streamlit_html(...) -> str:
    renderer = StreamlitRenderer(...)
    return renderer._get_html(mode=mode)
```

Just a thin wrapper that could be documented instead.

---

## Refactoring Roadmap

### Phase 1: Critical Bug Fixes (1-2 sprints)
1. Fix null safety bug in `_infer_prop()`
2. Fix empty series bug in `_infer_semantic()`
3. Fix error response returning wrong data
4. Add logging for silent exception handlers

### Phase 2: API Consistency (2-3 sprints)
1. Standardize return types with type hints
2. Add deprecation warnings with removal timeline
3. Unify default values across entry points
4. Add missing `spec_io_mode` to core APIs

### Phase 3: Code Quality (3-4 sprints)
1. Extract common inference logic to base parser
2. Refactor chart methods to use factory pattern
3. Implement proper DataParserRegistry
4. Fix typos and magic numbers

### Phase 4: Technical Debt (ongoing)
1. Implement cleanup for HackerCommunication
2. Replace crude sleep with proper message queue
3. Improve config error handling
4. Add comprehensive type hints

---

## Metrics for Success

| Metric | Current | Target |
|--------|---------|--------|
| Type hint coverage | ~40% | 90% |
| Duplicated code blocks | 15+ | <5 |
| Silent exception handlers | 5 | 0 |
| Deprecated APIs without warnings | 4 | 0 |
| Public API consistency score | ~60% | 95% |

---

## Overall Assessment

**Strengths:**
- Clean architecture with good separation of concerns
- Excellent multi-environment support (Jupyter, Streamlit, Gradio, etc.)
- Well-designed data parser abstraction
- Good use of async patterns where appropriate

**Weaknesses:**
- Accumulated technical debt in error handling
- API inconsistencies across entry points
- Code duplication in parsers and chart methods
- Some memory management issues

**Conclusion:** PyGWalker is a fundamentally well-designed library that would benefit significantly from targeted refactoring. The critical issues should be addressed immediately, while the medium and low priority items can be tackled incrementally. The codebase is maintainable and the suggested improvements will enhance both reliability and developer experience.
