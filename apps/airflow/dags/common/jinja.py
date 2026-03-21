"""
This is a class for interpolating (rendering, inserting values of variables) YAML files created using Jinja templating.
"""

from jinja2 import Template
import yaml
from airflow.providers.cncf.kubernetes.pod_generator import PodGenerator

class Jinja:
    def load_yaml(self, yaml_file_path, params):
        # Render the template YAML file. 
        # Arguments:
        # - params- Parameters with values to insert into the template. For example, if params={git: {branch: "branch_name"}},
        #       then value "{{ params.git.branch }}" in the template will be replaced with "branch_name".
        # - yaml_file_path - Path to the template YAML file we want to interpolate
        with open(yaml_file_path) as f:
            template = Template(f.read())

        rendered = template.render(params=params)

        return yaml.safe_load(rendered)


    def prepare_pod_spec(self, yaml_file_path, params):
        # Prepare a V1Pod Kubernetes model object which can be used as the full_pod_spec parameter in the KubernetesPodOperator function.
        # Arguments:
        # - params- Parameters with values to insert into the template. For example, if params={git: {branch: "branch_name"}},
        #       then value "{{ params.git.branch }}" in the template will be replaced with "branch_name".
        # - yaml_file_path - Path to the template YAML file we want to interpolate
        pod_spec_yaml = self.load_yaml(yaml_file_path, params)
        pod_spec = PodGenerator.deserialize_model_dict(pod_spec_yaml)

        return pod_spec