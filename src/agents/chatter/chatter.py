import json
import asyncio
from src.llm import LLM
from src.services.utils import retry_wrapper
from src.browser.search import DuckDuckGoSearch, BingSearch, GoogleSearch
from src.browser import Browser
from jinja2 import Environment, BaseLoader
from src.state import AgentState
from src.project import ProjectManager
import time 
from src.agents.formatter import Formatter
from src.socket_instance import emit_agent
from src.logger import Logger

PROMPT = open("src/agents/chatter/prompt.jinja2", "r").read().strip()
IS_CHAT_PROMPT = open("src/agents/chatter/is_chat.jinja2", "r").read().strip()

class Chatter:
    def __init__(self, base_model: str):
        self.logger = Logger()
        self.llm = LLM(model_id=base_model)
        self.project_manager = ProjectManager()
    
    def render(
        self, conversation: str, code_markdown: str, prompt: str
    ) -> str:
        env = Environment(loader=BaseLoader())
        template = env.from_string(PROMPT)
        return template.render(
            conversation = conversation,
            code_markdown = code_markdown,
            prompt = prompt,
        )
    
    def render_is_chat(
        self, prompt: str
    ):
        env = Environment(loader=BaseLoader())
        template = env.from_string(IS_CHAT_PROMPT)
        return template.render(
            prompt = prompt
        )

    def validate_is_chat(self, response: str) -> bool:
        response = response.strip().replace("```json", "```")

        if response.startswith("```") and response.endswith("```"):
            response = response[3:-3].strip()

        try:
            response = json.loads(response)
        except Exception as _:
            return False

        if "start_project" not in response:
            return False
        else: 
            return response

    def is_chat(self, prompt: str, project_name: str):
        prompt = self.render_is_chat(prompt)
        response = self.llm.inference(prompt, project_name)
        valid_response = self.validate_is_chat(response)
        if not valid_response:
            return self.is_chat(prompt, project_name)
        
        if valid_response['start_project'] == "True" or valid_response['start_project'] == "true" or valid_response["start_project"] == True:
            return False
        
        return True
    
    def validate_response(self, response: str) -> bool:
        response = response.strip().replace("```json", "```")

        if response.startswith("```") and response.endswith("```"):
            response = response[3:-3].strip()

        try:
            response = json.loads(response)
        except Exception as _:
            return False

        if "reply" not in response:
            return False
        else: 
            return response

    @retry_wrapper
    def execute(self,
                prompt: str, 
                project_name: str,
                code_markdown: str):
        
        conversation = self.project_manager.get_all_messages_formatted(project_name)
        prompt = self.render(conversation, code_markdown, prompt)
        response = self.llm.inference(prompt, project_name)
        valid_response = self.validate_response(response)
        if not valid_response:
            return False
        
        print("Zuhu-1")
        print(prompt)
        new_message = self.project_manager.new_message()
        new_message['message'] = valid_response['reply']
        self.project_manager.add_message_from_devika(project_name, new_message['message'])
        
        return new_message