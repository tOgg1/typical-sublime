import json
import os

import sublime
import sublime_plugin
import subprocess


class TypicalCommand(sublime_plugin.TextCommand):
    def run(self, edit, current_directory=False):

        if current_directory:
            self.run_in_current_directory()
        else:
            self.get_directory_and_run()

    def get_directory_and_run(self):
        cwd = os.path.dirname(self.view.file_name())
        self.view.window().show_input_panel(
            "Directory to run in:",
            cwd,
            on_done=lambda name: self.run_in_directory(name),
            on_change=None,
            on_cancel=None
        )

    def run_in_directory(self, directory):
        recipes = str(subprocess.check_output(['typical', '--list'])) \
                      .split("\\n")[1:-1]
        recipes = list(map(lambda x: x.replace(' + ', ''), recipes))

        def on_select(selection):
            selected_recipe = recipes[selection]
            typical_recipe_config = str(subprocess.check_output(
                ['typical', '-p', recipes[selection]],
                universal_newlines=True
            ))

            typical_recipe_config = json.loads(
                typical_recipe_config,
                encoding='utf-8'
            )

            interpolations = typical_recipe_config.get('__interpolations__', [])
            resolved = []

            def show_input(interpolations, resolved_so_far=0):
                interpolation = interpolations[resolved_so_far]
                caption = ""
                name = interpolation.get('name', interpolation)
                if isinstance(interpolation, dict):
                    caption = interpolation.get('description', interpolation.get('name'))
                elif isinstance(interpolation, str):
                    caption = interpolation

                self.view.window().show_input_panel(
                    caption,
                    '',
                    on_done=lambda line: on_resolve(name, line, interpolations, resolved_so_far),
                    on_change=None,
                    on_cancel=on_cancel
                )

            def on_resolve(name, line, interpolations, resolved_so_far):
                resolved.append([name, line])
                if resolved_so_far+1 == len(interpolations):
                    self.call_typical(selected_recipe, directory, resolved)
                else:
                    show_input(interpolations, resolved_so_far+1)

            def on_cancel():
                return

            if len(interpolations) == 0:
                self.call_typical(selected_recipe, directory, resolved)
            else:
                show_input(interpolations, 0)

        self.view.window().show_quick_panel(recipes, on_select)

    def run_in_current_directory(self):
        self.run_in_directory(os.path.dirname(self.view.file_name()))

    def call_typical(self, recipe, cwd, resolved_interpolations=[]):
        command = [
            'typical',
            '-o',
            cwd,
        ]
        for interpolation in resolved_interpolations:
            command += ['-i'] + [interpolation[0] + '=' + interpolation[1]]

        command += [recipe]
        subprocess.call(command)
