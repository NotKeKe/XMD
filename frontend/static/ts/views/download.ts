import { getInfo, downloadMedia, type MediaInfo } from '../api.js';

const urlInput = document.getElementById('url-input') as HTMLInputElement;
const getInfoBtn = document.getElementById('get-info-btn') as HTMLButtonElement | null;
const infoResults = document.getElementById('info-results');
const mediaCount = document.getElementById('media-count');
const mediaList = document.getElementById('media-list');
const downloadAllBtn = document.getElementById('download-all-btn') as HTMLButtonElement | null;

let currentMediaInfo: MediaInfo | null = null;

export function initDownloadView() {
    if (getInfoBtn) {
        getInfoBtn.onclick = async () => {
            const url = urlInput.value.trim();
            if (!url) return;

            try {
                if (getInfoBtn) getInfoBtn.innerHTML = '讀取中...';
                currentMediaInfo = await getInfo(url);
                renderMediaInfo(currentMediaInfo);
                infoResults?.classList.remove('hidden');
            } catch (error) {
                alert('獲取資訊失敗: ' + error);
            } finally {
                if (getInfoBtn) getInfoBtn.innerHTML = '獲取資訊';
            }
        };
    }

    if (downloadAllBtn) {
        downloadAllBtn.onclick = async () => {
            if (!currentMediaInfo) return;
            const originalText = downloadAllBtn.innerText;
            try {
                downloadAllBtn.innerText = '下載中...';
                downloadAllBtn.disabled = true;
                await downloadMedia(currentMediaInfo.url);
            } catch (error) {
                alert('下載失敗: ' + error);
            } finally {
                downloadAllBtn.innerText = originalText;
                downloadAllBtn.disabled = false;
            }
        };
    }
}

function renderMediaInfo(info: MediaInfo) {
    if (!mediaCount || !mediaList) return;

    mediaCount.innerText = info.media.len.toString();
    mediaList.innerHTML = '';

    info.media.urls.forEach((mediaObj, index) => {
        const item = document.createElement('div');
        item.className = 'flex items-center gap-4 p-4 border border-gray-100 rounded-lg bg-gray-50';
        
        const isVideo = mediaObj.type === 'video' || mediaObj.type === 'animated_gif';
        
        item.innerHTML = `
            <input type="checkbox" class="w-5 h-5 border-gray-300 rounded text-black focus:ring-black" data-index="${index}">
            <div class="w-20 h-20 bg-gray-200 rounded overflow-hidden flex-shrink-0 relative">
                ${isVideo ? '<div class="absolute inset-0 flex items-center justify-center bg-black/20 text-white"><i data-lucide="play" class="w-8 h-8"></i></div>' : ''}
                <img src="${mediaObj.thumbnail}" class="w-full h-full object-cover" referrerpolicy="no-referrer">
            </div>
            <div class="flex-grow">
                <p class="text-sm font-medium text-gray-500 uppercase tracking-wider">${mediaObj.type}</p>
                <p class="text-xs text-gray-400 truncate max-w-[200px]">${mediaObj.url}</p>
            </div>
            <button class="download-single-btn p-2 hover:bg-gray-200 rounded-full transition-colors flex items-center justify-center min-w-[40px] min-h-[40px]" data-index="${index}">
                <i data-lucide="download" class="w-5 h-5 text-gray-600"></i>
            </button>
        `;
        mediaList.appendChild(item);
    });

    // Re-create icons for injected items
    (window as any).lucide?.createIcons();

    // Setup single download buttons
    const singleDownloadBtns = mediaList.querySelectorAll('.download-single-btn');
    singleDownloadBtns.forEach(btn => {
        const buttonElement = btn as HTMLButtonElement;
        buttonElement.onclick = async () => {
            const index = parseInt(buttonElement.getAttribute('data-index') || '0');
            const iconContainer = buttonElement.querySelector('i');
            const originalIcon = iconContainer?.getAttribute('data-lucide');
            
            if (currentMediaInfo) {
                try {
                    if (iconContainer) {
                        iconContainer.setAttribute('data-lucide', 'refresh-cw');
                        iconContainer.classList.add('animate-spin-fast');
                        (window as any).lucide?.createIcons();
                    }
                    buttonElement.disabled = true;

                    await downloadMedia(currentMediaInfo.url, [index]);
                } catch (error) {
                    alert('下載失敗: ' + error);
                } finally {
                    buttonElement.disabled = false;
                    if (iconContainer && originalIcon) {
                        iconContainer.setAttribute('data-lucide', originalIcon);
                        iconContainer.classList.remove('animate-spin-fast');
                        (window as any).lucide?.createIcons();
                    }
                }
            }
        };
    });
}
