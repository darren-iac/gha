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

  Before Buildx runs, the workflow calls the pinned
  `ensure-dockerhub-private` action. A missing repository is created with
  `is_private: true` and read back to prove its visibility. An existing private
  repository is a no-op. An existing public repository fails the build before
  any push; the workflow never relies on Docker Hub's default visibility.
- Multi-image releases pass a shared `candidate-<run-id>-<full-commit-sha>` tag
  to each `image-build.yaml` call. Flux ignores candidates. After every build
  succeeds, `image-promote-bundle.yaml` applies one shared
  `git-<unix-seconds>-<full-commit-sha>` tag to the exact output digests. This
  prevents a failed coordinated build from becoming deployable. Because Docker
  Hub repositories cannot be updated atomically, the consumer repository must
  also enforce release parity in CI before merging Flux's promotion PR.
