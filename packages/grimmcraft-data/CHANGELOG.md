# Changelog — grimmcraft-data

## fix(tasks): correct the root Taskfile include for this package

The root `Taskfile.yml` referenced `Taskfile.yml`, but this package's tasks live
in `Taskfile.yaml`; the include was pointed at the correct file so `data:` tasks
load. No changes to the package sources themselves (it already used `uv_build`
with `module-root = "srcs"`).
