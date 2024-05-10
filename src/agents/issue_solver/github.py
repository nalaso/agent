from src.agents.feature import Feature
from src.agents.patcher import Patcher
from src.agents.reporter import Reporter
from src.agents.planner import Planner
from src.agents.action import Action
from src.agents.researcher import Researcher

from src.project import ProjectManager
from src.state import AgentState
from src.services import Github
from src.filesystem import ReadCode

import platform
import json

class GitHubAgent:
    def __init__(self, project_path: str, base_model: str, search_engine: str):
        self.github = Github(project_path, base_model)
        self.feature = Feature(base_model=base_model, search_engine=search_engine)
        self.action = Action(base_model=base_model)
        self.patcher = Patcher(base_model=base_model, search_engine=search_engine)
        self.reporter = Reporter(base_model=base_model)
        self.planner = Planner(base_model=base_model)
        self.researcher = Researcher(base_model=base_model)
        self.project_manager = ProjectManager()
        self.agent_state = AgentState()
        self.project_path = project_path

    def solve_github_issue(self, repo_url: str, issue_number: int, project_name: str):

        issue_title, issue_body = self.github.get_issue_details(repo_url, issue_number)
        issue = issue_title+" -> "+issue_body

        self.project_manager.add_message_from_devika(project_name, f"Solving issue #{issue_number} - {issue_title}")
        self.project_manager.add_message_from_devika(project_name, f"Issue  - {issue_body}")

        newBranch = issue_title.split(" ")[0]
        self.github.checkoutToBranch(newBranch)

        self.project_manager.add_message_from_devika(project_name, f"Checkout to branch - {newBranch}")

        os_system = platform.platform()

        plan = self.planner.execute(issue, project_name)
        plan_response = self.planner.parse_response(plan)
        plans = plan_response["plans"]
        reply = plan_response["reply"]

        self.project_manager.add_message_from_devika(project_name, reply)
        self.project_manager.add_message_from_devika(project_name, json.dumps(plans, indent=4))

        conversation = self.project_manager.get_all_messages_formatted(project_name)
        code_markdown = ReadCode(project_name).code_set_to_markdown()

        response, action = self.action.execute(conversation, project_name)
        print("\naction :: ", action, '\n')

        self.project_manager.add_message_from_devika(project_name, response)

        code = self.feature.execute(
                conversation=conversation,
                code_markdown=code_markdown,
                system_os=os_system,
                project_name=project_name
        )
        print("\nfeature code :: ", code, '\n')
        self.feature.save_code_to_project(code, project_name)

        self.project_manager.add_message_from_devika(project_name, "Issue solved successfully!")