import React, { useState } from 'react';

const CameraFeed = () => {
    const [isLive, setIsLive] = useState(true);
    const cameraUrl = "http://localhost:5000"; // Mobile Camera Server URL

    return (
        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg h-[500px] flex flex-col">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <span>📹</span> Live Traffic Camera
                    {isLive && (
                        <span className="flex h-3 w-3 relative ml-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                        </span>
                    )}
                </h3>
                <div className="flex gap-2">
                    <button
                        onClick={() => setIsLive(!isLive)}
                        className={`px-3 py-1 rounded text-sm font-medium transition-colors ${isLive ? 'bg-red-500/20 text-red-400' : 'bg-slate-700 text-slate-400'
                            }`}
                    >
                        {isLive ? 'LIVE' : 'OFFLINE'}
                    </button>
                    <a
                        href={`${cameraUrl}/dashboard`}
                        target="_blank"
                        rel="noreferrer"
                        className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded text-sm hover:bg-blue-500/30 transition-colors"
                    >
                        Open Dashboard ↗
                    </a>
                </div>
            </div>

            <div className="flex-1 bg-black rounded-lg overflow-hidden relative border border-slate-700">
                {isLive ? (
                    <iframe
                        src={cameraUrl}
                        title="Live Camera Feed"
                        className="w-full h-full border-0"
                        allow="camera; microphone"
                        onError={() => setIsLive(false)}
                    />
                ) : (
                    <div className="w-full h-full flex flex-col items-center justify-center text-slate-500">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mb-4 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                        <p>Camera feed offline</p>
                        <p className="text-xs mt-2 text-slate-600">Ensure Mobile Camera Server is running on port 5000</p>
                    </div>
                )}
            </div>

            <div className="mt-4 grid grid-cols-3 gap-4 text-center text-sm text-slate-400">
                <div className="bg-slate-900/50 p-2 rounded">
                    <div className="text-slate-500 text-xs uppercase mb-1">Status</div>
                    <div className="text-green-400 font-bold">Connected</div>
                </div>
                <div className="bg-slate-900/50 p-2 rounded">
                    <div className="text-slate-500 text-xs uppercase mb-1">Source</div>
                    <div className="text-white">Mobile Cam</div>
                </div>
                <div className="bg-slate-900/50 p-2 rounded">
                    <div className="text-slate-500 text-xs uppercase mb-1">Detection</div>
                    <div className="text-blue-400 font-bold">Active</div>
                </div>
            </div>
        </div>
    );
};

export default CameraFeed;
