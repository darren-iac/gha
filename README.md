# darren-iac GitHub Actions

Secret-free reusable workflows shared by repositories in the darren-iac
estate. Consumers pin workflow calls to a full commit SHA.

## Workflows

- `buildrun-request.yaml` creates and follows a trusted Shipwright BuildRun on
  the etcdrich ARC runner. The declarative Build remains owned by Flux.
