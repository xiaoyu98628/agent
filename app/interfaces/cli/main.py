import asyncio
import sys

from app.application.chat.service import ChatService
from app.interfaces.cli.bootstrap import shutdown, startup
from app.interfaces.cli.commands import HELP_TEXT, run_turn_with_renderer
from app.interfaces.cli.render import print_banner, print_user_message
from app.interfaces.cli.session import CliSession
from app.interfaces.cli.tui import AgentTui
from config.config import config


async def run_cli(
    *,
    message: str | None,
    conversation_id: str | None,
    provider: str | None,
    model: str | None,
    stream: bool,
    plain: bool,
) -> int:
    await startup()
    try:
        session = CliSession(
            conversation_id=conversation_id,
            provider=provider,
            model=model,
            stream=stream,
        )
        chat = ChatService()

        if message:
            configure = config()
            print_banner(deployment_mode=configure.app.deployment_mode, model_label=session.model_label())
            print_user_message(message)
            await run_turn_with_renderer(message=message, session=session, chat=chat, stream=stream)
            if session.conversation_id:
                from app.interfaces.cli.render import cprint

                cprint(f"conversation_id={session.conversation_id}")
            return 0

        if plain:
            await _plain_repl(session, chat)
        else:
            tui = AgentTui(session, chat)
            await tui.run()
        return 0
    finally:
        await shutdown()


async def _plain_repl(session: CliSession, chat: ChatService) -> None:
    from app.interfaces.cli.commands import handle_slash_command

    configure = config()
    print_banner(deployment_mode=configure.app.deployment_mode, model_label=session.model_label())

    while True:
        try:
            line = input("❯ ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        text = line.strip()
        if not text:
            continue
        if text.startswith("/"):
            should_continue = await handle_slash_command(text, session)
            if not should_continue:
                break
            continue

        print_user_message(text)
        await run_turn_with_renderer(message=text, session=session, chat=chat, stream=session.stream)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(prog="agent", description="Agent personal CLI")
    parser.add_argument("-m", "--message", help="Send one message and exit")
    parser.add_argument("--conversation-id", help="Resume an existing conversation")
    parser.add_argument("--provider", help="Override LLM provider for this session")
    parser.add_argument("--model", help="Override LLM model for this session")
    parser.add_argument("--no-stream", action="store_true", help="Disable streaming output")
    parser.add_argument("--plain", action="store_true", help="Use plain readline REPL instead of TUI")
    parser.add_argument("--help-commands", action="store_true", help="Show slash commands and exit")
    args = parser.parse_args()

    if args.help_commands:
        print(HELP_TEXT.rstrip())
        raise SystemExit(0)

    code = 0
    try:
        code = asyncio.run(
            run_cli(
                message=args.message,
                conversation_id=args.conversation_id,
                provider=args.provider,
                model=args.model,
                stream=not args.no_stream,
                plain=args.plain,
            )
        )
    except KeyboardInterrupt:
        print(file=sys.stderr)
        code = 130
    raise SystemExit(code)


if __name__ == "__main__":
    main()
