const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const uploadFile = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    console.log(`[client.ts] Uploading ${file.name} to ${API_URL}/ingestion/upload...`);
    try {
        const response = await fetch(`${API_URL}/ingestion/upload`, {
            method: 'POST',
            body: formData,
        });

        console.log(`[client.ts] Response status: ${response.status}`);

        if (!response.ok) {
            throw new Error(`Upload failed with status ${response.status}`);
        }

        const data = await response.json();
        console.log(`[client.ts] Upload success:`, data);
        return data;
    } catch (error) {
        console.error(`[client.ts] Fetch error for ${file.name}:`, error);
        throw error;
    }
};

export const processFile = async (filename: string) => {
    const response = await fetch(`${API_URL}/processing/process/${filename}`, {
        method: 'POST',
    });

    if (!response.ok) {
        throw new Error('Processing failed');
    }

    return response.json();
};
