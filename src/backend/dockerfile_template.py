"""
Dockerfile template for conda-project deployments.
"""

DOCKERFILE_TEMPLATE = """FROM continuumio/miniconda3 as miniconda
### Install and configure miniconda
RUN conda install conda-forge::conda-project --yes && conda clean --all --yes

FROM miniconda as conda-project

COPY --from=miniconda /opt/conda /opt/conda

### Set timezone
ENV TZ=US/Central
RUN cp /usr/share/zoneinfo/${TZ} /etc/localtime \\
    && echo ${TZ} > /etc/timezone

ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1

ENV PATH=/opt/conda/bin:$PATH
ENV HOME=/project

COPY . /project
RUN chown -R 1001:1001 /project

USER 1001
WORKDIR /project
RUN ["conda", "project", "prepare", "--force"]

ENTRYPOINT ["conda", "project", "run"]
CMD []
"""


def generate_dockerfile(project_path: str, custom_commands: list = None) -> str:
    """
    Generate a Dockerfile for a conda-project.
    
    Args:
        project_path: Path to the conda-project directory
        custom_commands: Optional list of custom RUN commands to add
        
    Returns:
        Dockerfile content as string
    """
    dockerfile_content = DOCKERFILE_TEMPLATE
    
    # Add custom commands if provided
    if custom_commands:
        custom_section = "\n".join([f"RUN {cmd}" for cmd in custom_commands])
        # Insert custom commands before the final RUN conda project install
        dockerfile_content = dockerfile_content.replace(
            "RUN [\"conda\", \"project\", \"install\"]",
            f"{custom_section}\nRUN [\"conda\", \"project\", \"install\"]"
        )
    
    return dockerfile_content


def write_dockerfile(project_path: str, output_path: str = None, custom_commands: list = None) -> str:
    """
    Write a Dockerfile to the specified location.
    
    Args:
        project_path: Path to the conda-project directory
        output_path: Path where to write the Dockerfile (defaults to project_path/Dockerfile)
        custom_commands: Optional list of custom RUN commands to add
        
    Returns:
        Path to the written Dockerfile
    """
    if output_path is None:
        output_path = f"{project_path}/Dockerfile"
    
    dockerfile_content = generate_dockerfile(project_path, custom_commands)
    
    with open(output_path, 'w') as f:
        f.write(dockerfile_content)
    
    return output_path
