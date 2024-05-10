import os

from src.config import Config

"""
TODO: Replace this with `code2prompt` - https://github.com/mufeedvh/code2prompt
"""

class ReadCode:
    def __init__(self, project_name: str):
        config = Config()
        project_path = config.get_projects_dir()
        self.directory_path = os.path.join(project_path, project_name.lower().replace(" ", "-"))

    def read_directory(self):
        files_list = []
        strictly_include = False
        inclded_files = ['README.md']
        excluded_dirs = ['.assets', '.github', 'benchmarks', '.git', '.idea', 'venv', 'data', 'src', 'test', 'docs', 'ui', 'images','app', 'public', 'dist', 'build', 'docs', 'examples', 'demos', 'samples', 'templates', 'tools', 'vendor', 'website', 'docs', 'images', 'public', 'samples', 'test', 'tools', 'vendor', 'website']

        for root, _dirs, files in os.walk(self.directory_path):
            for dir_name in excluded_dirs:
                if dir_name in _dirs:
                    _dirs.remove(dir_name)

            for file in files:
                if(strictly_include and file not in inclded_files): continue
                try:
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r') as file_content:
                        files_list.append({"filename": file_path, "code": file_content.read()})
                except:
                    pass
        return files_list

    def code_set_to_markdown(self):
        code_set = self.read_directory()
        markdown = ""
        for code in code_set:
            markdown += f"### {code['filename']}:\n\n"
            markdown += f"```\n{code['code']}\n```\n\n"
            markdown += "---\n\n"
        return markdown
