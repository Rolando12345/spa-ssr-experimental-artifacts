import psutil


def _process_matches(process, architecture):
    try:
        if process.pid <= 4 or process.name().lower() not in ("node.exe", "node"):
            return False
        command = " ".join(process.cmdline()).lower()
        if architecture.upper() == "SPA":
            return "serve" in command and ("-l 4200" in command or "--listen 4200" in command)
        return "next" in command and "start" in command and ("-p 3000" in command or "--port 3000" in command)
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return False


def find_process(port: int, architecture: str):
    """Return only the verified Node.js process LISTENING on the target port."""
    candidates = []
    for connection in psutil.net_connections(kind="inet"):
        try:
            if not connection.laddr or connection.laddr.port != port:
                continue
            if connection.status != psutil.CONN_LISTEN:
                continue
            if connection.pid is None or connection.pid <= 4:
                continue
            process = psutil.Process(connection.pid)
            if process.is_running() and _process_matches(process, architecture):
                candidates.append(process)
        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
            AttributeError,
        ):
            continue

    unique = {process.pid: process for process in candidates}
    if len(unique) != 1:
        found = sorted(unique)
        raise RuntimeError(
            f"Expected exactly one verified {architecture} Node.js LISTEN process "
            f"on port {port}; found PIDs: {found or 'none'}"
        )
    return next(iter(unique.values()))
