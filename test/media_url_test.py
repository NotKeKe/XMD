import asyncio

from src.services.twitter.utils import get_media_items, get_tweet


async def main():
    tweet = await get_tweet('2027639682520256545')

    for idx, item in enumerate(get_media_items(tweet)):
        print(f'{idx}: [{item.type}] {item.direct_url}')


if __name__ == '__main__':
    asyncio.run(main())
