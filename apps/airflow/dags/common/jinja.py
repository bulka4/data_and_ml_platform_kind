"""
This is a class for interpolating (rendering, inserting values of variables) YAML files created using Jinja templating.
"""

from jinja2 import Template
import yaml
from airflow.providers.cncf.kubernetes.pod_generator import PodGenerator

class Jinja:
    def render(self, params, yaml_file_path):
        # Render the template YAML file. 
        # Arguments:
        # - params- Parameters with values to insert into the template. For example, if params={git: {branch: "branch_name"}},
        #       then value "{{ params.git.branch }}" in the template will be replaced with "branch_name".
        # - yaml_file_path - Path to the template YAML file we want to interpolate
        with open(yaml_file_path) as f:
            template = Template(f.read())

        rendered = template.render(params=params)

        return rendered


    def prepare_pod_spec(self, params, yaml_file_path):
        # Prepare a V1Pod Kubernetes model object which can be used as the full_pod_spec parameter in the KubernetesPodOperator function.
        # Arguments:
        # - params- Parameters with values to insert into the template. For example, if params={git: {branch: "branch_name"}},
        #       then value "{{ params.git.branch }}" in the template will be replaced with "branch_name".
        # - yaml_file_path - Path to the template YAML file we want to interpolate
        rendered_yaml = self.render(params, yaml_file_path)
        pod_spec = PodGenerator.deserialize_model_dict(yaml.safe_load(rendered_yaml))

        return pod_spec