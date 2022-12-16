from dataclasses import dataclass


@dataclass(frozen=True)
class Tweet:
    id: str
    created_at: str
    text: str


@dataclass(frozen=True)
class Appearance:
    datetime: str
    sections: list[tuple[str, str]]
    reason: str
    object: str
    train: str
    text: str


@dataclass(frozen=True)
class Location:
    lat: float
    lon: float

    @staticmethod
    def midpoint(a: "Location", b: "Location") -> "Location":
        new_lat = (a.lat + b.lat) / 2
        new_lon = (a.lon + b.lon) / 2
        return Location(new_lat, new_lon)

    def to_tuple(self):
        return (self.lat, self.lon)
