def is_nested_template(context):
    return bool({"template", "templates"} & set(context["cookiecutter"].keys()))


def get_relative_path(full_path_to_template, temporary_directory_root):
    """Return the path of a nested template relative to the root of a given temporary directory."""
    return full_path_to_template.split(temporary_directory_root + "/")[-1]
