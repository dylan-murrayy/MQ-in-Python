#!/usr/bin/env python3
import os, time, argparse, sys
import ibmmq

QMGR    = os.getenv("MQ_QMGR", "QM1")
CHANNEL = os.getenv("MQ_CHANNEL", "DEV.APP.SVRCONN")
CONN    = os.getenv("MQ_CONN", "localhost(1414)")
QUEUE   = os.getenv("MQ_QUEUE", "DEV.QUEUE.1")
USER    = os.getenv("MQ_USER", "app")
PASSWORD= os.getenv("MQ_PASSWORD", "apppass")

# constants (robust)
try:
    from ibmmq.constants import MQC
except Exception:
    MQC = getattr(ibmmq, "MQC", None)

def mqc_val(name, fallback):
    return getattr(MQC, name, fallback) if MQC else fallback

MQOO_OUTPUT          = mqc_val("MQOO_OUTPUT",          0x00000010)
MQOO_INPUT_AS_Q_DEF  = mqc_val("MQOO_INPUT_AS_Q_DEF",  0x00000001)
MQPER_PERSISTENT     = mqc_val("MQPER_PERSISTENT",     1)

def main():
    ap = argparse.ArgumentParser(description="IBM MQ producer")
    ap.add_argument("-n", "--count", type=int, default=5, help="messages to send")
    ap.add_argument("-p", "--persistent", action="store_true", help="send as persistent")
    args = ap.parse_args()

    print(f"Connecting to {QMGR} via {CHANNEL}@{CONN} as {USER} …")
    qmgr = ibmmq.connect(QMGR, CHANNEL, CONN, user=USER, password=PASSWORD)

    open_opts = MQOO_OUTPUT | MQOO_INPUT_AS_Q_DEF
    try:
        q = ibmmq.Queue(qmgr, QUEUE, open_opts)  # positional open options
    except TypeError:
        # fallback: open default (output) handle
        q = ibmmq.Queue(qmgr, QUEUE)

    pmo = ibmmq.PMO()
    if args.persistent:
        # CamelCase on this build
        pmo.Persistence = MQPER_PERSISTENT

    for i in range(args.count):
        md = ibmmq.MD()  # new MD so MsgId is set by QM each put
        payload = f"msg {i+1}/{args.count} @ {time.time():.3f}"
        q.put(payload, md, pmo)  # <-- positional: data, MD, PMO
        print(f"PUT: {payload}  (MsgId={md.MsgId.hex()})")
        time.sleep(0.05)

    q.close()
    qmgr.disconnect()
    print("✅ done")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("❌", e)
        sys.exit(1)
