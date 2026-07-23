
from dataclasses import dataclass



@dataclass
class WorkerError:
    exception: Exception
    traceback: str