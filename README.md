# darren-iac GitHub Actions

Reusable workflows shared by repositories in the darren-iac estate. Consumers
pin workflow calls to a full commit SHA.

## Workflows

- `buildrun-request.yaml` creates and follows a trusted Shipwright BuildRun on
  the etcdrich ARC runner. The declarative Build remains owned by Flux.
- `image-build.yaml` is the organization-wide Buildx contract. It always uses
  a full `mode=max` registry cache at `:buildcache` and pushes one immutable
  tag: `git-<unix-seconds>-<full-commit-sha>` for trusted builds, or
  `pr-<number>-<full-commit-sha>` for pull requests. It never publishes
  `latest` or a mutable branch tag. Callers normally use the shared
  `arc-runners-darren-iac` pool; a different runner requires a real capability
  boundary such as Brainiac's machine-bound workload.
