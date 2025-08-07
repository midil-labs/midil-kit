from pathlib import Path
from midil.cli.core.scaffolds.base import ProjectScaffolder
from midil.cli.core.scaffolds.project import FastAPIServiceScaffolder
from midil.cli.core.scaffolds.lambda_function import LambdaFunctionScaffolder

_ALLOW_USER_INPUT = True


class ProjectScaffolderFactory:
    """
    Factory class to create project scaffolders based on project type.
    """

    @staticmethod
    def create(project_type: str = "fastapi") -> "ProjectScaffolder":
        template_base = Path(__file__).parent.parent / "templates"
        if project_type == "fastapi":
            template_path = template_base / "cookiecutter-midil-project"
            return FastAPIServiceScaffolder(
                template_path, allow_user_input=_ALLOW_USER_INPUT
            )
        elif project_type == "lambda":
            template_path = template_base / "cookiecutter-midil-lambda"
            return LambdaFunctionScaffolder(
                template_path, allow_user_input=_ALLOW_USER_INPUT
            )
        else:
            raise ValueError(f"Unknown project type: {project_type}")


def scaffold_project(name: str, project_type: str = "fastapi") -> None:
    """
    Facade function to scaffold a new MIDIL project using the appropriate scaffolder.
    """
    scaffolder = ProjectScaffolderFactory.create(project_type)
    scaffolder.scaffold(name)
