/**
 * LiveKit Avatar Integration
 * Connects to LiveKit room with custom agent and displays avatar video
 */

class AvatarApp {
  constructor() {
    this.room = null;
    this.isMuted = false;
    this.isConnected = false;
    
    // UI Elements
    this.elements = {
      startBtn: document.getElementById('start-btn'),
      endBtn: document.getElementById('end-btn'),
      muteBtn: document.getElementById('mute-btn'),
      statusText: document.getElementById('status-text'),
      statusIndicator: document.querySelector('.status-indicator'),
      avatarVideo: document.getElementById('avatar-video'),
      welcomeScreen: document.getElementById('welcome-screen'),
      loading: document.getElementById('loading'),
      transcriptContainer: document.getElementById('transcript-container'),
      transcript: document.getElementById('transcript'),
      micOnIcon: document.getElementById('mic-on-icon'),
      micOffIcon: document.getElementById('mic-off-icon'),
    };
    
    this.initEventListeners();
  }
  
  initEventListeners() {
    this.elements.startBtn.addEventListener('click', () => this.startConversation());
    this.elements.endBtn.addEventListener('click', () => this.endConversation());
    this.elements.muteBtn.addEventListener('click', () => this.toggleMute());
  }
  
  updateStatus(text, connected = false) {
    this.elements.statusText.textContent = text;
    if (connected) {
      this.elements.statusIndicator.classList.add('connected');
    } else {
      this.elements.statusIndicator.classList.remove('connected');
    }
  }
  
  showLoading(show = true) {
    if (show) {
      this.elements.loading.classList.remove('hidden');
    } else {
      this.elements.loading.classList.add('hidden');
    }
  }
  
  addTranscriptMessage(speaker, text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `transcript-message ${speaker.toLowerCase()} fade-in`;
    messageDiv.innerHTML = `
      <div class="speaker">${speaker}</div>
      <div class="text">${text}</div>
    `;
    this.elements.transcript.appendChild(messageDiv);
    this.elements.transcriptContainer.scrollTop = this.elements.transcriptContainer.scrollHeight;
  }
  
  async startConversation() {
    try {
      this.updateStatus('Connecting...');
      this.showLoading(true);
      this.elements.startBtn.disabled = true;
      
      // Get access token from backend
      const response = await fetch(CONFIG.tokenEndpoint);
      
      if (!response.ok) {
        throw new Error(`Failed to get token: ${response.statusText}`);
      }
      
      const data = await response.json();
      const { token, url } = data;
      
      // Create LiveKit room
      this.room = new LiveKit.Room({
        adaptiveStream: true,
        dynacast: true,
        videoCaptureDefaults: {
          resolution: LiveKit.VideoPresets.h720.resolution,
        },
      });
      
      // Set up event handlers
      this.setupRoomHandlers();
      
      // Connect to room
      await this.room.connect(url || CONFIG.livekitUrl, token);
      
      // Enable microphone
      await this.room.localParticipant.setMicrophoneEnabled(true);
      
      // Update UI
      this.isConnected = true;
      this.elements.welcomeScreen.classList.add('hidden');
      this.elements.startBtn.classList.add('hidden');
      this.elements.endBtn.classList.remove('hidden');
      this.elements.muteBtn.classList.remove('hidden');
      this.elements.transcriptContainer.classList.remove('hidden');
      this.showLoading(false);
      this.updateStatus('Connected - Speak to the avatar', true);
      
      console.log('Connected to room:', this.room.name);
      
    } catch (error) {
      console.error('Connection error:', error);
      this.updateStatus('Connection failed. Please try again.');
      this.showLoading(false);
      this.elements.startBtn.disabled = false;
      
      // Show user-friendly error
      alert(`Failed to connect: ${error.message}\n\nPlease check:\n1. Token server is running\n2. LiveKit agent is deployed\n3. Browser has microphone permission`);
    }
  }
  
  setupRoomHandlers() {
    // Handle remote video tracks (avatar video)
    this.room.on(LiveKit.RoomEvent.TrackSubscribed, (track, publication, participant) => {
      console.log('Track subscribed:', track.kind, 'from', participant.identity);
      
      if (track.kind === LiveKit.Track.Kind.Video) {
        // This is the avatar video from the agent
        const videoElement = track.attach();
        videoElement.id = 'avatar-video';
        videoElement.autoplay = true;
        videoElement.playsInline = true;
        
        // Replace placeholder video
        const container = document.getElementById('avatar-container');
        const oldVideo = document.getElementById('avatar-video');
        if (oldVideo) {
          container.replaceChild(videoElement, oldVideo);
        } else {
          container.appendChild(videoElement);
        }
        
        this.elements.avatarVideo = videoElement;
        console.log('Avatar video attached');
      }
    });
    
    // Handle track unsubscribed
    this.room.on(LiveKit.RoomEvent.TrackUnsubscribed, (track, publication, participant) => {
      console.log('Track unsubscribed:', track.kind);
      track.detach();
    });
    
    // Handle participant connected
    this.room.on(LiveKit.RoomEvent.ParticipantConnected, (participant) => {
      console.log('Participant connected:', participant.identity);
      if (participant.identity.includes('agent')) {
        this.updateStatus('Agent joined - Ready to chat', true);
      }
    });
    
    // Handle participant disconnected
    this.room.on(LiveKit.RoomEvent.ParticipantDisconnected, (participant) => {
      console.log('Participant disconnected:', participant.identity);
    });
    
    // Handle disconnection
    this.room.on(LiveKit.RoomEvent.Disconnected, (reason) => {
      console.log('Disconnected from room:', reason);
      this.handleDisconnect();
    });
    
    // Handle connection quality
    this.room.on(LiveKit.RoomEvent.ConnectionQualityChanged, (quality, participant) => {
      console.log('Connection quality:', quality, participant?.identity);
    });
    
    // Handle data received (for transcript, etc.)
    this.room.on(LiveKit.RoomEvent.DataReceived, (payload, participant) => {
      try {
        const data = JSON.parse(new TextDecoder().decode(payload));
        console.log('Data received:', data);
        
        if (data.type === 'transcript') {
          this.addTranscriptMessage(data.speaker, data.text);
        }
      } catch (error) {
        console.error('Error parsing data:', error);
      }
    });
    
    // Handle errors
    this.room.on(LiveKit.RoomEvent.MediaDevicesError, (error) => {
      console.error('Media device error:', error);
      alert('Microphone error. Please check permissions and try again.');
    });
    
    this.room.on(LiveKit.RoomEvent.ConnectionStateChanged, (state) => {
      console.log('Connection state:', state);
      
      if (state === LiveKit.ConnectionState.Reconnecting) {
        this.updateStatus('Reconnecting...');
      } else if (state === LiveKit.ConnectionState.Connected) {
        this.updateStatus('Connected - Speak to the avatar', true);
      }
    });
  }
  
  async endConversation() {
    if (this.room) {
      await this.room.disconnect();
      this.room = null;
    }
    this.handleDisconnect();
  }
  
  handleDisconnect() {
    this.isConnected = false;
    this.isMuted = false;
    
    // Reset UI
    this.elements.welcomeScreen.classList.remove('hidden');
    this.elements.startBtn.classList.remove('hidden');
    this.elements.endBtn.classList.add('hidden');
    this.elements.muteBtn.classList.add('hidden');
    this.elements.startBtn.disabled = false;
    this.showLoading(false);
    this.updateStatus('Ready to connect');
    
    console.log('Disconnected and UI reset');
  }
  
  async toggleMute() {
    if (!this.room) return;
    
    try {
      this.isMuted = !this.isMuted;
      await this.room.localParticipant.setMicrophoneEnabled(!this.isMuted);
      
      // Update UI
      if (this.isMuted) {
        this.elements.micOnIcon.classList.add('hidden');
        this.elements.micOffIcon.classList.remove('hidden');
        this.elements.muteBtn.textContent = 'Unmute';
        this.updateStatus('Microphone muted', true);
      } else {
        this.elements.micOnIcon.classList.remove('hidden');
        this.elements.micOffIcon.classList.add('hidden');
        this.elements.muteBtn.textContent = 'Mute';
        this.updateStatus('Connected - Speak to the avatar', true);
      }
      
      console.log('Microphone', this.isMuted ? 'muted' : 'unmuted');
      
    } catch (error) {
      console.error('Error toggling mute:', error);
    }
  }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  console.log('Initializing Avatar App...');
  
  // Check if LiveKit SDK is loaded
  if (typeof LiveKit === 'undefined') {
    console.error('LiveKit SDK not loaded!');
    alert('Failed to load LiveKit SDK. Please refresh the page.');
    return;
  }
  
  // Check configuration
  if (!CONFIG.tokenEndpoint) {
    console.error('Token endpoint not configured!');
    alert('Configuration error. Please set TOKEN_ENDPOINT in index.html');
    return;
  }
  
  // Create app instance
  window.avatarApp = new AvatarApp();
  console.log('Avatar App initialized');
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
  if (document.hidden && window.avatarApp?.isConnected) {
    console.log('Page hidden - maintaining connection');
  } else if (!document.hidden && window.avatarApp?.isConnected) {
    console.log('Page visible - connection active');
  }
});

// Handle before unload
window.addEventListener('beforeunload', (event) => {
  if (window.avatarApp?.isConnected) {
    window.avatarApp.endConversation();
  }
});
