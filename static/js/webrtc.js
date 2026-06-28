/* WebRTC Signaling and Stream Engine */

class WebRTCManager {
    constructor(meetingCode, username, isHost, socket) {
        this.meetingCode = meetingCode;
        this.username = username;
        this.isHost = isHost;
        this.socket = socket;
        
        this.localStream = null;
        this.screenStream = null;
        this.peerConnections = {}; // { username: RTCPeerConnection }
        
        this.iceServers = {
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' },
                { urls: 'stun:stun2.l.google.com:19302' }
            ]
        };

        this.onLocalStream = null;
        this.onRemoteStream = null;
        this.onRemoteStreamRemove = null;
    }

    async initLocalMedia(video = true, audio = true) {
        try {
            this.localStream = await navigator.mediaDevices.getUserMedia({
                video: video ? { width: { ideal: 1280 }, height: { ideal: 720 } } : false,
                audio: audio ? { echoCancellation: true, noiseSuppression: true } : false
            });
            if (this.onLocalStream) this.onLocalStream(this.localStream);
            return true;
        } catch (err) {
            console.error("Failed to acquire local media devices:", err);
            return false;
        }
    }

    createPeerConnection(targetUsername) {
        if (this.peerConnections[targetUsername]) {
            return this.peerConnections[targetUsername];
        }

        const pc = new RTCPeerConnection(this.iceServers);

        // Add local tracks to peer connection
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => {
                pc.addTrack(track, this.localStream);
            });
        }

        // ICE Candidate handler
        pc.onicecandidate = (event) => {
            if (event.candidate) {
                this.socket.send(JSON.stringify({
                    action: 'signal',
                    target: targetUsername,
                    signal: { candidate: event.candidate }
                }));
            }
        };

        // Track receiver handler
        pc.ontrack = (event) => {
            if (this.onRemoteStream) {
                this.onRemoteStream(targetUsername, event.streams[0]);
            }
        };

        pc.oniceconnectionstatechange = () => {
            if (pc.iceConnectionState === 'disconnected' || pc.iceConnectionState === 'failed' || pc.iceConnectionState === 'closed') {
                this.removePeerConnection(targetUsername);
            }
        };

        this.peerConnections[targetUsername] = pc;
        return pc;
    }

    async initiateOffer(targetUsername) {
        const pc = this.createPeerConnection(targetUsername);
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);

        this.socket.send(JSON.stringify({
            action: 'signal',
            target: targetUsername,
            signal: { sdp: pc.localDescription }
        }));
    }

    async handleSignal(senderUsername, signal) {
        const pc = this.createPeerConnection(senderUsername);

        if (signal.sdp) {
            await pc.setRemoteDescription(new RTCSessionDescription(signal.sdp));

            if (signal.sdp.type === 'offer') {
                const answer = await pc.createAnswer();
                await pc.setLocalDescription(answer);

                this.socket.send(JSON.stringify({
                    action: 'signal',
                    target: senderUsername,
                    signal: { sdp: pc.localDescription }
                }));
            }
        } else if (signal.candidate) {
            try {
                await pc.addIceCandidate(new RTCIceCandidate(signal.candidate));
            } catch (e) {
                console.error("Error adding received ICE candidate:", e);
            }
        }
    }

    removePeerConnection(targetUsername) {
        if (this.peerConnections[targetUsername]) {
            this.peerConnections[targetUsername].close();
            delete this.peerConnections[targetUsername];
            if (this.onRemoteStreamRemove) {
                this.onRemoteStreamRemove(targetUsername);
            }
        }
    }

    toggleCamera(enabled) {
        if (this.localStream) {
            const videoTracks = this.localStream.getVideoTracks();
            videoTracks.forEach(track => track.enabled = enabled);
        }
    }

    toggleMicrophone(enabled) {
        if (this.localStream) {
            const audioTracks = this.localStream.getAudioTracks();
            audioTracks.forEach(track => track.enabled = enabled);
        }
    }

    async startScreenShare() {
        try {
            this.screenStream = await navigator.mediaDevices.getDisplayMedia({
                video: true,
                audio: true
            });

            const screenTrack = this.screenStream.getVideoTracks()[0];

            // Replace video track for all connected peers
            for (let target in this.peerConnections) {
                const pc = this.peerConnections[target];
                const senders = pc.getSenders();
                const sender = senders.find(s => s.track && s.track.kind === 'video');
                if (sender) {
                    sender.replaceTrack(screenTrack);
                }
            }

            screenTrack.onended = () => {
                this.stopScreenShare();
            };

            return this.screenStream;
        } catch (err) {
            console.error("Screen share canceled or failed:", err);
            return null;
        }
    }

    stopScreenShare() {
        if (this.screenStream) {
            this.screenStream.getTracks().forEach(track => track.stop());
            this.screenStream = null;
        }

        if (this.localStream) {
            const videoTrack = this.localStream.getVideoTracks()[0];
            for (let target in this.peerConnections) {
                const pc = this.peerConnections[target];
                const senders = pc.getSenders();
                const sender = senders.find(s => s.track && s.track.kind === 'video');
                if (sender && videoTrack) {
                    sender.replaceTrack(videoTrack);
                }
            }
        }
    }

    closeAllConnections() {
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => track.stop());
        }
        if (this.screenStream) {
            this.screenStream.getTracks().forEach(track => track.stop());
        }
        for (let target in this.peerConnections) {
            this.peerConnections[target].close();
        }
        this.peerConnections = {};
    }
}
