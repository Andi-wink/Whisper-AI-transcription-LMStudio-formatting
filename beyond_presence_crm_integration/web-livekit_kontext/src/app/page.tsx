'use client';

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { BeyondPresenceStream } from '../lib/beyondpresence';
import type { UseBeyondPresenceConfig } from '../lib/beyondpresence';
import { RemoteAudioTrack, Room } from 'livekit-client';
import { useAuth } from '../lib/auth/AuthContext';
import { LoginPage } from '../components/LoginPage';
import { ChatPanel } from '../components/ChatPanel';

export default function Home() {
  const { isAuthenticated, user, logout } = useAuth();
  const [view, setView] = useState<'landing' | 'agent'>('landing');
  const [agentType, setAgentType] = useState<'voice' | 'video'>('video');
  const [isConnected, setIsConnected] = useState(false);
  const [room, setRoom] = useState<Room | null>(null);
  const [isChatOpen, setIsChatOpen] = useState(true);
  const [streamKey, setStreamKey] = useState(0); // Used to force remount stream
  const [shouldConnect, setShouldConnect] = useState(false); // Controls when to start connection
  const visualizerRef = useRef<HTMLDivElement>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  // Track if user has clicked to start agent
  const [userReady, setUserReady] = useState(false);
  const [pendingAgentType, setPendingAgentType] = useState<'voice' | 'video'>('video');
  const greetingTriggeredRef = useRef(false); // Prevent double-greeting

  // Start preloading when authenticated - single stream used for both preload and main view
  useEffect(() => {
    if (isAuthenticated && !shouldConnect) {
      console.log('🚀 Starting avatar preload...');
      setShouldConnect(true);
    }
  }, [isAuthenticated, shouldConnect]);

  // Helper: Update room metadata to trigger agent greeting
  const triggerAgentGreeting = useCallback(async (roomName: string, type: 'voice' | 'video') => {
    const livekitUrl = process.env.NEXT_PUBLIC_DEMO_LIVEKIT_URL || '';
    console.log(`🎯 Updating room metadata to disable preload (trigger greeting)...`);

    try {
      const response = await fetch('/api/beyondpresence/room-metadata', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          roomName: roomName,
          livekitUrl: livekitUrl,
          metadata: { mode: type, preload: false }
        })
      });

      if (response.ok) {
        console.log('✅ Room metadata updated - agent should greet now');
      } else {
        const error = await response.json();
        console.error('Failed to update room metadata:', error);
      }
    } catch (e) {
      console.error('Failed to update room metadata:', e);
    }
  }, []);

  // Trigger greeting when BOTH room is connected AND user has clicked
  useEffect(() => {
    if (room && userReady && !greetingTriggeredRef.current) {
      console.log('🟢 Both room connected AND user ready - triggering greeting!');
      greetingTriggeredRef.current = true;
      triggerAgentGreeting(room.name, pendingAgentType);
    }
  }, [room, userReady, pendingAgentType, triggerAgentGreeting]);

  // Single unified configuration - preloads on landing, same stream shown in agent view
  const config: UseBeyondPresenceConfig = {
    beyondPresence: {
      apiKey: process.env.NEXT_PUBLIC_BEY_API_KEY || ''
    },
    session: {
      avatarId: process.env.NEXT_PUBLIC_DEMO_AVATAR_ID || '',
      livekitToken: '',
      livekitUrl: process.env.NEXT_PUBLIC_DEMO_LIVEKIT_URL || '',
      mode: agentType, // Will be 'video' by default for preload
      preload: true // OPTION B: Agent waits for metadata change before greeting
    },
    autoConnect: shouldConnect, // Connect as soon as authenticated
    onError: (error) => {
      console.error('Connection Error:', error);
    },
    onConnected: () => {
      console.log('✅ Avatar connected and ready!');
      setIsConnected(true);
    },
    onDisconnected: () => {
      console.log('Disconnected');
      setIsConnected(false);
      setView('landing');
      cleanupVisualizer();
      // Restart connection for next use
      setStreamKey(prev => prev + 1);
      setShouldConnect(true);
    }
  };

  const handleStartAgent = (type: 'voice' | 'video') => {
    console.log('🔵 handleStartAgent called:', { type, roomExists: !!room, roomName: room?.name });

    // Mark user as ready - useEffect will trigger greeting when room is also ready
    setPendingAgentType(type);
    setUserReady(true);

    if (type === 'voice' && agentType !== 'voice') {
      // Switching to voice mode - need to reconnect with voice-only config
      setAgentType('voice');
      setStreamKey(prev => prev + 1); // Force remount
      setShouldConnect(true);
    } else if (type === 'video') {
      // Video mode - just reveal the already-connected stream!
      setAgentType('video');
    }
    setView('agent');
  };

  const handleDisconnect = useCallback(() => {
    console.log('🔴 Disconnecting...');
    if (room) {
      room.disconnect();
    }
    // State cleanup handled by onDisconnected callback
  }, [room]);

  // Visualizer Cleanup
  const cleanupVisualizer = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    analyserRef.current = null;
  }, []);

  // Handle Audio Track Attachment for Visualizer
  const handleAudioTrackAttached = useCallback((element: HTMLAudioElement, track: RemoteAudioTrack) => {
    if (agentType !== 'voice') return;

    try {
      // Initialize Audio Context
      const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
      const audioContext = new AudioContext();
      audioContextRef.current = audioContext;

      // Create Analyser
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 64; // Increased for better resolution (32 bins)
      analyser.smoothingTimeConstant = 0.5; // Smooth out the animation
      analyserRef.current = analyser;

      // Create Source from Track
      if (track.mediaStream) {
        const source = audioContext.createMediaStreamSource(track.mediaStream);
        source.connect(analyser);
      }

      // Start Animation Loop
      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      const updateVisualizer = () => {
        if (!analyserRef.current || !visualizerRef.current) return;

        analyserRef.current.getByteFrequencyData(dataArray);
        const bars = visualizerRef.current.children;

        // Symmetric Mapping (Mountain Shape)
        // We focus on the lower bins where speech energy is concentrated (0-10)
        // Center bar (index 2) gets the lowest/loudest frequencies
        // Side bars get progressively higher frequencies

        // Map bins to bars: [High, Mid, Low, Mid, High]
        // Bins: [4-5, 2-3, 0-1, 2-3, 4-5]

        const getAverage = (startIndex: number, count: number) => {
          let sum = 0;
          for (let i = 0; i < count; i++) {
            sum += dataArray[startIndex + i] || 0;
          }
          return sum / count;
        };

        // Calculate heights
        const center = getAverage(0, 2); // Bins 0-1 (Low freq, high energy)
        const mid = getAverage(2, 2);    // Bins 2-3 (Mid freq)
        const outer = getAverage(4, 3);  // Bins 4-6 (High-mid freq)

        const heights = [outer, mid, center, mid, outer];

        for (let i = 0; i < bars.length; i++) {
          // Map 0-255 to 20%-100% height, with a minimum threshold to keep it alive
          const value = heights[i];
          const height = 20 + (value / 255) * 80;
          (bars[i] as HTMLElement).style.height = `${height}%`;
        }

        animationFrameRef.current = requestAnimationFrame(updateVisualizer);
      };

      updateVisualizer();

    } catch (error) {
      console.error('Failed to setup visualizer:', error);
    }
  }, [agentType]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanupVisualizer();
    };
  }, [cleanupVisualizer]);

  // Check configuration
  const isConfigured = !!(
    process.env.NEXT_PUBLIC_BEY_API_KEY &&
    process.env.NEXT_PUBLIC_DEMO_AVATAR_ID &&
    process.env.NEXT_PUBLIC_DEMO_LIVEKIT_URL
  );

  if (!isConfigured) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black text-white">
        <div className="glass-card p-8 rounded-xl max-w-md text-center">
          <h2 className="text-2xl font-bold text-red-400 mb-4">Configuration Missing</h2>
          <p className="text-gray-300">Please check your environment variables.</p>
        </div>
      </div>
    );
  }

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <div className="min-h-screen relative">
      {/* Header with user info and logout */}
      {view === 'landing' && (
        <div className="absolute top-4 right-4 z-50 flex items-center gap-4">
          <span className="text-sm text-slate-400">
            Welcome, <span className="text-white">{user?.name}</span>
          </span>
          <button
            onClick={logout}
            className="px-4 py-2 text-sm text-slate-400 hover:text-white border border-white/10 rounded-lg hover:bg-white/5 transition-all"
          >
            Logout
          </button>
        </div>
      )}

      {/* Single BeyondPresenceStream - preloads on landing (hidden), shown in agent view */}
      {isAuthenticated && (
        <div
          key={streamKey}
          className={`fixed top-0 left-0 bottom-0 transition-all duration-300 ${view === 'agent' && agentType === 'video'
            ? 'opacity-100 z-40'
            : 'opacity-0 pointer-events-none -z-50'
            } ${view === 'agent' && isChatOpen
              ? 'right-80 lg:right-96'
              : 'right-0'
            }`}
        >
          <BeyondPresenceStream
            config={config}
            className="w-full h-full object-contain"
            showConnectionStatus={false}
            showErrorDisplay={view === 'agent' && agentType === 'video'}
            onAudioTrackAttached={handleAudioTrackAttached}
            onRoomConnected={(connectedRoom) => {
              console.log('🞣 Room connected:', connectedRoom.name);
              setRoom(connectedRoom);
              // useEffect will trigger greeting when userReady is also true
            }}
          />
        </div>
      )}

      {/* Landing View */}
      {view === 'landing' && (
        <div id="landing-view" className="flex flex-col items-center justify-center min-h-screen text-center p-5 animate-fade-in">
          <h1 className="text-5xl md:text-6xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400 pb-2">
            U-insure Support
          </h1>
          <p className="text-xl text-slate-400 mb-12 max-w-2xl">
            Experience the future of customer service. Choose your preferred way to connect with our AI agent.
          </p>

          <div className="flex flex-wrap justify-center gap-8">
            {/* Voice Agent Card */}
            <div
              onClick={() => handleStartAgent('voice')}
              className="glass-card p-10 rounded-3xl w-72 cursor-pointer transition-all duration-300 flex flex-col items-center"
            >
              <div className="mb-6 text-slate-200">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                  <line x1="12" y1="19" x2="12" y2="23"></line>
                  <line x1="8" y1="23" x2="16" y2="23"></line>
                </svg>
              </div>
              <h3 className="text-2xl font-bold mb-2 text-slate-50">Voice Agent</h3>
              <p className="text-slate-400 text-sm">High-fidelity voice interaction for quick questions and support.</p>
            </div>

            {/* Video Agent Card */}
            <div
              onClick={() => handleStartAgent('video')}
              className="glass-card p-10 rounded-3xl w-72 cursor-pointer transition-all duration-300 flex flex-col items-center"
            >
              <div className="mb-6 text-slate-200">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="23 7 16 12 23 17 23 7"></polygon>
                  <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
                </svg>
              </div>
              <h3 className="text-2xl font-bold mb-2 text-slate-50">Video Agent</h3>
              <p className="text-slate-400 text-sm">Face-to-face interaction with our hyper-realistic digital avatar.</p>
            </div>
          </div>

          {/* Connection Status Indicator */}
          <div className="mt-8 text-sm text-gray-500 opacity-50 hover:opacity-100 transition-opacity">
            {isConnected ? (
              <span className="text-green-400">✓ Agent ready</span>
            ) : shouldConnect ? (
              <span className="text-yellow-400">⏳ Preparing agent...</span>
            ) : (
              <span className="text-gray-500">Waiting...</span>
            )}
          </div>
        </div>
      )}

      {/* Agent View */}
      <div
        id="agent-view"
        className={`fixed inset-0 transition-opacity duration-500 pointer-events-none ${view === 'agent' ? 'opacity-100 z-50' : 'opacity-0 -z-10'}`}
      >
        {/* Main layout with video/voice and chat panel */}
        {view === 'agent' && (
          <div className="w-full h-full flex">
            {/* Video/Voice Area */}
            <div className={`flex-1 relative ${isChatOpen ? '' : 'w-full'}`}>
              {/* Voice mode visualizer overlay */}
              {agentType === 'voice' && (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-black">
                  <div className="visualizer-container" ref={visualizerRef}>
                    <div className="visualizer-bar"></div>
                    <div className="visualizer-bar"></div>
                    <div className="visualizer-bar"></div>
                    <div className="visualizer-bar"></div>
                    <div className="visualizer-bar"></div>
                  </div>
                </div>
              )}

              {/* Controls Bar */}
              {/* Controls Bar */}
              <div className="control-bar">
                {/* Microphone Toggle (Visual Only) */}
                <button className="btn-control" title="Toggle Microphone">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                    <line x1="12" y1="19" x2="12" y2="23"></line>
                    <line x1="8" y1="23" x2="16" y2="23"></line>
                  </svg>
                </button>

                {/* Camera Toggle (Visual Only) */}
                <button className="btn-control" title="Toggle Camera">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polygon points="23 7 16 12 23 17 23 7"></polygon>
                    <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
                  </svg>
                </button>

                {/* Toggle Chat Button */}
                <button
                  onClick={() => setIsChatOpen(!isChatOpen)}
                  className={`btn-control ${isChatOpen ? 'active' : ''}`}
                  title={isChatOpen ? 'Hide Chat' : 'Show Chat'}
                >
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                  </svg>
                </button>

                {/* End Call Button */}
                <button
                  onClick={handleDisconnect}
                  className="btn-control btn-end"
                  title="End Call"
                >
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M10.68 13.31a16 16 0 0 0 3.41 2.6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7 2 2 0 0 1 1.72 2v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.42 19.42 0 0 1-3.33-2.67m-2.67-3.34a19.79 19.79 0 0 1-3.07-8.63A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91"></path>
                    <line x1="23" y1="1" x2="1" y2="23"></line>
                  </svg>
                </button>
              </div>
            </div>

            {/* Chat Panel */}
            <div
              className={`h-full border-l border-white/10 transition-all duration-300 z-[70] pointer-events-auto bg-black/80 ${isChatOpen ? 'w-80 lg:w-96' : 'w-0 overflow-hidden'
                }`}
            >
              {isChatOpen && (
                <ChatPanel
                  room={room}
                  onSendMessage={(message) => {
                    // TODO: Send text message to agent via LiveKit
                    console.log('Send message:', message);
                  }}
                  onFileUpload={(file) => {
                    // TODO: Handle file upload
                    console.log('Upload file:', file);
                  }}
                  className="h-full"
                />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}