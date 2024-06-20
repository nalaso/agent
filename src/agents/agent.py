from .planner import Planner
from .researcher import Researcher
from .formatter import Formatter
from .coder import Coder
from .action import Action
from .internal_monologue import InternalMonologue
from .answer import Answer
from .runner import Runner
from .feature import Feature
from .patcher import Patcher
from .reporter import Reporter
from .decision import Decision
from .issue_solver import GitHubAgent
from .chatter import Chatter
from src.project import ProjectManager
from src.state import AgentState
from src.logger import Logger

from src.bert.sentence import SentenceBert
from src.memory import KnowledgeBase
from src.browser.search import BingSearch, GoogleSearch, DuckDuckGoSearch
from src.browser import Browser
from src.browser import start_interaction
from src.filesystem import ReadCode
from src.services import Netlify, Github
from src.documenter.pdf import PDF

import json
import time
import platform
import tiktoken
import asyncio

from src.socket_instance import emit_agent


class Agent:
    def __init__(self, base_model: str, search_engine: str):
        if not base_model:
            raise ValueError("base_model is required")

        self.logger = Logger()

        """
        Accumulate contextual keywords from chained prompts of all preparation agents
        """
        self.collected_context_keywords = []

        """
        Agents
        """
        self.base_model = base_model
        self.planner = Planner(base_model=base_model)
        self.researcher = Researcher(base_model=base_model)
        self.formatter = Formatter(base_model=base_model)
        self.coder = Coder(base_model=base_model)
        self.action = Action(base_model=base_model)
        self.internal_monologue = InternalMonologue(base_model=base_model)
        self.answer = Answer(base_model=base_model)
        self.runner = Runner(base_model=base_model, search_engine=search_engine)
        self.feature = Feature(base_model=base_model,search_engine=search_engine)
        self.patcher = Patcher(base_model=base_model, search_engine=search_engine)
        self.reporter = Reporter(base_model=base_model)
        self.decision = Decision(base_model=base_model)
        self.chatter = Chatter(base_model=base_model)
        self.git = None

        self.project_manager = ProjectManager()
        self.agent_state = AgentState()
        self.engine = search_engine
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def is_chat(self, prompt: str, project_name: str) -> bool:
        """
        Check if the prompt is a chat message
        """
        self.agent_state.set_agent_active(project_name, True)
        return self.chatter.is_chat(prompt, project_name)
    
    def chat(self, prompt: str, project_name: str):
        """
        Chat with the user
        """
        new_message = self.project_manager.new_message()
        new_message['message'] = prompt
        new_message['from_devika'] = False
        self.project_manager.add_message_from_user(project_name, new_message['message'])
        code_markdown = ""
        self.chatter.execute(prompt, project_name, code_markdown)
        self.agent_state.set_agent_active(project_name, False)

    async def open_page(self, project_name, url):
        browser = await Browser().start()

        await browser.go_to(url)
        _, raw = await browser.screenshot(project_name)
        data = await browser.extract_text()
        await browser.close()

        return browser, raw, data

    def search_queries(self, queries: list, project_name: str) -> dict:
        results = {}

        knowledge_base = KnowledgeBase()

        if self.engine == "bing":
            web_search = BingSearch()
        elif self.engine == "google":
            web_search = GoogleSearch()
        else:
            web_search = DuckDuckGoSearch()

        self.logger.info(f"\nSearch Engine :: {self.engine}")

        for query in queries:
            query = query.strip().lower()

            # knowledge = knowledge_base.get_knowledge(tag=query)
            # if knowledge:
            #     results[query] = knowledge
            #     continue

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            web_search.search(query)

            link = web_search.get_first_link()
            print("\nLink :: ", link, '\n')
            if not link:
                continue
            browser, raw, data = loop.run_until_complete(self.open_page(project_name, link))
            emit_agent("screenshot", {"data": raw, "project_name": project_name}, False)
            results[query] = self.formatter.execute(data, project_name)

            self.logger.info(f"got the search results for : {query}")
            # knowledge_base.add_knowledge(tag=query, contents=results[query])
        return results

    def update_contextual_keywords(self, sentence: str):
        """
            Update the context keywords with the latest sentence/prompt
        """
        keywords = SentenceBert(sentence).extract_keywords()
        for keyword in keywords:
            self.collected_context_keywords.append(keyword[0])

        return self.collected_context_keywords

    def make_decision(self, prompt: str, project_name: str) -> str:
        decision = self.decision.execute(prompt, project_name)

        for item in decision:
            function = item["function"]
            args = item["args"]
            reply = item["reply"]

            self.project_manager.add_message_from_devika(project_name, reply)

            if function == "git_clone":
                url = args["url"]
                # Implement git clone functionality here

            elif function == "generate_pdf_document":
                user_prompt = args["user_prompt"]
                # Call the reporter agent to generate the PDF document
                markdown = self.reporter.execute([user_prompt], "", project_name)
                _out_pdf_file = PDF().markdown_to_pdf(markdown, project_name)

                project_name_space_url = project_name.replace(" ", "%20")
                pdf_download_url = "http://127.0.0.1:1337/api/download-project-pdf?project_name={}".format(
                    project_name_space_url)
                response = f"I have generated the PDF document. You can download it from here: {pdf_download_url}"

                #asyncio.run(self.open_page(project_name, pdf_download_url))

                self.project_manager.add_message_from_devika(project_name, response)

            elif function == "browser_interaction":
                user_prompt = args["user_prompt"]
                # Call the interaction agent to interact with the browser
                start_interaction(self.base_model, user_prompt, project_name)

            elif function == "coding_project":
                user_prompt = args["user_prompt"]
                # Call the planner, researcher, coder agents in sequence
                plan = self.planner.execute(user_prompt, project_name)
                planner_response = self.planner.parse_response(plan)

                research = self.researcher.execute(plan, self.collected_context_keywords, project_name)
                search_results = self.search_queries(research["queries"], project_name)

                code = self.coder.execute(
                    step_by_step_plan=plan,
                    user_context=research["ask_user"],
                    search_results=search_results,
                    project_name=project_name
                )
                self.coder.save_code_to_project(code, project_name)

    def subsequent_execute(self, prompt: str, project_name: str):
        """
        Subsequent flow of execution
        """
        new_message = self.project_manager.new_message()
        new_message['message'] = prompt
        new_message['from_devika'] = False
        self.project_manager.add_message_from_user(project_name, new_message['message'])

        os_system = platform.platform()

        self.agent_state.set_agent_active(project_name, True)

        conversation = self.project_manager.get_all_messages_formatted(project_name)
        code_markdown = ReadCode(project_name).code_set_to_markdown()

        response, action = self.action.execute(conversation, project_name)

        self.project_manager.add_message_from_devika(project_name, response)

        print("\naction :: ", action, '\n')

        if action == "answer":
            response = self.answer.execute(
                conversation=conversation,
                code_markdown=code_markdown,
                project_name=project_name
            )
            self.project_manager.add_message_from_devika(project_name, response)

        elif action == "run":
            project_path = self.project_manager.get_project_path(project_name)
            self.runner.execute(
                conversation=conversation,
                code_markdown=code_markdown,
                os_system=os_system,
                project_path=project_path,
                project_name=project_name
            )

        elif action == "deploy":
            deploy_metadata = Netlify().deploy(project_name)
            deploy_url = deploy_metadata["deploy_url"]

            response = {
                "message": "Done! I deployed your project on Netlify.",
                "deploy_url": deploy_url
            }
            response = json.dumps(response, indent=4)

            self.project_manager.add_message_from_devika(project_name, response)

        elif action == "feature":
            code = self.feature.execute(
                conversation=conversation,
                code_markdown=code_markdown,
                system_os=os_system,
                project_name=project_name
            )
            print("\nfeature code :: ", code, '\n')
            self.feature.save_code_to_project(code, project_name)

        elif action == "bug":
            code = self.patcher.execute(
                conversation=conversation,
                code_markdown=code_markdown,
                commands=None,
                error=prompt,
                error_context=None,
                system_os=os_system,
                project_name=project_name
            )
            print("\nbug code :: ", code, '\n')
            self.patcher.save_code_to_project(code, project_name)

        elif action == "report":
            markdown = self.reporter.execute(conversation, code_markdown, project_name)

            _out_pdf_file = PDF().markdown_to_pdf(markdown, project_name)

            project_name_space_url = project_name.replace(" ", "%20")
            pdf_download_url = "http://127.0.0.1:1337/api/download-project-pdf?project_name={}".format(
                project_name_space_url)
            response = f"I have generated the PDF document. You can download it from here: {pdf_download_url}"

            #asyncio.run(self.open_page(project_name, pdf_download_url))

            self.project_manager.add_message_from_devika(project_name, response)
        
        elif action == "repo_init":
            project_path = self.project_manager.get_project_path(project_name)
            if self.git == None:
                self.git = Github(project_path, self.base_model)

        elif action == "repo_commit":
            project_path = self.project_manager.get_project_path(project_name)
            if self.git == None:
                self.git = Github(project_path, self.base_model)

            commit_message = self.git.generate_commit_message(project_name, conversation,code_markdown)
            self.git.commit(commit_message)

        elif action == "reset_code":
            project_path = self.project_manager.get_project_path(project_name)
            if self.git == None:
                self.git = Github(project_path, self.base_model)

            self.git.reset_to_previous_commit()

        elif action == "start_auto_commit":
            self.project_manager.start_auto_commit(project_name)

        elif action == "stop_auto_commit":
            self.project_manager.stop_auto_commit(project_name)

        self.agent_state.set_agent_active(project_name, False)
        if self.project_manager.get_auto_commit(project_name):
            print("\n Committing the code\n")
            project_path = self.project_manager.get_project_path(project_name)
            if self.git == None:
                self.git = Github(project_path, self.base_model)

            commit_message = self.git.generate_commit_message(project_name, conversation,code_markdown)
            self.git.commit(commit_message)
        self.agent_state.set_agent_completed(project_name, True)

    def execute(self, prompt: str, project_name: str) -> str:
        """
        Agentic flow of execution
        """
        if project_name:
            self.project_manager.add_message_from_user(project_name, prompt)

        self.agent_state.create_state(project=project_name)
        self.agent_state.set_subsequent_execute(project = project_name, subsequent_execute=True)

        plan = self.planner.execute(prompt, project_name)
        print("\nplan :: ", plan, '\n')

        planner_response = self.planner.parse_response(plan)
        reply = planner_response["reply"]
        focus = planner_response["focus"]
        plans = planner_response["plans"]
        summary = planner_response["summary"]
        conversation = self.project_manager.get_all_messages_formatted(project_name)
        code_markdown = ReadCode(project_name).code_set_to_markdown()

        self.project_manager.add_message_from_devika(project_name, reply)
        self.project_manager.add_message_from_devika(project_name, json.dumps(plans, indent=4))
        # self.project_manager.add_message_from_devika(project_name, f"In summary: {summary}")

        self.update_contextual_keywords(focus)
        print("\ncontext_keywords :: ", self.collected_context_keywords, '\n')

        internal_monologue = self.internal_monologue.execute(current_prompt=plan, project_name=project_name)
        print("\ninternal_monologue :: ", internal_monologue, '\n')

        new_state = self.agent_state.new_state()
        new_state["internal_monologue"] = internal_monologue
        new_state["subsequent_execute"] = True
        self.agent_state.add_to_current_state(project_name, new_state)

        research = self.researcher.execute(plan, self.collected_context_keywords, project_name=project_name)
        print("\nresearch :: ", research, '\n')

        queries = research["queries"]
        queries_combined = ", ".join(queries)
        ask_user = research["ask_user"]

        if (queries and len(queries) > 0) or ask_user != "":
            self.project_manager.add_message_from_devika(
                project_name,
                f"I am browsing the web to research the following queries: {queries_combined}."
                f"\n If I need anything, I will make sure to ask you."
            )
        if not queries and len(queries) == 0:
            self.project_manager.add_message_from_devika(
                project_name,
                "I think I can proceed without searching the web."
            )

        ask_user_prompt = "Nothing from the user."

        if ask_user != "" and ask_user is not None:
            self.project_manager.add_message_from_devika(project_name, ask_user)
            self.agent_state.set_agent_active(project_name, False)
            got_user_query = False

            while not got_user_query:
                self.logger.info("Waiting for user query...")

                latest_message_from_user = self.project_manager.get_latest_message_from_user(project_name)
                validate_last_message_is_from_user = self.project_manager.validate_last_message_is_from_user(
                    project_name)

                if latest_message_from_user and validate_last_message_is_from_user:
                    ask_user_prompt = latest_message_from_user["message"]
                    got_user_query = True
                    self.project_manager.add_message_from_devika(project_name, "Thanks! 🙌")
                time.sleep(5)

        self.agent_state.set_agent_active(project_name, True)

        if queries and len(queries) > 0:
            search_results = self.search_queries(queries, project_name)

        else:
            search_results = {}

        code = self.coder.execute(
            step_by_step_plan=plan,
            user_context=ask_user_prompt,
            search_results=search_results,
            project_name=project_name
        )
        print("\ncode :: ", code, '\n')

        self.coder.save_code_to_project(code, project_name)

        self.agent_state.set_agent_active(project_name, False)
        if self.project_manager.get_auto_commit(project_name):
            project_path = self.project_manager.get_project_path(project_name)
            if self.git == None:
                self.git = Github(project_path, self.base_model)

            commit_message = self.git.generate_commit_message(project_name, conversation,code_markdown)
            self.git.commit(commit_message)
            
        self.agent_state.set_agent_completed(project_name, True)
        self.project_manager.add_message_from_devika(
            project_name,
            "I have completed the my task. \n"
            "if you would like me to do anything else, please let me know. \n"
        )

    def solve_github_issue(self, prompt: str, project_name: str):
        if project_name:
            self.project_manager.add_message_from_user(project_name, prompt)

        self.agent_state.create_state(project=project_name)
        self.agent_state.set_agent_active(project_name, True)

        github_repo_url = next((part for part in prompt.split() if 'github.com' in part), None)

        if github_repo_url:
            repo_url = '/'.join(github_repo_url.split('/')[:5])
        else:
            self.project_manager.add_message_from_devika(project_name, f"Repo not found.")
            return

        issue_number = prompt.split(" ")[1].split("/")[-1]

        plan = self.planner.execute(prompt, project_name)
        print("\nplan :: ", plan, '\n')

        planner_response = self.planner.parse_response(plan)
        reply = planner_response["reply"]
        plans = planner_response["plans"]

        self.project_manager.add_message_from_devika(project_name, reply)
        self.project_manager.add_message_from_devika(project_name, json.dumps(plans, indent=4))

        internal_monologue = self.internal_monologue.execute(current_prompt=plan, project_name=project_name)
        print("\ninternal_monologue :: ", internal_monologue, '\n')

        new_state = self.agent_state.new_state()
        new_state["internal_monologue"] = internal_monologue
        self.agent_state.add_to_current_state(project_name, new_state)

        project_path = self.project_manager.get_project_path(project_name)
        Github.clone(repo_url, project_path)

        self.project_manager.add_message_from_devika(project_name, "Cloned the repo successfully!")
        emit_agent("task", {"data": "fetch_files", "project_name": project_name}, False)

        github_agent = GitHubAgent(project_path, base_model=self.base_model, search_engine=self.engine)
        github_agent.solve_github_issue(repo_url, issue_number, project_name)

        conversation = self.project_manager.get_all_messages_formatted(project_name)
        code_markdown = ReadCode(project_name).code_set_to_markdown()

        if self.git == None:
            self.git = Github(project_path, self.base_model)

        # TODO implement commit message generation for large file difference
        # commit_message = self.git.generate_commit_message(project_name, conversation, code_markdown)
        self.project_manager.add_message_from_devika(project_name, "Committing the changes")
        self.git.commit(f"solve #{issue_number}")

        new_state = self.agent_state.new_state()
        new_state["internal_monologue"] = "Pushing the changes to remote."
        self.agent_state.add_to_current_state(project_name, new_state)

        self.git.push_to_remote()
        self.project_manager.add_message_from_devika(project_name, "Pushed the changes to remote.")

        self.agent_state.set_agent_active(project_name, False)
        self.agent_state.set_agent_completed(project_name, True)