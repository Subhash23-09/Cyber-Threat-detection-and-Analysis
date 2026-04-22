import { useState, useCallback } from 'react';
import { Upload as UploadIcon, File, CheckCircle, AlertCircle, Download, Brain, CloudUpload } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import { uploadFile, processFile } from '../api/client';

export interface UploadProps {
  onUploadSuccess?: (filename: string) => void;
  onAnalysisComplete?: (filename: string, signals: any[], stats: any) => void;
}

export function Upload({ onUploadSuccess, onAnalysisComplete }: UploadProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [uploadStatus, setUploadStatus] = useState<Record<string, 'idle' | 'uploading' | 'uploaded' | 'processing' | 'success' | 'error' | 'rejected'>>({});
  const [downloadLinks, setDownloadLinks] = useState<Record<string, string>>({});
  const [remainingUploads, setRemainingUploads] = useState(5);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setErrorMsg(null);
    let validFiles: File[] = [];
    let rejectedCount = 0;
    for (const file of acceptedFiles) {
      const ext = file.name.split('.').pop()?.toLowerCase();
      if (!['log', 'csv', 'pcap'].includes(ext || '')) { rejectedCount++; continue; }
      validFiles.push(file);
    }
    if (rejectedCount > 0) setErrorMsg(`Skipped ${rejectedCount} file(s) due to invalid type.`);
    if (validFiles.length > remainingUploads) {
      setErrorMsg(`Limit reached. You can only upload ${remainingUploads} more file(s).`);
      validFiles = validFiles.slice(0, remainingUploads);
    }
    if (validFiles.length === 0) return;
    setRemainingUploads(prev => prev - validFiles.length);
    setFiles(prev => [...prev, ...validFiles]);
    for (const file of validFiles) {
      setUploadStatus(prev => ({ ...prev, [file.name]: 'uploading' }));
      try {
        const result = await uploadFile(file);
        setUploadStatus(prev => ({ ...prev, [file.name]: 'uploaded' }));
        if (onUploadSuccess && result.filename) onUploadSuccess(result.filename);
      } catch (err) {
        console.error(err);
        setUploadStatus(prev => ({ ...prev, [file.name]: 'error' }));
      }
    }
  }, [remainingUploads, onUploadSuccess]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.log'],
      'text/csv': ['.csv'],
      'application/vnd.tcpdump.pcap': ['.pcap'],
      'application/octet-stream': ['.log', '.pcap'],
    },
    maxSize: 3 * 1024 * 1024 * 1024,
    onDropRejected: (rejections) => {
      const sizeRejected = rejections.some(r => r.errors.some(e => e.code === 'file-too-large'));
      const typeRejected = rejections.some(r => r.errors.some(e => e.code === 'file-invalid-type'));
      if (sizeRejected) setErrorMsg('Some files were rejected: File too large (Max 3GB).');
      else if (typeRejected) setErrorMsg('Some files were rejected: Invalid file type. Allowed: .log, .csv, .pcap.');
      else setErrorMsg('Some files were rejected due to an unknown error.');
    },
  });

  const startAnalysis = async (filename: string) => {
    setUploadStatus(prev => ({ ...prev, [filename]: 'processing' }));
    try {
      const processResult = await processFile(filename);
      setDownloadLinks(prev => ({ ...prev, [filename]: processResult.download_url }));
      setUploadStatus(prev => ({ ...prev, [filename]: 'success' }));
      if (onAnalysisComplete) onAnalysisComplete(filename, [], processResult.stats);
    } catch (err) {
      console.error(err);
      setUploadStatus(prev => ({ ...prev, [filename]: 'error' }));
    }
  };

  const downloadSignals = (filename: string) => {
    const url = downloadLinks[filename];
    if (!url) return;
    window.open(`http://localhost:8000${url}`, '_blank');
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-6 space-y-6">
      {/* Drop zone */}
      <div
        {...getRootProps()}
        className="rounded-xl p-12 text-center transition-all duration-300 cursor-pointer"
        style={{
          border: isDragActive
            ? '2px solid #2563EB'
            : '2px dashed rgba(255,255,255,0.12)',
          background: isDragActive ? 'rgba(37,99,235,0.08)' : 'var(--bg-surface)',
        }}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-4">
          <div
            className="p-4 rounded-full"
            style={{
              background: isDragActive ? 'rgba(37,99,235,0.2)' : 'var(--bg-elevated)',
              border: '1px solid var(--border-card)',
            }}
          >
            <CloudUpload className="w-8 h-8" style={{ color: isDragActive ? '#60A5FA' : 'var(--text-muted)' }} />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
              {isDragActive ? 'Drop files here...' : 'Drop security logs here'}
            </h3>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              Support for .log, .csv, and .pcap (Max 3GB)
            </p>
            <p className="text-xs font-mono px-2 py-1 rounded inline-block mt-1"
              style={{ background: 'rgba(37,99,235,0.12)', color: '#60A5FA' }}>
              Remaining Uploads: {remainingUploads}
            </p>
            {errorMsg && (
              <p className="text-sm font-medium mt-2" style={{ color: '#F87171' }}>{errorMsg}</p>
            )}
          </div>
          <button
            type="button"
            className="btn-primary mt-2"
          >
            <UploadIcon className="w-4 h-4" /> Select Files
          </button>
        </div>
      </div>

      {/* Activity list */}
      {files.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs uppercase tracking-widest font-medium px-1" style={{ color: 'var(--text-muted)' }}>
            Activity
          </p>
          <div className="space-y-2">
            {files.map((file, idx) => (
              <div
                key={`${file.name}-${idx}`}
                className="flex items-center justify-between p-4 rounded-xl transition-all"
                style={{
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border-card)',
                }}
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg" style={{ background: 'var(--bg-elevated)' }}>
                    <File className="w-4 h-4" style={{ color: '#60A5FA' }} />
                  </div>
                  <div>
                    <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{file.name}</p>
                    <p className="text-xs font-mono" style={{ color: 'var(--text-muted)' }}>
                      {(file.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {uploadStatus[file.name] === 'uploading' && (
                    <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--text-secondary)' }}>
                      <div className="w-3 h-3 border-2 rounded-full animate-spin"
                        style={{ borderColor: 'rgba(37,99,235,0.3)', borderTopColor: '#2563EB' }} />
                      Uploading...
                    </div>
                  )}
                  {uploadStatus[file.name] === 'uploaded' && (
                    <div className="flex items-center gap-1 text-xs" style={{ color: '#34D399' }}>
                      <CheckCircle className="w-4 h-4" />
                      <span>Uploaded</span>
                    </div>
                  )}
                  {uploadStatus[file.name] === 'processing' && (
                    <div className="flex items-center gap-2 text-xs" style={{ color: '#60A5FA' }}>
                      <div className="w-3 h-3 border-2 rounded-full animate-spin"
                        style={{ borderColor: 'rgba(37,99,235,0.3)', borderTopColor: '#2563EB' }} />
                      Converting...
                    </div>
                  )}
                  {uploadStatus[file.name] === 'success' && (
                    <div className="flex items-center gap-2">
                      <span className="flex items-center gap-1 text-xs font-bold" style={{ color: '#34D399' }}>
                        <CheckCircle className="w-4 h-4" /> Ready
                      </span>
                      {downloadLinks[file.name] && (
                        <button onClick={() => downloadSignals(file.name)}
                          className="p-1.5 rounded transition-all"
                          style={{ color: 'var(--text-muted)' }}
                          title="Download JSON"
                        >
                          <Download className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  )}
                  {uploadStatus[file.name] === 'error' && (
                    <AlertCircle className="w-4 h-4" style={{ color: '#F87171' }} />
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Trigger button */}
          {Object.values(uploadStatus).some(s => s === 'uploaded') && (
            <div className="flex justify-center pt-2">
              <button
                onClick={() => files.forEach(f => { if (uploadStatus[f.name] === 'uploaded') startAnalysis(f.name); })}
                className="btn-primary px-8 py-3 text-base rounded-xl"
                style={{
                  background: 'linear-gradient(135deg, #4F46E5, #7C3AED)',
                  boxShadow: '0 4px 20px rgba(79,70,229,0.3)',
                }}
              >
                <Brain className="w-5 h-5" />
                Start Analysis ({files.filter(f => uploadStatus[f.name] === 'uploaded').length} files ready)
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
