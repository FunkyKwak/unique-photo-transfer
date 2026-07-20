from dataclasses import dataclass
from enum import Enum
from typing import Optional

class ProgressPhase(Enum):
    INDEX = "index"
    COPY = "copy"
    
@dataclass
class ProgressEvent:
    phase: ProgressPhase
    root_folder: str
    current: int
    total: Optional[int] = None
    message: str = ""