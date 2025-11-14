#!/usr/bin/env python3
import os
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
    # Connect to the queue manager
    #
    # The Python library calls MQCONNX under the covers using the
    # channel & connection details you provide.
    # -------------------------------------------------------------------

    print(f"Connecting to {QMGR} via {CHANNEL}@{CONN} as {USER} …")
    qmgr = ibmmq.connect(QMGR, CHANNEL, CONN, user=USER, password=PASSWORD)

    # -------------------------------------------------------------------
    # Open the queue for GET operations
    #
    # Because this is a 101 example, we don't specify any special
    # options. MQ will use the queue's default behaviour.
    # -------------------------------------------------------------------

    q = ibmmq.Queue(qmgr, QUEUE)

    print(f"Waiting for messages on {QUEUE}. Will stop when the queue is empty.")
    count = 0

    try:
        while True:
            try:
            # -------------------------------------------------------------------
            # Get a message from the queue.
            #
            # By default, this is a *blocking* call. If a message is available,
            # MQ returns it immediately. If the queue is empty, MQ raises
            # Reason 2033 (MQRC_NO_MSG_AVAILABLE).
            # -------------------------------------------------------------------
                msg = q.get()
            except ibmmq.MQMIError as e:
                # 2033 = "no more messages available right now"
                if e.reason == 2033:
                    break
                raise # anything else is a real error

            count += 1
            text = msg.decode("utf-8", errors="replace")
            print(f"[{count}] {text}")

    finally:

        # -------------------------------------------------------------------
        # Always clean up MQ resources:
        #   - close the queue
        #   - disconnect from the queue manager
        #
        # MQ apps should always do this, even for simple scripts.
        # -------------------------------------------------------------------
        try: q.close()
        except Exception: pass
        try: qmgr.disconnect()
        except Exception: pass
        print("✅ consumer stopped")

if __name__ == "__main__":
    main()
