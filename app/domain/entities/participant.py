from dataclasses import dataclass
from enum import Enum


class ParticipantType(Enum):
    INDIVIDUAL = "individual"
    CORPORATE = "corporate"


@dataclass
class Participant:
    participant_id: str
    participant_type: ParticipantType
    name: str
    tax_id: str