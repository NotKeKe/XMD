import { initDownloadView } from './views/download.js';
import { initOverviewView } from './views/overview.js';

const navDownload = document.getElementById('nav-download');
const navOverview = document.getElementById('nav-overview');
const downloadView = document.getElementById('download-view');
const overviewView = document.getElementById('overview-view');

function showView(view: 'download' | 'overview') {
    if (view === 'download') {
        downloadView?.classList.remove('hidden');
        overviewView?.classList.add('hidden');
        navDownload?.classList.add('active');
        navOverview?.classList.remove('active');
        initDownloadView();
    } else {
        downloadView?.classList.add('hidden');
        overviewView?.classList.remove('hidden');
        navDownload?.classList.remove('active');
        navOverview?.classList.add('active');
        initOverviewView();
    }
}

navDownload?.addEventListener('click', () => showView('download'));
navOverview?.addEventListener('click', () => showView('overview'));

// Initialize default view
initDownloadView();

// Handle Lucide icons
declare const lucide: any;
if (typeof lucide !== 'undefined') {
    lucide.createIcons();
}
