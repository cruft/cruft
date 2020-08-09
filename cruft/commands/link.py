from pathlib import Path

from examples import example

from cruft.commands._utils import (
    RobustTemporaryDirectory,
    generate_cookiecutter_context,
    get_cookiecutter_repo,
    get_cruft_file,
    json_dumps,
)


@example("https://github.com/timothycrosley/cookiecutter-python/", no_input=True, use_latest=True)
def link(
    template_git_url: str,
    project_dir: str = ".",
    use_latest: bool = False,
    no_input: bool = False,
    config_file: str = None,
    default_config: bool = False,
    extra_context: dict = None,
    directory: str = "",
) -> bool:
    """Links an existing project created from a template, to the template it was created from."""
    project_dir_path = Path(project_dir)
    cruft_file = get_cruft_file(project_dir_path, exists=False)

    with RobustTemporaryDirectory() as cookiecutter_template_dir_str:
        cookiecutter_template_dir = Path(cookiecutter_template_dir_str)
        repo = get_cookiecutter_repo(template_git_url, cookiecutter_template_dir)
        last_commit = repo.head.object.hexsha

        if directory:
            cookiecutter_template_dir = cookiecutter_template_dir / directory

        context = generate_cookiecutter_context(
            template_git_url,
            cookiecutter_template_dir,
            config_file,
            default_config,
            extra_context,
            no_input,
        )

        if use_latest or no_input:
            use_commit = last_commit
        else:  # pragma: no cover
            print("")
            print(f"The latest commit to the template is {last_commit}")
            print("Press enter to link against this commit or provide an alternative commit.")
            print("")
            use_commit = input(f"Link to template at commit [{last_commit}]: ")  # nosec
            use_commit = use_commit if use_commit.strip() else last_commit

        cruft_file.write_text(
            json_dumps(
                {
                    "template": template_git_url,
                    "commit": use_commit,
                    "context": context,
                    "directory": directory,
                }
            )
        )

    return True
