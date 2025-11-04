# Run IBM MQ with Python MQI on macOS (Apple Silicon)  

Demonstrates the Point-to-Point Messaging pattern, a reliable, one-to-one message flow between a producer and a consumer via a queue.

https://github.com/ibm-messaging/mq-mqi-python  

**Goal:** Run a local IBM MQ Developer Edition queue manager in a container on macOS (M1/M2) and connect to it using the official IBM MQ Python MQI (`ibmmq`) library.  
This tutorial shows how to:
- Run IBM MQ Developer Edition (9.4+) in Podman on macOS (Apple Silicon or Intel)
- Connect to it from a Python app using the IBM MQ MQI (`ibmmq`) library
- Send and receive messages programmatically

By the end, you’ll have a working producer and consumer written in Python communicating through a local MQ queue manager.

---

### Prerequisites
- macOS 13 or later (Intel or Apple Silicon)  
- Podman 5.x  
- Homebrew  
- Python 3.10+ (Conda, pyenv, or system Python are all fine)

---

### Step 1 — Install the IBM MQ client toolkit  
The Python MQI library needs the MQ C client libraries installed locally.

```bash
brew tap ibm-messaging/ibmmq
brew install ibmmq-client
```

Then verify the toolkit is available:

```bash
ls /opt/mqm/lib64
```

If you see `libmqic_r.dylib` and similar libraries, you’re good.

---

### Step 2 — Create and activate a Python environment

```bash
conda create -n mq python=3.10 -y
conda activate mq
pip install ibmmq
```

---

### Step 3 — Initialize a Podman machine  
Apple Silicon uses a Linux VM under the hood.  
Create and start it once:

```bash
podman machine init --cpus 4 --memory 4096 --disk-size 30
podman machine start
podman info
```

---

### Step 4 — Create MQ secrets for the app and admin user

```bash
printf 'adminpass' | podman secret create mqAdminPassword -
printf 'apppass'  | podman secret create mqAppPassword -
```

List to confirm:

```bash
podman secret ls
```

You should see both secrets listed.

---

### Step 5 — Run the MQ Developer Edition container  
Create and run the queue manager (`QM1`) with the developer configuration.

```bash
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
```

Then check that it’s up:

```bash
podman ps
podman logs -f mq-adv | grep "Web application available"
```

Once you see `QM1 started` and `mqweb server is ready`, you can open the MQ Console:  
🔗 https://localhost:9443/ibmmq/console

Login with:  
User: `admin`  
Password: `adminpass`

---

### Step 6 — Test Python connectivity  
In your `MQ-in-Python` directory, create the following two scripts:  
`producer.py`  
`consumer.py`

---

### Step 7 — Run the demo  

Start the consumer first:

```bash
python consumer.py
```

In another terminal, send messages:

```bash
python producer.py
```

Expected output (producer):

```
PUT: hello from python 1 @ 1761913992.200
...
✅ done
```

Expected output (consumer):

```
GET: hello from python 1 @ 1761913992.200
GET: hello from python 2 @ 1761913992.256
...
```

🎉 **You’re done!**

You now have:
- A working IBM MQ Developer queue manager running in Podman  
- A Python MQI client successfully connecting, putting, and getting messages



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
