from app.application.chat.service import ChatService
from app.domain.exceptions import DomainError
from app.infrastructure.llm.catalog import list_model_options
from app.infrastructure.tools.registry import describe_agent_tools
from app.interfaces.cli.render import StreamRenderer, cprint, print_assistant_plain
from app.interfaces.cli.session import CliSession
from config.config import config


HELP_TEXT = """\
Commands:
  /help, /h              Show this help
  /exit, /quit, /q       Exit CLI
  /new                   Start a new conversation
  /conv                  Show current conversation id
  /model                 Show current model override
  /model <provider> <model>   Set model for this session
  /tools                 List enabled agent tools
  /models                List available models from catalog
"""


async def handle_slash_command(line: str, session: CliSession) -> bool:
    """Handle slash command. Returns False to exit REPL."""
    parts = line.strip().split()
    cmd = parts[0].lower()

    match cmd:
        case "/help" | "/h" | "/?":
            cprint(HELP_TEXT.rstrip())
        case "/exit" | "/quit" | "/q":
            return False
        case "/new":
            session.conversation_id = None
            cprint("Started new conversation.")
        case "/conv":
            cprint(session.conversation_id or "(none yet)")
        case "/model":
            if len(parts) >= 3:
                session.provider = parts[1].strip().lower()
                session.model = parts[2].strip()
                cprint(f"Model override: {session.model_label()}")
            else:
                cprint(f"Model: {session.model_label()}")
        case "/tools":
            payload = describe_agent_tools(config())
            cprint(f"policy={payload['policy']} workspace={payload['workspace_dir']}")
            for tool in payload["tools"]:
                desc = tool["description"].split("\n")[0] if tool["description"] else ""
                cprint(f"  · {tool['name']}: {desc}")
        case "/models":
            payload = list_model_options()
            default = payload["default"]
            cprint(f"default: {default['provider']}:{default['model']}")
            for entry in payload["models"]:
                cprint(f"  · {entry.provider}:{entry.model}  {entry.label}")
        case _:
            cprint(f"Unknown command: {cmd}. Type /help for commands.")
    return True


async def run_turn_with_renderer(
    *,
    message: str,
    session: CliSession,
    chat: ChatService,
    stream: bool,
) -> None:
    try:
        if stream:
            await _stream_turn(message=message, session=session, chat=chat)
        else:
            await _blocking_turn(message=message, session=session, chat=chat)
    except DomainError as exc:
        cprint(f"\nError: {exc}")
    except Exception as exc:
        cprint(f"\nError: {exc}")


async def run_turn(
    *,
    message: str,
    session: CliSession,
    chat: ChatService,
) -> None:
    await run_turn_with_renderer(
        message=message,
        session=session,
        chat=chat,
        stream=session.stream,
    )


async def _blocking_turn(*, message: str, session: CliSession, chat: ChatService) -> None:
    result = await chat.send_message(
        message=message,
        conversation_id=session.conversation_id,
        provider=session.provider,
        model=session.model,
    )
    session.conversation_id = result.conversation_id
    print_assistant_plain(result.reply)


async def _stream_turn(*, message: str, session: CliSession, chat: ChatService) -> None:
    renderer = StreamRenderer()
    printed_any = False
    async for event in chat.stream_message(
        message=message,
        conversation_id=session.conversation_id,
        provider=session.provider,
        model=session.model,
    ):
        match event.event:
            case "delta":
                content = event.data.get("content", "")
                if content:
                    renderer.write(content)
                    printed_any = True
            case "done":
                session.conversation_id = event.data.get("conversation_id") or session.conversation_id
                reply = event.data.get("reply", "")
                if not printed_any and reply:
                    renderer.write(reply)
                    printed_any = True
                renderer.close()
                if not printed_any:
                    cprint("(no response)")
            case "error":
                renderer.close()
                cprint(f"Error: {event.data.get('message', 'unknown error')}")
