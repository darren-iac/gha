# darren-iac GitHub Actions

Reusable workflows shared by repositories in the darren-iac estate. Consumers
pin workflow calls to a full commit SHA.

## Workflows

- `buildrun-request.yaml` creates and follows a trusted Shipwright BuildRun on
  the etcdrich ARC runner. The declarative Build remains owned by Flux.
- `image-build.yaml` is the organization-wide Buildx contract. It always
  imports the full `mode=max` registry cache at `:buildcache`. A trusted build
  pushes one immutable tag, `git-<unix-seconds>-<full-commit-sha>`, and
  refreshes the cache. A pull request builds but pushes nothing. It never
  publishes `latest` or a mutable branch tag. Callers normally use the shared
  `arc-runners-darren-iac` pool; a different runner requires a real capability
  boundary such as Brainiac's machine-bound workload.

  Credentials are chosen by event, never by the caller. Callers pass
  `secrets: inherit`; the repository secrets `DOCKERHUB_USERNAME`,
  `DOCKERHUB_READ_TOKEN` and `DOCKERHUB_WRITE_TOKEN` supply them (managed in
  darren-iac/iac `tofu/github`). They are repository secrets, not organization
  secrets: on GitHub Free, organization secrets never reach a private
  repository. A `pull_request` build logs in read-only,
  imports the cache and builds every stage, but pushes nothing, writes no cache
  and creates no repository, so untrusted PR code cannot touch the registry. A
  trusted build logs in with the write token and fails closed if it is absent.
  Login retries Docker Hub's per-IP rate limit.

  Before a trusted build pushes, the workflow calls the pinned
  `ensure-dockerhub-private` action. A missing repository is created with
  `is_private: true` and read back to prove its visibility. An existing private
  repository is a no-op. An existing public repository fails the build before
  any push; the workflow never relies on Docker Hub's default visibility.
