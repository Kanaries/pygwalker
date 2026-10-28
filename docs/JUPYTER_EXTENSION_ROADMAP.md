# PyGWalker Jupyter Extension Roadmap

> Status: Round 1 implemented and verified; Rounds 2–4 planned
>
> Product goal: increase the number of natural PyGWalker entry points in Jupyter without
> changing or weakening the existing `pyg.walk()` workflow.

## 1. Product and compatibility decisions

The extension is an additional entry point, not a replacement renderer.

- The existing `pyg.walk()`/anywidget path remains the compatibility path for every Jupyter
  environment PyGWalker already supports.
- The extension is distributed as a companion package with its own Jupyter host constraints.
  Installing or upgrading the core `pygwalker` package must not implicitly activate a
  JupyterLab plugin.
- The modern extension uses one codebase for JupyterLab 4 and Notebook 7. Those products
  share the JupyterLab application and prebuilt-extension model, but they remain separate
  test targets because their available shell capabilities differ.
- JupyterLab 3 and Classic Notebook 6 do not receive the extension. Users on those hosts keep
  using `pyg.walk()` exactly as they do today.
- The extension reuses PyGWalker's Python data bridge, protocol, and frontend application. It
  must not add a second data engine or a temporary web server.

| Environment | Existing `pyg.walk()` | New extension |
|---|---:|---:|
| Classic Notebook 6 | unchanged | not supported |
| JupyterLab 3 | unchanged | not supported |
| JupyterLab 4 | unchanged | supported from Round 1 |
| Notebook 7 | unchanged | supported from Round 1 |
| VS Code / Streamlit / other adapters | unchanged | not applicable |

The intended package boundary is:

```text
pygwalker (core package)
  public API + parsers + data bridge + Graphic Walker frontend
             ^
             | narrow, versioned kernel protocol
             |
pygwalker-jupyter (companion prebuilt extension)
  sidebar + host integration + active-kernel connection
```

The core may contain a dormant kernel bridge that is imported on demand by the companion
extension. It must have no import-time registration, no JupyterLab dependency, and no effect
on `pyg.walk()`.

## 2. Delivery principles

Each round is a usable vertical product, not a collection of disconnected components.

1. A round starts with one user journey and ends only when that journey works against a real
   Jupyter host and kernel.
2. No hard-coded datasets, mock kernel, static screenshots, generated `pyg.walk(df)` cells, or
   separate local web server count as a completed journey.
3. New source types and hosts are added only after the narrower journey is stable.
4. Compatibility tests for the existing `pyg.walk()` path are release gates for every round.
5. Product instrumentation measures the funnel without recording dataframe contents, column
   values, notebook source, or file contents.

## 3. Roadmap at a glance

| Round | Product state | Complete user journey | Exit signal |
|---|---|---|---|
| 1 | **Bicycle / technical POC** | Active Notebook → host-native entry → discover pandas DataFrame → open real PyGWalker | Repeatable locally on JupyterLab 4 and Notebook 7 with real kernel communication |
| 2 | **Motorcycle / MVP** | The same journey works reliably in JupyterLab 4 and Notebook 7, including normal lifecycle changes | Installable companion wheel, CI matrix green, internal users can use it daily |
| 3 | **Small car / beta** | Users can enter from notebook variables or supported data files and recover useful sessions | Beta cohort shows reliable activation and return usage |
| 4 | **Production car / GA** | Secure, observable, performant extension across supported deployment shapes | Release gates, docs, support policy, and rollout/rollback controls are ready |

## 4. Round 1 — Bicycle / real technical POC

### 4.1 The one journey

A user on JupyterLab 4 or Notebook 7 opens a Python notebook and creates a pandas DataFrame.
In JupyterLab they open the PyGWalker sidebar; in Notebook 7 they use the PyGWalker notebook
toolbar button. They refresh, choose the DataFrame, and get a real interactive PyGWalker view
in the host's native resizable work area. Dragging fields and issuing data queries uses the
same live kernel and PyGWalker services as the notebook.

```text
real pandas DataFrame in active kernel
              ↓
PyGWalker selector discovers safe top-level variable names
              ↓
user chooses one variable
              ↓
kernel creates a real PygWalker + existing CommHandler
              ↓
host-native view mounts the real Graphic Walker frontend
              ↓
interactive data/spec requests return through the kernel comm
```

### 4.2 Fixed scope

- Host: JupyterLab `>=4.2,<5` and Notebook `>=7.2,<8` for the Round 1 artifact.
- Session: the currently active `NotebookPanel` and its connected Python kernel.
- Data: top-level variables whose runtime type is `pandas.DataFrame`.
- Discovery: explicit refresh plus one initial refresh when the host-native selector is shown.
- View: one extension-owned PyGWalker document at a time. JupyterLab uses a main-area split;
  Notebook 7 uses its native resizable right panel because its document-centric main area
  accepts only the active notebook. Both hosts preserve a `768px` minimum explorer content
  width and scroll horizontally below it. Selecting another DataFrame replaces the view's
  session.
- Computation: real kernel computation through the existing `DataBridge` and `CommHandler`.
- Installation: a development/prebuilt extension artifact in this repository; publishing to
  PyPI is deliberately deferred.
- Compatibility: existing `pyg.walk(df)` continues to use anywidget and receives a regression
  test; the extension does not patch or intercept it.

### 4.3 Explicit non-goals

Round 1 does not include JupyterLab 3, Classic Notebook 6, CSV/Excel entry points,
polars/pyarrow/Spark discovery, non-Python kernels, several open
PyGWalker documents, persistence across restart, automatic variable watching, JupyterHub
hardening, remote contents, telemetry, marketplace polish, or public package publication.

These exclusions are constraints, not placeholders: they prevent lifecycle, packaging, and
file-I/O work from hiding whether the core activation loop is valuable.

### 4.4 Technical slices and ordered checkpoints

#### R1.1 — Companion extension shell

- Add a standalone prebuilt JupyterLab extension workspace shared by JupyterLab
  `>=4.2,<5` and Notebook `>=7.2,<8`; do not add JupyterLab or Notebook packages to
  PyGWalker's runtime Python dependencies.
- Register a PyGWalker sidebar item and command for JupyterLab, plus a Notebook 7 toolbar
  entry that reveals the same selector in its native left panel.
- Resolve the active notebook and show actionable empty states for no notebook/no kernel.

Checkpoint: the host-appropriate entry appears only when the companion extension is
installed, and opening it does not import or invoke PyGWalker in the kernel.

#### R1.2 — Narrow kernel bridge

- Add an on-demand, idempotent core bridge with a versioned comm target.
- Bootstrap it by executing a silent, fixed import/register statement in the active kernel.
- List only safe top-level pandas DataFrame variable names and basic metadata (rows, columns).
  Do not evaluate arbitrary expressions and do not serialize cell values for discovery.
- Reject stale/unknown names when opening a session.

Checkpoint: a DataFrame created after the notebook starts appears after refresh; a deleted or
rebound variable cannot be opened from a stale result.

#### R1.3 — Real PyGWalker session over the comm

- Construct a real `Walker`/`PygWalker` for the selected object with kernel computation.
- Adapt the Jupyter kernel comm to the existing `BaseCommunication` contract and register the
  existing `CommHandler` endpoints rather than duplicating them.
- Return frontend props and a session id through a JSON-safe envelope; route request/response
  messages by request id on the POC's single session comm.
- Dispose or replace the prior POC session when a second DataFrame is opened.

Checkpoint: real field metadata and data queries originate in the selected kernel object;
there is no mock API or copied static HTML.

#### R1.4 — Reusable frontend mount

- Expose a small supported mount/unmount boundary around the existing PyGWalker React app.
- Inject the extension's communication adapter without changing the anywidget adapter.
- Mount the app in a JupyterLab main-area widget or Notebook 7 native right panel and resize
  it with the host shell.
- Keep the POC's single-session limitation explicit because current frontend stores are
  process-wide singletons.

Checkpoint: the selected DataFrame opens as the real Graphic Walker UI and a user can create
or modify a chart.

#### R1.5 — Proof and developer handoff

- Unit-test DataFrame discovery, stale-name rejection, protocol errors, and session
  replacement.
- Typecheck/build both the existing frontend and the extension.
- Run existing Python tests relevant to `pyg.walk()`/anywidget.
- Add JupyterLab 4 and Notebook 7 browser smoke tests for the complete journey, or, if browser
  automation is blocked by a local host, record a deterministic manual test script and the
  exact blocker.
- Document local install, link, launch, and uninstall commands for the POC.

Checkpoint: a new contributor can reproduce the full journey from the documentation, and
uninstalling/disabling the companion extension leaves `pyg.walk()` behavior unchanged.

### 4.5 Round 1 definition of done

Round 1 is complete only when all of the following are true:

- [x] In real JupyterLab 4 and Notebook 7 Python notebooks, `df = pandas.DataFrame(...)` is
      discovered from the active kernel.
- [x] Choosing `df` opens the real PyGWalker UI in the host-native resizable work area without
      inserting or running a user-visible `pyg.walk(df)` cell.
- [x] At least one interactive chart operation causes real frontend↔kernel protocol traffic
      and succeeds.
- [x] Refresh, no-notebook, no-kernel, empty-list, stale-variable, and Python-side error states
      are understandable and recoverable.
- [x] The bridge does not evaluate a client-supplied Python expression.
- [x] Existing `pyg.walk(df)` still renders through anywidget with the extension installed and
      with it absent.
- [x] Core runtime dependencies do not gain JupyterLab/Lumino/Node packages.
- [x] The POC build and test commands are documented and repeatable.

The reproducible browser journey, observed protocol traffic, environment, and cleanup steps
are recorded in [`JUPYTER_EXTENSION_POC_TEST.md`](JUPYTER_EXTENSION_POC_TEST.md).

### 4.6 Round 1 stop/go review

Before adding more source types, run five to ten internal sessions and review:

- Can users discover the sidebar without instruction?
- Do they understand that the list represents variables in the active kernel?
- What percentage of sidebar opens reach a rendered PyGWalker view?
- Is the main-area document a better interaction surface than an embedded/right-sidebar UI?
- Which failure dominates: extension discovery, kernel bootstrap, DataFrame discovery, or UI
  load time?

If the activation loop is not compelling, change the entry interaction before broadening the
compatibility matrix.

## 5. Round 2 — Motorcycle / daily-usable MVP

Round 2 turns the validated vertical slice into a supportable companion package.

### Scope

- Automate and harden the shared JupyterLab 4 and Notebook 7 codebase, keeping host-specific
  shell behavior explicit where their document models differ.
- Handle active-notebook switches, kernel restart/reconnect, notebook close, and comm
  disposal without leaking sessions.
- Discover pandas, polars, and pyarrow top-level variables with bounded metadata work.
- Support multiple extension documents, isolating frontend state and kernel sessions.
- Package and install as a separate `pygwalker-jupyter` wheel containing a prebuilt extension;
  declare the compatible core range and JupyterLab host range independently.
- Add clear version-mismatch, missing-core, missing-kernel, and unsupported-kernel UX.
- Add CI for minimum/latest JupyterLab 4, Notebook 7, companion-package install/uninstall,
  and core-only legacy regression coverage.
- Add privacy-preserving activation funnel events behind the existing privacy setting.

### Exit criteria

- Internal users can use it for normal notebook work for one week without manual recovery.
- The same wheel passes automated end-to-end journeys in JupyterLab 4 and Notebook 7.
- Kernel restart, notebook switching, and extension disable/uninstall are covered.
- Core-only installs and old-host `pyg.walk()` workflows remain unaffected.

## 6. Round 3 — Small car / data-entry beta

Round 3 increases trigger opportunities after the kernel-variable loop is reliable.

### Scope

- Register “Open with PyGWalker” for CSV/TSV through Jupyter's contents model.
- Add Excel workbook entry with explicit sheet selection and bounded preview/size handling.
- Define local versus remote/JupyterHub file semantics; file access must use supported server
  APIs rather than assuming the browser and kernel share a filesystem.
- Add recent sources and recoverable saved exploration state without silently copying source
  data.
- Add large-file limits, cancellation, progress, encoding errors, and Excel engine guidance.
- Validate common JupyterHub/base-URL/auth deployments and document the supported subset.
- Run an opt-in beta with funnel, latency, error-class, and return-use measurements.

### Exit criteria

- Notebook variable, CSV/TSV, and Excel journeys are complete and recoverable.
- Remote contents and kernel-local paths have explicit, tested behavior.
- Beta metrics identify the sources of activation and the dominant drop-off points without
  collecting user data contents.

## 7. Round 4 — Production car / GA

Round 4 makes the extension safe to recommend broadly.

### Scope

- Performance budgets for activation time, large-table queries, bundle size, and memory;
  remove duplicated frontend payloads where package boundaries allow it.
- Threat model and hardening for kernel execution, comm validation, HTML rendering, file
  access, and cross-origin/base-URL behavior.
- Accessibility, keyboard navigation, theme integration, localization readiness, and polished
  empty/error/loading states.
- Compatibility policy, deprecation policy, troubleshooting guide, support matrix, release
  notes, and migration/uninstall instructions.
- Staged rollout, feature kill switch, version pin/rollback plan, and operational dashboards.
- Public companion-package release only after install/upgrade/uninstall tests pass against the
  supported matrix.

### Exit criteria

- Security, accessibility, performance, compatibility, documentation, and operations release
  gates are signed off.
- A failed extension upgrade can be rolled back without changing the installed core
  PyGWalker workflow.
- Product metrics show that the added entry points improve meaningful activation and return
  usage, not merely sidebar impressions.

## 8. Cross-round risks and controls

| Risk | Control |
|---|---|
| Extension breaks old Jupyter environments | Separate distribution; no auto-enable from core; legacy/core-only CI |
| Host/version coupling grows into the core wheel | All JupyterLab/Lumino dependencies stay in the companion workspace/package |
| Arbitrary kernel execution | Fixed bootstrap statement; discovered-name allowlist; never evaluate client expressions |
| Protocols drift | Versioned extension handshake; reuse existing generated PyGWalker protocol and `CommHandler` |
| Frontend singleton state breaks multiple views | One view in Round 1; isolate stores before enabling multiple documents in Round 2 |
| Large data freezes discovery or browser | Metadata-only discovery; existing kernel computation; explicit limits and cancellation later |
| JupyterLab works but Notebook 7 fails | Separate end-to-end targets even though implementation is shared |
| Activation rises but retention does not | Instrument the full funnel and review stop/go signals at every round |

## 9. Release and dependency guardrails

- No JupyterLab dependency is added to `[project.dependencies]` in the core package.
- The companion JavaScript package declares JupyterLab `4.x` compatibility; its Python wheel
  declares an explicit compatible PyGWalker range.
- Core and companion packages are versioned independently, with a handshake that fails with a
  useful message instead of trying to operate across an unsupported protocol pair.
- Generated frontend bundles remain build artifacts. Source, lockfiles, manifests, and tests
  are reviewed; generated PyGWalker `templates/dist` files are not committed.
- Every release matrix contains both positive extension cases and a negative/core-only case.
