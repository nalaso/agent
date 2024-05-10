from src.services import Github
from src.agents.coder import Coder
from src.agents.patcher import Patcher
from src.agents.reporter import Reporter
from src.agents.planner import Planner
from src.agents.action import Action
from src.agents.researcher import Researcher
from src.project import ProjectManager
from src.state import AgentState

from src.filesystem import ReadCode

class GitHubAgent:
    def __init__(self, project_path: str, base_model: str):
        self.github = Github(project_path, base_model)
        self.coder = Coder(base_model=base_model)
        self.action = Action(base_model=base_model)
        self.patcher = Patcher(base_model=base_model, search_engine="google")
        self.reporter = Reporter(base_model=base_model)
        self.planner = Planner(base_model=base_model)
        self.researcher = Researcher(base_model=base_model)
        self.project_manager = ProjectManager()
        self.agent_state = AgentState()
        self.project_path = project_path

    def solve_github_issue(self, repo_url: str, issue_number: int, project_name: str):

        # Fetch the issue details
        issue, issue_title = self.github.get_issue_details(repo_url, issue_number)

        self.project_manager.add_message_from_devika(project_name, f"Issue  - {issue}")

        # Plan the solution
        plan = self.planner.execute(issue, project_name)
        plan_response = self.planner.parse_response(plan)

        conversation = self.project_manager.get_all_messages_formatted(project_name)
        code_markdown = ReadCode(project_name).code_set_to_markdown()

        response, action = self.action.execute(conversation, project_name)
        print("\naction :: ", action, '\n')

        self.project_manager.add_message_from_devika(project_name, response)

        # Research the solution
        research = self.researcher.execute(plan_response["plans"], [], project_name=project_name)
        queries = research["queries"]
        ask_user = research["ask_user"]

        # Implement the solution
        code = self.coder.execute(
            step_by_step_plan=plan_response["plans"],
            user_context=ask_user,
            search_results={query: self.github.search_code(repo_url, query) for query in queries},
            project_name=project_name
        )
        self.coder.save_code_to_project(code, project_name)

        # Create a pull request
        self.github.create_pull_request(issue_title)

        return "Pull request created successfully!"