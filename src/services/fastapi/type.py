from pydantic import BaseModel

class APIDownloadModel(BaseModel):
    url: str # twitter url
    indices: list[int] | None = None # index of media to download