import time

import psutil


class CostMonitor:
    """Samples CPU and RSS for a frontend server and all its descendants."""

    def __init__(self, root_process, interval=0.5):
        self.root_process = root_process
        self.interval = interval
        self.cpu_process_tree_pct = []
        self.cpu_machine_pct = []
        self.ram_tree_mb = []
        self.process_counts = []
        self.logical_cpus = psutil.cpu_count(logical=True) or 1

    def _tree(self):
        processes = [self.root_process]
        try:
            processes.extend(self.root_process.children(recursive=True))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

        unique = {}
        for process in processes:
            try:
                if process.is_running():
                    unique[process.pid] = process
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return list(unique.values())

    def process_metadata(self):
        metadata = []
        for process in self._tree():
            try:
                metadata.append({
                    "pid": process.pid,
                    "parent_pid": process.ppid(),
                    "name": process.name(),
                    "command_line": process.cmdline(),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return metadata

    def _prime_cpu(self):
        for process in self._tree():
            try:
                process.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    def sample_for(self, duration_seconds):
        self._prime_cpu()
        started = time.monotonic()

        # Wait before the first retained observation so cpu_percent has a
        # meaningful interval. This avoids the artificial initial zero.
        time.sleep(self.interval)

        while time.monotonic() - started <= duration_seconds:
            tree = self._tree()
            cpu_total = 0.0
            rss_total = 0

            for process in tree:
                try:
                    cpu_total += process.cpu_percent(interval=None)
                    rss_total += process.memory_info().rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            self.cpu_process_tree_pct.append(round(cpu_total, 4))
            self.cpu_machine_pct.append(
                round(min(cpu_total / self.logical_cpus, 100.0), 4)
            )
            self.ram_tree_mb.append(round(rss_total / 1024 / 1024, 4))
            self.process_counts.append(len(tree))
            time.sleep(self.interval)

        return self.results()

    def results(self):
        return {
            "cpu_process_tree_pct": self.cpu_process_tree_pct,
            "cpu_machine_pct": self.cpu_machine_pct,
            "ram_tree_mb": self.ram_tree_mb,
            "process_counts": self.process_counts,
        }
