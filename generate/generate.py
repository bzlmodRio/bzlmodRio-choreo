import argparse
import os

from bazelrio_gentool.clean_existing_version import clean_existing_version
from bazelrio_gentool.cli import GenericCliArgs, add_generic_cli
from bazelrio_gentool.generate_group import generate_meta_deps
from bazelrio_gentool.generate_module_project_files import (
    create_default_mandatory_settings,
    generate_module_project_files,
)
from bazelrio_gentool.manual_cleanup_helper import manual_cleanup_helper
from bazelrio_gentool.utils import TEMPLATE_BASE_DIR, render_template
from get_choreolib_dependencies import get_choreolib_dependencies


def main():
    SCRIPT_DIR = os.environ["BUILD_WORKSPACE_DIRECTORY"]
    REPO_DIR = os.path.join(SCRIPT_DIR, "..")
    output_dir = os.path.join(REPO_DIR, "libraries")

    parser = argparse.ArgumentParser()
    add_generic_cli(parser)
    parser.add_argument("--use_local_allwpilib", action="store_true")
    parser.add_argument("--use_local_opencv", action="store_true")
    parser.add_argument("--use_local_ni", action="store_true")
    args = parser.parse_args()

    group = get_choreolib_dependencies(
        use_local_allwpilib=args.use_local_allwpilib,
        use_local_opencv=args.use_local_opencv,
        use_local_ni=args.use_local_ni,
    )

    mandatory_dependencies = create_default_mandatory_settings(GenericCliArgs(args))

    clean_existing_version(REPO_DIR, force_tests=args.force_tests)
    generate_module_project_files(
        REPO_DIR,
        group,
        mandatory_dependencies=mandatory_dependencies,
        include_windows_arm_compiler=False,
    )
    generate_meta_deps(output_dir, group, force_tests=args.force_tests)

    for exe_tool in group.bundled_executable_tools:
        for child_tool in exe_tool.children_tools:
            template_base = os.path.join(
                TEMPLATE_BASE_DIR,
                "library_wrapper",
                "libraries",
                "bundled_executable_tools",
            )
            lib_dir = os.path.join(output_dir, "tools", child_tool)

            # Write BUILD file
            template_file = os.path.join(template_base, "BUILD.bazel.jinja2")
            output_file = os.path.join(lib_dir, "BUILD")
            render_template(
                template_file, output_file, target=exe_tool, child_tool=child_tool
            )

    manual_cleanup(REPO_DIR)


def manual_cleanup(repo_dir):
    manual_cleanup_helper(
        os.path.join(repo_dir, "libraries", "cpp", "choreolib-cpp", "BUILD.bazel"),
        lambda x: x.replace(
            "@bzlmodrio-choreolib//libraries", "@bzlmodrio-choreolib//private"
        ),
    )


if __name__ == "__main__":
    main()
