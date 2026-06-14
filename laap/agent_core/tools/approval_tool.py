"""ApprovalTool"""
import json
class ApprovalTool:
    def request(self,p,t=300): return json.dumps({"id":1,"p":p})
    def respond(self,i,a): return json.dumps({"id":i,"a":a})
TOOL_DEFS = []
