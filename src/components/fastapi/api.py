from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

from .type import APIDownloadModel

from src.components.twitter.utils import TweetMediaDownloader

router = APIRouter(prefix='/api')

@router.post('/get_info', response_class=JSONResponse)
async def get_info(model: APIDownloadModel):
    return await TweetMediaDownloader.get_info(model.url)

@router.post('/download', response_class=FileResponse)
async def download(model: APIDownloadModel):
    # 預設只會下載一個檔案
    results = await TweetMediaDownloader.download_media(model.url)
    return FileResponse(path=results[0], filename=results[0].name)
