import os

from jinja2 import Template
import argparse
import yaml
import subprocess
from typing import List


class DlpcProject:
    name: str
    path: str
    deps: List[str]

    def __init__(self, name, path, deps):
        self.name = name
        self.path = path
        self.deps = deps


def run(destination_folder: str):
    diff = subprocess.Popen(['git', 'diff', 'origin/master', '--name-only'],
                            stdout=subprocess.PIPE).stdout.read().decode()
    diff = diff.split('\n')
    changed_projects = [path.split('/') for path in diff
                        if path.startswith('projects/') or path.startswith('libs/')]
    changed_projects = {f'{path[0]}/{path[1]}' for path in changed_projects}
    with open('projects_config.yml') as f:
        config = yaml.safe_load(f.read())
    projects = []
    projects_config = config['services']
    is_master_pipeline = os.environ['CI_COMMIT_REF_NAME'] == 'master'
    # if not is_master_pipeline:
    projects_config.update(config['libs'])
    for p in projects_config:
        project = DlpcProject(p, projects_config[p]['path'], projects_config[p]['deps'])
        if is_master_pipeline or project.path in changed_projects or \
                [dep for dep in project.deps if projects_config[dep]['path'] in changed_projects]:
            projects.append(project)
    with open('project_job_template.j2') as template_file:
        with open(f'{destination_folder}/generated_ci.yml', 'w') as generated_file:
            template = Template(template_file.read())
            generated_file.write(template.render(projects=projects))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('dest')
    args = parser.parse_args()
    run(args.dest)