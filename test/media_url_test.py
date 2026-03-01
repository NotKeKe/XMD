import asyncio
from typing import cast
from pathlib import Path
from tweety.types import Media

from src.services.twitter.utils import _get_client

async def main():
    app = await _get_client()

    tweet = await app.tweet_detail('2027639682520256545')
    
    for m in tweet.media:  
        m = cast(Media, m)
        media_type = m.type


        # download
        download_url = None
        if media_type == "photo":  
            download_url = m.url
        elif media_type in ("video", "animated_gif"):  
            best = await m.best_stream()  
            if best: download_url = best.url

        print(download_url)

if __name__ == '__main__':
    asyncio.run(main())