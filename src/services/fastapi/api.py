from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from tweety.types import Tweet
from zipstream import ZipStream, ZIP_DEFLATED
import asyncio

from .type import APIDownloadModel

from src.services.twitter.utils import TweetMediaDownloader, get_tweet_id

router = APIRouter(prefix='/api')

tweet_objs: dict[str, Tweet] = {}

async def cleanup_tweet_objs():
    while True:
        tweet_objs.clear()
        await asyncio.sleep(60) # 1 min

@router.post('/get_info', response_class=JSONResponse)
async def get_info(model: APIDownloadModel):
    tweet_id = get_tweet_id(model.url)
    info, tweet = await TweetMediaDownloader.get_info(tweet_id)
    tweet_objs[tweet_id] = tweet
    return info

@router.post('/download', response_class=StreamingResponse)
async def download(model: APIDownloadModel):
    # 先試著取得 tweet obj
    tweet_id = get_tweet_id(model.url)
    tweet = tweet_objs.get(tweet_id)
    results = await TweetMediaDownloader.download_media(
        **({'tweet': tweet} if tweet else {'tweet_id': tweet_id}) # type: ignore
    )

    if not results:
        return JSONResponse({"error": "No media found"}, status_code=404)

    elif len(results) > 1:
        zs = ZipStream(compress_type=ZIP_DEFLATED)
        for path in results:
            if path.is_file():
                zs.add_path(str(path.resolve()), arcname=path.name)

        headers = {
            "Content-Disposition": f'attachment; filename="{tweet_id}.zip"',
        }

        return StreamingResponse(zs, media_type="application/zip", headers=headers)
    else:
        return FileResponse(path=results[0], filename=results[0].name)