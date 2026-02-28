from pydantic import BaseModel

class APIDownloadModel(BaseModel):
    url: str # twitter url