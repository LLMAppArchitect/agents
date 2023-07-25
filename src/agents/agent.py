# coding=utf-8
# Copyright 2023  The AIWaves Inc. team.

#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
LLM autonoumous agent
"""

from utils import *
from sop import *
from prompt import *
import time 

MAX_CHAT_HISTORY = 5

class Agent():
    def __init__(self,root:Node) -> None:
        self.content = {
            "messages":[]
            }
        self.root = root
        self.now_node = root
        self.done = False
        
    def reply(self,query):
        self.content["message"].append({"role":"user","content":query})
        now_node = self.now_node
        flag = 0
        
        "Continuous recursion"
        while True:
            chat_history_orig = self.content["messages"]
            ch_dict = self.process_history(chat_history_orig)
            # If the current node is a node that requires user feedback or a leaf node, recursion will jump out after the node ends running
            if now_node.done:
                flag =1
            
            # Extract key information to determine which node branch to enter
            if now_node.node_type =="judge":
                now_node.set_user_input(ch_dict[-1]["content"])
                
                system_prompt,last_prompt = now_node.get_prompt()
                response = get_gpt_response_rule(ch_dict,system_prompt,last_prompt)
                keywords = extract(response,now_node.extract_words)
                
                
                print("AI:" + response)
                next_nodes_nums = len(now_node.next_nodes.keys())
                for i,key in enumerate(now_node.next_nodes):
                    if i == next_nodes_nums-1:
                        now_node = now_node.next_nodes[key]
                    elif key == keywords:
                        now_node = now_node.next_nodes[key]
                        break
                
            # Extract keywords to proceed to the next node
            elif now_node.node_type == "extract":
                now_node.set_user_input(ch_dict[-1]["content"])
                system_prompt,last_prompt = now_node.get_prompt()
                response = get_gpt_response_rule(ch_dict,system_prompt,last_prompt)
                print("AI:" + response)
                keywords = extract(response,now_node.extract_words)
                now_node = now_node.next_nodes[0]
                
            
            
            elif now_node.node_type == "response":
                now_node.set_user_input(ch_dict[-1]["content"])
                system_prompt,last_prompt = now_node.get_prompt()
                response = get_gpt_response_rule(ch_dict,system_prompt,last_prompt)
                response = extract(response,now_node.extract_words)
                print("AI:" + response)
                self.answer(response)
                chat_history_orig = self.content["messages"]
                ch_dict = self.process_history(chat_history_orig)
                now_node = now_node.next_nodes[0]
                self.now_node = now_node
                return response
                
                
            if flag or now_node == self.root:
                break

    def process_history(self,chat_history):
        """Dealing with incoming data in different situations

        Args:
            chat_history (_type_): input chat history

        Returns:
            list: history of gpt usage
        """
        ch_dict = []
        for ch in chat_history:
            if ch["role"]=="user":
                ch_dict.append(  {"role": "user", "content": ch["content"]})
            else:
                ch_dict.append(  {"role": "assistant", "content": ch["content"]})
        
        if len(ch_dict)>2*MAX_CHAT_HISTORY:
            ch_dict = ch_dict[-(2*MAX_CHAT_HISTORY+1):]
        return ch_dict
    
    def is_done(self,node:Node):
        return node.done