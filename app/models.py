from dataclasses import dataclass, asdict

@dataclass
class Endpoint:
    id: str
    tenant: str
    name: str
    url: str
    enabled: bool
    revision: int

    def json(self, dataset_revision: int):
        out = asdict(self)
        out["datasetRevision"] = dataset_revision
        return out

@dataclass
class Delivery:
    id: str
    endpointId: str
    eventId: str
    streamKey: str
    sequence: int
    receivedAt: str
    status: str
    errorCode: str
    replayAttempts: int
    simulation: str

    def json(self):
        return asdict(self)
