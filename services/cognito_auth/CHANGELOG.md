## [5.0.1] (2026-07-21)
### changes
* propagate tags from task_definition when lauching ECS task

## [5.0.0] (2026-07-20)
### features
* add ECS support for model execution
* start/poll/stop/describes are now all available on this API (stepfunction or ECS).
* get image tag from lambda / ECS task definition. no more need for an env variable.

### changes
* refactor cognito functions


## [4.2.0] (2026-03-03)
### features
* can manager user from another user group if you have access to those buckets. user group names should have the same name as the bucket to acces it (except admin that is all)

### changes
* python 3.12 and poetry

