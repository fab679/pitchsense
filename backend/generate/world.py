"""
Fictional football league, clubs, rosters, and tactical presets for PitchSense.
Complies with competition rule §4.7 (strictly synthetic, 0 third-party trademarks).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class Player:
    code: str
    number: int
    name: str
    position: str  # GK, CB, LB, RB, DM, CM, AM, LW, RW, CF
    pace: float  # 0.0 to 1.0
    passing_skill: float  # 0.0 to 1.0
    shot_power: float  # 0.0 to 1.0
    press_resistance: float  # 0.0 to 1.0
    preferred_zone_x: float  # average nominal pitch coordinate [0..105]
    preferred_zone_y: float  # average nominal pitch coordinate [0..68]

@dataclass
class TeamTactics:
    press_intensity: float = 0.75  # 0.0 (low block) to 1.0 (heavy metal press)
    tempo: float = 0.70           # 0.0 (patient build-up) to 1.0 (blitz transition)
    line_height: float = 62.0     # Defensive line position (meters from own goal)
    directness: float = 0.45      # 0.0 (short tiki-taka) to 1.0 (long direct balls)

@dataclass
class Team:
    code: str
    name: str
    short_name: str
    stadium: str
    primary_color: str
    secondary_color: str
    tactics: TeamTactics
    roster: List[Player] = field(default_factory=list)

    def get_player(self, code: str) -> Optional[Player]:
        for p in self.roster:
            if p.code == code:
                return p
        return None

# Fictional Clubs & Squads
SALTMARSH_ROVERS = Team(
    code="SAL",
    name="Saltmarsh Rovers",
    short_name="Rovers",
    stadium="Marsh Point Ground",
    primary_color="#0F766E",  # Teal 700
    secondary_color="#F0FDFA",  # Teal 50
    tactics=TeamTactics(
        press_intensity=0.82,
        tempo=0.78,
        line_height=65.0,
        directness=0.55
    ),
    roster=[
        Player("sal_01", 1, "Eamon Vance", "GK", 0.60, 0.65, 0.50, 0.70, 5.0, 34.0),
        Player("sal_02", 2, "Kieran Holt", "RB", 0.82, 0.74, 0.58, 0.68, 35.0, 10.0),
        Player("sal_04", 4, "Declan Cross", "CB", 0.70, 0.68, 0.45, 0.65, 26.0, 24.0),
        Player("sal_05", 5, "Bram O'Rourke", "CB", 0.68, 0.70, 0.52, 0.72, 26.0, 44.0),
        Player("sal_03", 3, "Nico Finch", "LB", 0.84, 0.72, 0.55, 0.64, 35.0, 58.0),
        Player("sal_06", 6, "Tariq Danvers", "DM", 0.72, 0.81, 0.62, 0.85, 45.0, 34.0),
        Player("sal_08", 8, "Carlos Rosmere", "CM", 0.78, 0.88, 0.75, 0.90, 58.0, 26.0),
        Player("sal_10", 10, "Felix Bram", "AM", 0.85, 0.91, 0.82, 0.92, 70.0, 38.0),
        Player("sal_07", 7, "Julian Thorne", "RW", 0.90, 0.78, 0.79, 0.76, 75.0, 12.0),
        Player("sal_11", 11, "Malik Vance", "LW", 0.88, 0.76, 0.78, 0.74, 75.0, 56.0),
        Player("sal_09", 9, "Daan Visser", "CF", 0.84, 0.75, 0.89, 0.82, 85.0, 34.0),
        # Bench
        Player("sal_12", 12, "Gage Bennett", "CM", 0.74, 0.75, 0.65, 0.72, 55.0, 34.0),
        Player("sal_14", 14, "Corin Sterling", "CF", 0.82, 0.70, 0.81, 0.75, 82.0, 34.0),
        Player("sal_15", 15, "Samir Boyd", "CB", 0.69, 0.66, 0.40, 0.64, 25.0, 34.0),
    ]
)

BRACKFIELD_ATHLETIC = Team(
    code="BRA",
    name="Brackfield Athletic",
    short_name="Athletic",
    stadium="High Ridge Park",
    primary_color="#E11D48",  # Rose 600
    secondary_color="#FFF1F2",  # Rose 50
    tactics=TeamTactics(
        press_intensity=0.68,
        tempo=0.62,
        line_height=58.0,
        directness=0.38
    ),
    roster=[
        Player("bra_01", 1, "Milan Cassian", "GK", 0.58, 0.72, 0.48, 0.75, 5.0, 34.0),
        Player("bra_02", 2, "Zack Alder", "RB", 0.79, 0.76, 0.55, 0.72, 34.0, 12.0),
        Player("bra_04", 4, "Kaelen Ward", "CB", 0.66, 0.78, 0.50, 0.80, 25.0, 25.0),
        Player("bra_05", 5, "Orson Fletcher", "CB", 0.68, 0.75, 0.52, 0.78, 25.0, 43.0),
        Player("bra_03", 3, "Lucian Val", "LB", 0.81, 0.79, 0.60, 0.74, 34.0, 56.0),
        Player("bra_06", 6, "Anders Rowe", "DM", 0.70, 0.84, 0.66, 0.86, 44.0, 34.0),
        Player("bra_08", 8, "Hugo Sterling", "CM", 0.76, 0.89, 0.78, 0.88, 56.0, 42.0),
        Player("bra_10", 10, "Stefan Mercer", "AM", 0.82, 0.90, 0.85, 0.89, 68.0, 30.0),
        Player("bra_07", 7, "Jonas Lind", "RW", 0.87, 0.80, 0.77, 0.78, 74.0, 14.0),
        Player("bra_11", 11, "Mateo Diaz", "LW", 0.89, 0.77, 0.80, 0.77, 74.0, 54.0),
        Player("bra_09", 9, "Cyrus Vance", "CF", 0.81, 0.73, 0.88, 0.80, 84.0, 34.0),
        # Bench
        Player("bra_14", 14, "Enzo Ruiz", "CM", 0.75, 0.82, 0.70, 0.78, 55.0, 34.0),
        Player("bra_17", 17, "Leo Navarro", "CF", 0.83, 0.69, 0.82, 0.74, 82.0, 34.0),
        Player("bra_18", 18, "Toby Marsh", "CB", 0.67, 0.70, 0.45, 0.70, 25.0, 34.0),
    ]
)

TEAMS: Dict[str, Team] = {
    "SAL": SALTMARSH_ROVERS,
    "BRA": BRACKFIELD_ATHLETIC,
}

def get_team(code: str) -> Optional[Team]:
    return TEAMS.get(code.upper())
