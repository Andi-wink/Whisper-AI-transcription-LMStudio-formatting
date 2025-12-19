'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Room, RoomEvent, TranscriptionSegment, Participant } from 'livekit-client';

interface Message {
  id: string;
  sender: 'user' | 'agent';
  senderName: string;
  text: string;
  timestamp: Date;
  isInterim?: boolean;
}

interface ChatPanelProps {
  room: Room | null;
  onSendMessage?: (message: string) => void;
  onFileUpload?: (file: File) => void;
  className?: string;
}

export function ChatPanel({ room, onSendMessage, onFileUpload, className = '' }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const processedSegmentsRef = useRef<Set<string>>(new Set());
  const recentTextsRef = useRef<Map<string, number>>(new Map()); // text -> timestamp for dedup

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Handle transcription events from LiveKit
  useEffect(() => {
    if (!room) {
      processedSegmentsRef.current.clear();
      return;
    }

    console.log('Setting up transcription handler for room:', room.name);
    console.log('Local participant identity:', room.localParticipant?.identity);

    const handleTranscription = (
      segments: TranscriptionSegment[],
      participant?: Participant
    ) => {
      const participantIdentity = participant?.identity || '';
      const localIdentity = room.localParticipant?.identity || '';
      
      console.log('Transcription from:', participantIdentity, '| Local:', localIdentity);
      
      segments.forEach((segment) => {
        // Only show final transcriptions (skip interim to avoid duplicates)
        if (!segment.final) {
          return;
        }
        
        // Create unique key for deduplication
        const segmentKey = `${segment.id}-final`;
        
        // Skip if already processed (prevents duplicates from multiple handlers)
        if (processedSegmentsRef.current.has(segmentKey)) {
          console.log('Skipping duplicate segment:', segmentKey);
          return;
        }
        
        // Also dedupe based on text content within 3 seconds (catches duplicates with different IDs)
        const textKey = `${participantIdentity}-${segment.text?.trim().toLowerCase()}`;
        const now = Date.now();
        const lastSeen = recentTextsRef.current.get(textKey);
        if (lastSeen && (now - lastSeen) < 3000) {
          console.log('Skipping duplicate text within 3s:', segment.text);
          return;
        }
        
        processedSegmentsRef.current.add(segmentKey);
        recentTextsRef.current.set(textKey, now);
        // Clean up old entries after 30 seconds
        setTimeout(() => {
          processedSegmentsRef.current.delete(segmentKey);
          recentTextsRef.current.delete(textKey);
        }, 30000);
        
        // Determine if this is from the local user or the agent
        // The transcription participant is who SPOKE the words
        // If it matches local participant, it's the user speaking
        const isLocalUser = participantIdentity === localIdentity;
        
        const sender = isLocalUser ? 'user' : 'agent';
        const senderName = isLocalUser ? 'You' : 'U-insure Agent';

        console.log(`Transcription [${sender}] (final=${segment.final}): "${segment.text}"`);

        if (!segment.text || segment.text.trim() === '') return;

        const newMessage: Message = {
          id: segmentKey,
          sender,
          senderName,
          text: segment.text,
          timestamp: new Date(),
          isInterim: false
        };

        setMessages(prev => {
          // Check if message with same ID already exists
          if (prev.some(m => m.id === segmentKey)) {
            return prev;
          }
          return [...prev, newMessage];
        });
      });
    };

    room.on(RoomEvent.TranscriptionReceived, handleTranscription);

    return () => {
      room.off(RoomEvent.TranscriptionReceived, handleTranscription);
    };
  }, [room]);

  // Handle text input send
  const handleSend = () => {
    if (!inputValue.trim()) return;

    // Add user message to chat
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      sender: 'user',
      senderName: 'You',
      text: inputValue,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    // Send to agent
    if (onSendMessage) {
      onSendMessage(inputValue);
    }

    setInputValue('');
  };

  // Handle file selection
  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);

    try {
      if (onFileUpload) {
        await onFileUpload(file);
      }

      // Add file message to chat
      const fileMessage: Message = {
        id: `file-${Date.now()}`,
        sender: 'user',
        senderName: 'You',
        text: `📎 Uploaded: ${file.name}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, fileMessage]);
    } catch (error) {
      console.error('File upload failed:', error);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // Handle enter key
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className={`flex flex-col h-full bg-black/80 backdrop-blur-xl ${className}`}>
      {/* Header */}
      <div className="px-4 py-3 border-b border-white/10">
        <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider">Chat</h2>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-slate-500 text-sm mt-8">
            <p>Conversation will appear here</p>
            <p className="text-xs mt-1">Speak or type to start</p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex flex-col ${message.sender === 'user' ? 'items-end' : 'items-start'}`}
            >
              {/* Sender Label */}
              <span className={`text-xs mb-1 ${
                message.sender === 'user' ? 'text-blue-400' : 'text-emerald-400'
              }`}>
                {message.senderName}
              </span>
              
              {/* Message Bubble */}
              <div
                className={`max-w-[85%] px-4 py-2 rounded-2xl ${
                  message.sender === 'user'
                    ? 'bg-blue-600/30 text-white rounded-br-md'
                    : 'bg-white/10 text-slate-200 rounded-bl-md'
                } ${message.isInterim ? 'opacity-70' : ''}`}
              >
                <p className="text-sm leading-relaxed">{message.text}</p>
              </div>
              
              {/* Timestamp */}
              <span className="text-xs text-slate-600 mt-1">
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                {message.isInterim && ' • typing...'}
              </span>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-white/10">
        <div className="flex items-center gap-2 bg-white/5 rounded-2xl px-4 py-2">
          {/* File Upload Button (Paperclip) */}
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="p-2 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
            title="Upload file"
          >
            {isUploading ? (
              <svg className="w-5 h-5 animate-spin" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            ) : (
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
              </svg>
            )}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileSelect}
            className="hidden"
            accept="image/*,.pdf,.doc,.docx,.txt"
          />

          {/* Text Input */}
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message"
            className="flex-1 bg-transparent text-white placeholder-slate-500 focus:outline-none text-sm"
          />

          {/* Send Button */}
          <button
            onClick={handleSend}
            disabled={!inputValue.trim()}
            className="px-3 py-1 text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors disabled:text-slate-600 disabled:cursor-not-allowed"
          >
            SEND
          </button>
        </div>
      </div>
    </div>
  );
}
