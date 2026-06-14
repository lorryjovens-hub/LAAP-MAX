"""Find IM message handler method"""
import sys
sys.path.insert(0, "/opt/aris")
from lark_oapi.event.dispatcher_handler import EventDispatcherHandlerBuilder

b = EventDispatcherHandlerBuilder("", "")
methods = [m for m in dir(b) if "im_message" in m or "p2p" in m or "receive" in m or "message" in m]
print("Message-related methods:")
for m in methods:
    print(f"  {m}")
