from datetime import timezone


def serialize_meeting(meeting):
    instant = meeting["starts_at"].astimezone(timezone.utc)
    return {"id": meeting["id"], "starts_at": instant.strftime("%Y-%m-%dT%H:%M:%SZ")}


def serialize_deadline(deadline):
    instant = deadline["due_at"].astimezone(timezone.utc)
    return {"id": deadline["id"], "due_at": instant.strftime("%Y-%m-%dT%H:%M:%SZ")}


def serialize_event(event):
    raise NotImplementedError("Add event serialization")
