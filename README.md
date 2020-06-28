# Builder

Basic repository CI/CD tool - the main purpose of this tool is to build repositories when
receiving webhooks from Gogs/GitHub, and triggering a deploy if configured to do so.

On successful build, the configured artifacts are uploaded to the repository's bucket.
On every build a notification is sent over the configured channels, containing a link to 
the build's logs.

## Running

There are two main entrypoints: `worker` which will spawn `WORKER_COUNT` workers to execute builds in the background,
and `webserver` which will listen for `POST`ed data on `0.0.0.0:WEBSERVER_PORT/webhook` and queue builds for the worker.

## Builder Settings

Settings in this project use dynaconf so you can read the particulars of overrides/secret management 
[here](https://dynaconf.readthedocs.io/en/latest/).

Configurable keys and explanation:

```
[development] 				# environment for dynaconf
CLONE_PATH="/tmp/"  			# root under which to clone all repos for builds
LOG_PATH="/tmp/logs"			# path to store logs when executing a build
LOG_URL="http://ci.labs/logs/{logfile}" # URL that will serve `LOG_PATH` -- should be done by something like nginx
TELEGRAM_BOT_KEY="set me up!"  		# key for the "Telegram" notifier
S3_PROFILE='ci'				# profile for S3 in .aws/config, .aws/credentials
S3_ENDPOINT='http://localhost:9000'  	# endpoint for S3 - useful if you want to specify region or use minio
DOCKERFILES.NPM="Dockerfile-npm" 	# Dockerfile to use for the 'npm' build profile
DOCKERFILES.MAKE="Dockerfile-python" 	# Dockerfile to use for the 'python' build profile
REST_DEPLOYER_SECRET='some secret'	# Secret to send to the `REST` deployer
REST_DEPLOYER_URL='http://localhost:8080/sync/deploy/{repo}/{ref}' # URL for the `REST` deployer
WEBSERVER_PORT=8080			# Port to listen on for the webhook payload
WORKER_QUEUE_NAME='ci'			# Name for the queue on which work will be scheduled
WORKER_COUNT=2				# Build Worker count (Max amount of parallel builds)
KILL_WORKERS_ON_SIGNAL=false		# Send SIGINT to workers when receiving SIGINT/SIGTERM this is useful if
your daemon manager (systemd, supervisord, initd) does not send signals to the entire process group (only sends signals
to the parent PID).

  [[development.REPOS]]
  # Array for configured repositories - you have to repeat this section for each repo you want to configure
  Name="Test Repo" 			# Repo name - only used for labeling
  GitUrl="Some URL" 			# Repo ssh url - used to match against webhooks'
  Bucket="testrepo"			# Bucket name
  TelegramChatId=1234			# Telegram chat id for the `Telegram` notifier
  Deployer="REST"			# Select Deployer -- currently only REST is implemented 
  Notifier="Telegram"			# Select Notifier -- currently only Telegram is implemented
  REST_DEPLOYER_URL='http://url/{repo}/{ref}' # Override REST_DEPLOYER_URL
```

## Repository settings

On each of the configured repositories, `Builder` will look for a file named `build.json` at the 
top of the repository root.

Each project can have multiple subprojects, which will be built independently.

For each of the subprojects, the build matching `build_mode` will be executed in the configured `dir`
 (relative to the repo root).

```build.json
{
  "subprojects": [
    {
      "name": "recipes",
      "dir": "recipes",
      "artifacts": ["frontend.tar.gz"],
      "build_mode": "npm"
    },
    {
      "name": "ktchn",
      "dir": "ktchn",
      "artifacts": ["dist/bundle.js"],
      "build_mode": "npm"
    }
  ]
}

```

## Build Modes

The builds are only executing `docker build` with different docker files based on the `build_mode` specified.  

Example `python` and `npm` `Dockerfile`s are provided in the repo. The default is `npm`.


### npm

See [Dockerfile-npm](src/Dockerfile-npm) for full source.

Adds `package.json` and `package-lock.json` to the build context and runs `npm install`, then executes `npm build`.

### python

See [Dockerfile-python](src/Dockerfile-python) for full source.

Adds `setup.py` to the build context and runs `pip install` (in a python3.8 environment), then executes `make all`.

### Custom

The file named `Dockerfile` within the subproject's path will be used for build.

Keep in mind artifacts will be searched for in `/usr/src/app/`, so ensure your output gets generated accordingly.


## Deployment

If a `Deployer` is configured on the repository, after a succesful build for all of the subprojects, the deployment
will be triggered.

### REST deployer

Sends a `POST` to the configured `REST_DEPLOYER_URL` with a payload containing only `{secret: REST_DEPLOYER_SECRET}`

## Uploading artifacts

The `artifacts` specified on a repository's build.json will be uploaded to the configured S3 bucket in the following
way:

* Directories will be compressed and uploaded as `{directory}.tar.gz`
* Files will be uploaded as they are


The upload format is `{Bucket}/{subproject}/{ref}/{artifact}` which means that if you configure your webhooks
to trigger on push, and you only push directly to `master`, you'll only ever have **one** artifact - the latest master.

If you use feature branches or release tags, those will be stored permanently.

## What projects does it build?

* Itself
* [Kitchen](https://github.com/TatianaInama/kitchen)
* [Voices of Merseyside](https://github.com/TatianaInama/voices-of-merseyside)
* [Critter Crossing](https://github.com/TatianaInama/critter-crossing)
