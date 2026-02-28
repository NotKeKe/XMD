from abc import ABC, abstractmethod

class ServicesABC(ABC):
    @abstractmethod
    async def run(self) -> None:
        '''在這裡實作一個長久運行服務的啟動 (如 while True)'''
        pass

    @abstractmethod
    async def stop(self) -> None:
        '''在這裡完成資源釋放'''
        pass