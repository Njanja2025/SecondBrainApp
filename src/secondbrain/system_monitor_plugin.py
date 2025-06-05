class SystemMonitorPlugin:
    def __init__(self):
        pass

    def get_system_metrics(self):
        return {"cpu_usage": 10, "memory_usage": 20}

    @staticmethod
    def _get_system_metrics():
        return {"cpu_usage": 10, "memory_usage": 20}
