/* Meeting UI Controller */

document.addEventListener('DOMContentLoaded', () => {
    const stage = document.getElementById('videoStage');
    if (!stage) return; // Not on meeting room page

    const meetingCode = stage.dataset.meetingCode;
    const username = stage.dataset.username;
    const isHost = stage.dataset.isHost === 'true';

    let socket = null;
    let rtcManager = null;

    let cameraEnabled = true;
    let micEnabled = true;
    let screenSharing = false;
    let handRaised = false;

    function initSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        const wsUrl = `${protocol}${window.location.host}/ws/meeting/${meetingCode}/`;
        
        socket = new WebSocket(wsUrl);

        socket.onopen = async () => {
            console.log("WebSocket connected to meeting channel.");
            rtcManager = new WebRTCManager(meetingCode, username, isHost, socket);

            rtcManager.onLocalStream = (stream) => {
                attachLocalStream(stream);
            };

            rtcManager.onRemoteStream = (remoteUsername, stream) => {
                attachRemoteStream(remoteUsername, stream);
            };

            rtcManager.onRemoteStreamRemove = (remoteUsername) => {
                removeRemoteVideoTile(remoteUsername);
            };

            await rtcManager.initLocalMedia(cameraEnabled, micEnabled);
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleSocketAction(data);
        };

        socket.onclose = () => {
            console.log("WebSocket connection closed.");
        };
    }

    function handleSocketAction(data) {
        switch (data.action) {
            case 'participant_joined':
                if (data.username !== username) {
                    addParticipantTile(data.username, data.role, data.state);
                    // Initiate WebRTC offer if we are host or already connected
                    rtcManager.initiateOffer(data.username);
                }
                updateParticipantCount();
                break;

            case 'participant_left':
                rtcManager.removePeerConnection(data.username);
                removeRemoteVideoTile(data.username);
                updateParticipantCount();
                break;

            case 'signal':
                rtcManager.handleSignal(data.sender, data.signal);
                break;

            case 'state_change':
                updateParticipantStateUI(data.username, data.state);
                break;

            case 'chat':
                appendChatMessage(data.id, data.username, data.message, data.timestamp);
                break;

            case 'mute_mic':
                micEnabled = false;
                rtcManager.toggleMicrophone(false);
                document.getElementById('btnMic').classList.remove('active');
                document.getElementById('btnMic').classList.add('off');
                document.getElementById('btnMic').querySelector('i').className = 'fas fa-microphone-slash';
                broadcastState();
                break;

            case 'kicked':
            case 'meeting_ended':
                alert(data.action === 'kicked' ? "You were removed by the host." : "The host has ended the meeting.");
                window.location.href = "/meetings/";
                break;

            case 'approved_entry':
                window.location.reload();
                break;
        }
    }

    function attachLocalStream(stream) {
        const localVideo = document.getElementById('localVideo');
        if (localVideo) {
            localVideo.srcObject = stream;
        }
    }

    function attachRemoteStream(remoteUsername, stream) {
        let tile = document.getElementById(`tile-${remoteUsername}`);
        if (!tile) {
            tile = addParticipantTile(remoteUsername, 'Participant', {});
        }
        let video = tile.querySelector('video');
        if (!video) {
            video = document.createElement('video');
            video.autoplay = true;
            video.playsInline = true;
            tile.appendChild(video);
            tile.querySelector('.avatar-fallback').style.display = 'none';
        }
        video.srcObject = stream;
    }

    function addParticipantTile(participantUsername, role, state) {
        let tile = document.getElementById(`tile-${participantUsername}`);
        if (tile) return tile;

        tile = document.createElement('div');
        tile.className = 'video-tile';
        tile.id = `tile-${participantUsername}`;

        tile.innerHTML = `
            <div class="avatar-fallback">
                <div class="avatar-circle">${participantUsername.charAt(0).toUpperCase()}</div>
                <h6 class="text-white mb-0">${participantUsername}</h6>
            </div>
            <div class="participant-label">
                <span>${participantUsername} ${role === 'Host' ? '(Host)' : ''}</span>
            </div>
            <div class="participant-indicators">
                <div class="status-badge mic-status"><i class="fas fa-microphone"></i></div>
            </div>
        `;

        stage.appendChild(tile);
        updateStageGrid();
        return tile;
    }

    function removeRemoteVideoTile(remoteUsername) {
        const tile = document.getElementById(`tile-${remoteUsername}`);
        if (tile) {
            tile.remove();
            updateStageGrid();
        }
    }

    function updateStageGrid() {
        const count = stage.querySelectorAll('.video-tile').length;
        stage.dataset.participants = Math.min(count, 9);
    }

    function updateParticipantCount() {
        const count = stage.querySelectorAll('.video-tile').length;
        const badge = document.getElementById('participantCountBadge');
        if (badge) badge.textContent = count;
    }

    function updateParticipantStateUI(participantUsername, state) {
        const tile = document.getElementById(`tile-${participantUsername}`);
        if (!tile) return;

        if ('mic' in state) {
            const micBadge = tile.querySelector('.mic-status');
            if (micBadge) {
                if (state.mic) {
                    micBadge.classList.remove('muted');
                    micBadge.querySelector('i').className = 'fas fa-microphone';
                } else {
                    micBadge.classList.add('muted');
                    micBadge.querySelector('i').className = 'fas fa-microphone-slash';
                }
            }
        }
    }

    function broadcastState() {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                action: 'state_change',
                state: {
                    camera: cameraEnabled,
                    mic: micEnabled,
                    screen: screenSharing,
                    hand: handRaised
                }
            }));
        }
    }

    // Controls Event Listeners
    const btnMic = document.getElementById('btnMic');
    if (btnMic) {
        btnMic.addEventListener('click', () => {
            micEnabled = !micEnabled;
            rtcManager.toggleMicrophone(micEnabled);
            btnMic.classList.toggle('active', micEnabled);
            btnMic.classList.toggle('off', !micEnabled);
            btnMic.querySelector('i').className = micEnabled ? 'fas fa-microphone' : 'fas fa-microphone-slash';
            broadcastState();
        });
    }

    const btnCamera = document.getElementById('btnCamera');
    if (btnCamera) {
        btnCamera.addEventListener('click', () => {
            cameraEnabled = !cameraEnabled;
            rtcManager.toggleCamera(cameraEnabled);
            btnCamera.classList.toggle('active', cameraEnabled);
            btnCamera.classList.toggle('off', !cameraEnabled);
            btnCamera.querySelector('i').className = cameraEnabled ? 'fas fa-video' : 'fas fa-video-slash';
            
            const localFallback = document.querySelector('#tile-local .avatar-fallback');
            if (localFallback) localFallback.style.display = cameraEnabled ? 'none' : 'flex';
            broadcastState();
        });
    }

    const btnScreen = document.getElementById('btnScreen');
    if (btnScreen) {
        btnScreen.addEventListener('click', async () => {
            if (!screenSharing) {
                const stream = await rtcManager.startScreenShare();
                if (stream) {
                    screenSharing = true;
                    btnScreen.classList.add('active');
                }
            } else {
                rtcManager.stopScreenShare();
                screenSharing = false;
                btnScreen.classList.remove('active');
            }
            broadcastState();
        });
    }

    const btnHand = document.getElementById('btnHand');
    if (btnHand) {
        btnHand.addEventListener('click', () => {
            handRaised = !handRaised;
            btnHand.classList.toggle('active', handRaised);
            broadcastState();
        });
    }

    const btnEnd = document.getElementById('btnEnd');
    if (btnEnd) {
        btnEnd.addEventListener('click', () => {
            if (confirm("Leave the meeting?")) {
                if (rtcManager) rtcManager.closeAllConnections();
                window.location.href = "/meetings/";
            }
        });
    }

    // Toggle Sidebar Panels
    const btnParticipants = document.getElementById('btnParticipants');
    const btnChat = document.getElementById('btnChat');
    const sidebar = document.getElementById('meetingSidebar');
    const participantsPanel = document.getElementById('participantsPanel');
    const chatPanel = document.getElementById('chatPanel');

    if (btnParticipants) {
        btnParticipants.addEventListener('click', () => {
            sidebar.classList.remove('hidden');
            participantsPanel.style.display = 'block';
            chatPanel.style.display = 'none';
        });
    }

    if (btnChat) {
        btnChat.addEventListener('click', () => {
            sidebar.classList.remove('hidden');
            participantsPanel.style.display = 'none';
            chatPanel.style.display = 'block';
        });
    }

    const btnCloseSidebar = document.getElementById('btnCloseSidebar');
    if (btnCloseSidebar) {
        btnCloseSidebar.addEventListener('click', () => {
            sidebar.classList.add('hidden');
        });
    }

    // Send Chat Message
    const chatForm = document.getElementById('meetingChatForm');
    if (chatForm) {
        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const input = document.getElementById('meetingChatInput');
            const msg = input.value.trim();
            if (msg && socket) {
                socket.send(JSON.stringify({
                    action: 'chat',
                    message: msg
                }));
                input.value = '';
            }
        });
    }

    function appendChatMessage(id, senderUsername, messageText, timestamp) {
        const container = document.getElementById('chatMessagesContainer');
        if (!container) return;

        const isOwn = senderUsername === username;
        const timeStr = new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        const bubble = document.createElement('div');
        bubble.className = `chat-bubble ${isOwn ? 'own' : ''}`;
        bubble.innerHTML = `
            <div class="chat-bubble-sender">${senderUsername} • ${timeStr}</div>
            <div>${escapeHtml(messageText)}</div>
        `;
        container.appendChild(bubble);
        container.scrollTop = container.scrollHeight;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Initialize meeting connection
    initSocket();
});
