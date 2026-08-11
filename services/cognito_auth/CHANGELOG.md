## [5.2.0] (2026-08-11)
### changes
* Change RunPayload. pass params directly instead of launcher args. we create launcher_arg = {'params': params, 'training_folder': '/tmp'} here

### Bug fixes
* auth to microservice buckets was failing.

## [5.1.1] (2026-07-24)
### changes
* for ECS, return the reason the container / task exited in the error. (ex: user stopped, OutOfMemoryError)

## [5.1.0] (2026-07-24)
### changes
* admin role now uses a single policy with prefix to have access to all quetzal-* buckets. need to list all buckets from s3.listBuckets(). we had reach the max number of inline policy for a role. needed a new method

## [5.0.2] (2026-07-23)
### changes
* IMAGE_TAG env variable is now defined in the docker build (dockerfile). no more injection when lauching ECS task

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

