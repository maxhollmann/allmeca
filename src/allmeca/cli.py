import click
from pathlib import Path

from allmeca.bot import MainBot
from allmeca.processors.human import HumanProcessor
from allmeca.processors.auto import AutoProcessor
from allmeca import environments
from allmeca.prompts import load_prompt_set
from allmeca.messages import NullPersistence, FilePersistence
from allmeca import ui
from allmeca.run_context import RunContext


@click.command()
@click.option("-m", "--model", default="gpt-3.5-turbo")
@click.option("-p", "--prompt-set", default="default")
@click.option("-h", "--history-path", default=None)
@click.option("-w", "--work-dir", type=Path, default=Path.cwd())
@click.option("-t", "--task-file", type=click.File("r"), default=None)
@click.option("-g", "--git", is_flag=True, default=False)
@click.argument("task", nargs=-1)
def main(model, prompt_set, task, task_file, history_path, work_dir, git):
    if task_file is not None:
        task = task_file.read()
        task_file.close()
    elif len(task) == 0:
        task = ui.prompt_line("How can I help you?")
    else:
        task = " ".join(task)

    if history_path is None:
        persistence = NullPersistence()
    else:
        persistence = FilePersistence(history_path)

    environment = environments.LocalEnvironment(work_dir=work_dir)
    processor = AutoProcessor(environment=environment)
    prompt_set = load_prompt_set(prompt_set)

    bot = MainBot(
        processor=processor,
        model=model,
        prompt_set=prompt_set,
        persistence=persistence,
    )

    context = RunContext(
        main_bot=bot,
        environment=environment,
        processor=processor,
    )
    context.inject_self()

    if git:
        from allmeca.callbacks.handlers.git_committer import GitCommitter

        context.callbacks.register(GitCommitter(work_dir))

    context.callbacks.emit("before_run_start")
    bot.run(task)
    context.callbacks.emit("run_complete")


if __name__ == "__main__":
    main()
