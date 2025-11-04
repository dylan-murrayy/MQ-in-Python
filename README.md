# Run IBM MQ with Python MQI on macOS (Apple Silicon)

A minimal working demo that connects a Python app to an IBM MQ Developer Edition queue manager running in a Podman container.
It includes two Python scripts:
- producer.py — puts messages on a queue
- consumer.py — reads messages from the same queue


## Prerequisites

- macOS or Linux with:
  - Podman
  - Python 3.10+
  - Conda or venv for isolation
- IBM MQ container image (Developer edition)
- IBM MQ Toolkit on macOS (for the local Python MQI client):
  - brew tap ibm-messaging/ibmmq
  - brew install ibm-messaging/ibmmq/mqdevtoolkit
  - Ensure /opt/mqm/bin is on PATH and /opt/mqm/lib64 on DYLD_LIBRARY_PATH (macOS)


## Setup

1) Create Python environment

conda create -n mq python=3.10 -y
conda activate mq
pip install -r requirements.txt

(Or: python -m venv venv && source venv/bin/activate)

2) Initialize Podman (macOS first-time users)

podman machine init --memory 4096 --disk-size 30
podman machine start
podman info   # should print info without socket errors

3) Create MQ Secrets (stored in Podman, not in git)

printf 'adminpass' | podman secret create mqAdminPassword -
printf 'apppass'  | podman secret create mqAppPassword  -
podman secret ls

You should see:
mqAdminPassword
mqAppPassword

4) Start IBM MQ Advanced Developer container

Recommended on macOS: use a named volume (avoids virtiofs issues with bind mounts). Apple Silicon users: force amd64 platform.

podman volume create mqdata
podman run -d \
  --name mq-adv \
  --platform linux/amd64 \
  -p 1414:1414 -p 9443:9443 \
  -e LICENSE=accept \
  -e MQ_QMGR_NAME=QM1 \
  -e MQ_DEV=true \
  -e MQ_CONNAUTH_USE_HTP=true \
  --secret source=mqAdminPassword,type=mount,target=mqAdminPassword \
  --secret source=mqAppPassword,type=mount,target=mqAppPassword \
  --volume mqdata:/mnt/mqm \
  --shm-size=256m \
  icr.io/ibm-messaging/mq:9.4.4.0-r1

Wait until logs show the web server is ready and QM1 is started:

podman logs -f mq-adv

IBM MQ Console:
https://localhost:9443/ibmmq/console
Login: admin / adminpass



## Run the Demo

Terminal A — start consumer (waited gets):

python consumer.py

Terminal B — send 5 persistent messages:

python producer.py -n 5 -p

Environment variables (optional) to override defaults:

MQ_QMGR=QM1 MQ_CONN=localhost(1414) MQ_CHANNEL=DEV.APP.SVRCONN MQ_QUEUE=DEV.QUEUE.1 \
MQ_USER=app MQ_PASSWORD=apppass python producer.py



## Troubleshooting

- Cannot connect to Podman / socket errors:
  - Run: podman machine start
  - Then: podman info
- 2035 NOT_AUTHORIZED in Python:
  - Ensure you created secrets mqAdminPassword and mqAppPassword
  - Container must be started with MQ_CONNAUTH_USE_HTP=true
  - Use user=app password=apppass and channel DEV.APP.SVRCONN
- 2059 / 2538 (connectivity):
  - Confirm container is Up and port 1414 is published
  - Use localhost(1414) and channel DEV.APP.SVRCONN
- Queue open errors (2037):
  - Open the queue with input and/or output flags as needed
- Field/keyword errors in ibmmq:
  - GMO/PMO fields are CamelCase (Options, WaitInterval, Persistence)
  - Queue.put()/get() often require positional args, not keywords
- Apple Silicon:
  - Use --platform linux/amd64 on pull/run
  - If your Podman version lacks --arch on machine init, just use --platform on the container



## Inspect MQ directly

Show current queue depth from inside the container:

podman exec -it mq-adv runmqsc QM1 <<'EOF'
dis ql(DEV.QUEUE.1) curdepth
end
EOF



## Cleanup

Stop and remove the container and secrets:

podman stop mq-adv
podman rm mq-adv
podman secret rm mqAdminPassword mqAppPassword

(Optional) remove the named volume:

podman volume rm mqdata



## Requirements

requirements.txt should contain:
ibmmq>=2.3.0



## Security / Git Hygiene

- Do not commit secrets or local MQ data.
- .gitignore should exclude:
  - mq-data/, *.fdc, *.trc, *.log
  - __pycache__/, *.pyc, .DS_Store
  - venv/, .venv/, .idea/, .vscode/
  - any files named mqAdminPassword or mqAppPassword



## License

The Python demo code can be MIT-licensed. IBM MQ is licensed separately under the IBM MQ Advanced for Developers terms.
