#!/usr/bin/env python3
import os, sys, argparse, time
import ibmmq

QMGR    = os.getenv("MQ_QMGR", "QM1")
CHANNEL = os.getenv("MQ_CHANNEL", "DEV.APP.SVRCONN")
CONN    = os.getenv("MQ_CONN", "localhost(1414)")
QUEUE   = os.getenv("MQ_QUEUE", "DEV.QUEUE.1")
USER    = os.getenv("MQ_USER", "app")
PASSWORD= os.getenv("MQ_PASSWORD", "apppass")

try:
    from ibmmq.constants import MQC
except Exception:
    MQC = getattr(ibmmq, "MQC", None)

def mqc_val(name, fallback):
    return getattr(MQC, name, fallback) if MQC else fallback

MQOO_INPUT_AS_Q_DEF   = mqc_val("MQOO_INPUT_AS_Q_DEF",   0x00000001)
MQGMO_WAIT            = mqc_val("MQGMO_WAIT",            0x00000001)
MQRC_NO_MSG_AVAILABLE = mqc_val("MQRC_NO_MSG_AVAILABLE", 2033)

def main():
    ap = argparse.ArgumentParser(description="IBM MQ consumer")
    ap.add_argument("-t", "--timeout-ms", type=int, default=5000, help="wait time per get (ms)")
    ap.add_argument("-m", "--max", type=int, default=0, help="max messages to consume (0 = infinite)")
    args = ap.parse_args()

    print(f"Connecting to {QMGR} via {CHANNEL}@{CONN} as {USER} …")
    qmgr = ibmmq.connect(QMGR, CHANNEL, CONN, user=USER, password=PASSWORD)

    q   = ibmmq.Queue(qmgr, QUEUE, MQOO_INPUT_AS_Q_DEF)
    gmo = ibmmq.GMO(Options=MQGMO_WAIT, WaitInterval=args.timeout_ms)

    count = 0
    print(f"Waiting for messages on {QUEUE} (timeout {args.timeout_ms} ms). Ctrl+C to stop.")
    try:
        while True:
            md = ibmmq.MD()
            try:
                # Try most common signature first
                m = q.get(md, gmo)
            except TypeError:
                try:
                    # Some builds want GMO first
                    m = q.get(gmo, md)
                except TypeError:
                    # Fallback: no-arg GET; emulate waited behaviour with a short sleep loop
                    try:
                        m = q.get()   # NOWAIT by default; will raise 2033 if empty
                    except Exception as e:
                        reason = getattr(e, "Reason", None)
                        if reason == MQRC_NO_MSG_AVAILABLE or "2033" in str(e):
                            time.sleep(min(max(args.timeout_ms / 1000.0, 0.1), 5.0))
                            continue
                        raise

            count += 1
            try:
                text = m.decode("utf-8")
            except Exception:
                text = repr(m)
            # md.MsgId only reliable if the MD was actually used; handle gracefully
            msgid = getattr(md, "MsgId", b"")
            print(f"GET #{count}: {text}  (MsgId={getattr(msgid, 'hex', lambda: '')()})")
            if args.max and count >= args.max:
                break
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        try: q.close()
        except Exception: pass
        try: qmgr.disconnect()
        except Exception: pass
        print("✅ consumer stopped")

if __name__ == "__main__":
    main()
