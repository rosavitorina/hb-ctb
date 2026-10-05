from dataclasses import dataclass


@dataclass
class Owner:
    owner_id: str
    participant_id: str
    name: str