def clean_context(context):
    cleaned_context = context
    keys_to_remove = ["_output_dir", "_repo_dir"]

    for key in keys_to_remove:
        if key in cleaned_context["cookiecutter"]:
            del cleaned_context["cookiecutter"][key]

    return cleaned_context
