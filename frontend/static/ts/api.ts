export interface MediaInfo {
    text: string;
    url: string;
    id: string;
    author: string | null;
    media: {
        len: number;
        urls: { url: string; thumbnail: string; type: string }[];
    };
}

export interface DownloadHistoryItem {
    id: number;
    tweet_id: string;
    media_id: string;
    media_type: string;
    download_path: string;
    downloaded_at: string;
}

export async function getInfo(url: string): Promise<MediaInfo> {
    const response = await fetch('/api/get_info', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
    });
    if (!response.ok) throw new Error('Failed to get media info');
    return await response.json();
}

export async function downloadMedia(url: string, indices?: number[]): Promise<void> {
    const response = await fetch('/api/download', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url, indices }),
    });

    if (!response.ok) throw new Error('Download failed');

    // Handle file download
    const blob = await response.blob();
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = 'download';
    if (contentDisposition) {
        const match = contentDisposition.match(/filename="?([^"]+)"?/);
        if (match?.[1]) filename = match[1];
    }

    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(downloadUrl);
    a.remove();
}

export async function getMediaHistory(): Promise<DownloadHistoryItem[]> {
    const response = await fetch('/api/media');
    if (!response.ok) throw new Error('Failed to fetch media history');
    return await response.json();
}
