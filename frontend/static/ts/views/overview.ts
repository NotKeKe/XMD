import { getMediaHistory, type DownloadHistoryItem } from '../api.js';

const overviewGrid = document.getElementById('overview-grid');
const filterBtns = document.querySelectorAll('.filter-btn');

let historyItems: DownloadHistoryItem[] = [];
let currentFilter = 'all';

export async function initOverviewView() {
    try {
        historyItems = await getMediaHistory();
        renderOverview();
    } catch (error) {
        console.error('Failed to load history:', error);
    }

    filterBtns.forEach(btn => {
        (btn as HTMLButtonElement).onclick = () => {
            currentFilter = btn.getAttribute('data-filter') || 'all';
            
            // Update UI
            filterBtns.forEach(b => {
                b.classList.remove('bg-black', 'text-white');
                b.classList.add('bg-white', 'text-gray-600');
            });
            btn.classList.add('bg-black', 'text-white');
            btn.classList.remove('bg-white', 'text-gray-600');

            renderOverview();
        };
    });
}

function renderOverview() {
    if (!overviewGrid) return;

    overviewGrid.innerHTML = '';
    const filtered = historyItems.filter(item => {
        if (currentFilter === 'all') return true;
        if (currentFilter === 'photo') return item.media_type === 'photo';
        if (currentFilter === 'video') return item.media_type === 'video' || item.media_type === 'animated_gif';
        return true;
    });

    if (filtered.length === 0) {
        overviewGrid.innerHTML = '<div class="col-span-full py-20 text-center text-gray-400">目前沒有下載記錄</div>';
        return;
    }

    filtered.forEach(item => {
        const card = document.createElement('div');
        card.className = 'group relative aspect-square bg-gray-100 rounded-xl overflow-hidden border border-gray-100 shadow-sm hover:shadow-md transition-all duration-300';
        
        const isVideo = item.media_type === 'video' || item.media_type === 'animated_gif';
        const mediaUrl = `/media/${item.download_path.split(/[\\/]/).pop()}`;

        card.innerHTML = `
            ${isVideo ? `
                <video class="w-full h-full object-cover">
                    <source src="${mediaUrl}" type="video/mp4">
                </video>
                <div class="absolute inset-0 flex items-center justify-center bg-black/10 group-hover:bg-black/30 transition-colors">
                    <i data-lucide="play-circle" class="w-12 h-12 text-white opacity-80"></i>
                </div>
            ` : `
                <img src="${mediaUrl}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500">
            `}
            <div class="absolute bottom-0 inset-x-0 p-3 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                <p class="text-[10px] text-white/80 font-mono">${item.tweet_id}</p>
            </div>
            <a href="${mediaUrl}" target="_blank" class="absolute inset-0 z-10"></a>
        `;
        overviewGrid.appendChild(card);
    });

    // Re-create icons
    (window as any).lucide?.createIcons();
}
