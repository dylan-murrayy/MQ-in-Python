import os
import time
import argparse
import sys
import ibmmq

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
QMGR     = os.getenv("MQ_QMGR", "QM1")
CHANNEL  = os.getenv("MQ_CHANNEL", "DEV.APP.SVRCONN")
CONN     = os.getenv("MQ_CONN", "localhost(1414)")
QUEUE    = os.getenv("MQ_QUEUE", "DEV.QUEUE.1")
USER     = os.getenv("MQ_USER", "app")
PASSWORD = os.getenv("MQ_PASSWORD", "apppass")


def main():
    # -------------------------------------------------------------------
    # Simple command-line options:
    #   - how many messages to send
    #   - optional base text for the message
    # -------------------------------------------------------------------
    ap = argparse.ArgumentParser(description="IBM MQ producer")
    ap.add_argument("-n", "--count", type=int, default=5, help="number of messages to send")
    ap.add_argument(
        "-m", "--message",
        default="Hello from Python!",
        help="message text to send (a counter is added automatically)",
    )
    args = ap.parse_args()

    # -------------------------------------------------------------------
    # Connect to the queue manager
    #
    # The Python library calls MQCONNX under the covers using the
    # channel & connection details you provide.
    # -------------------------------------------------------------------
    print(f"Connecting to {QMGR} via {CHANNEL}@{CONN} as {USER} …")
    qmgr = ibmmq.connect(QMGR, CHANNEL, CONN, user=USER, password=PASSWORD)

    # -------------------------------------------------------------------
    # Open the queue for PUT operations
    #
    # For this 101 example we rely on the queue's default open options,
    # which allow us to put messages.
    # -------------------------------------------------------------------
    q = ibmmq.Queue(qmgr, QUEUE)

    print(f"Putting {args.count} message(s) to {QUEUE} …")

    try:
        for i in range(1, args.count + 1):
            # -------------------------------------------------------------------
            # Build the payload.
            #
            # MQ messages are just bytes. The Python library will encode
            # this string to bytes for us using UTF-8 by default.
            # -------------------------------------------------------------------
            payload = f"{args.message} [{i}/{args.count}] @ {time.time():.3f}"

            # -------------------------------------------------------------------
            # Put the message on the queue.
            #
            # This maps to MQPUT under the covers. We are not explicitly
            # setting any MQMD or MQPMO structures here – the queue manager
            # fills in sensible defaults for a simple application message.
            # -------------------------------------------------------------------
            q.put(payload)

            print(f"PUT: {payload}")
            time.sleep(0.05)  # small delay so you can see them arrive

    finally:
        # -------------------------------------------------------------------
        # Always clean up MQ resources:
        #   - close the queue
        #   - disconnect from the queue manager
        #
        # Even for small scripts, this is the right pattern.
        # -------------------------------------------------------------------
        try: q.close()
        except Exception: pass

        try: qmgr.disconnect()
        except Exception: pass

        print("✅ producer finished")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("❌", e)
        sys.exit(1)
