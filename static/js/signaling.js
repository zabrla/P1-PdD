class SignalingClient {
  /**
   * @param {string} roomName
   * @param {object} handlers - callbacks: onOpen, onClose, onError, onRole,
   *   onPeerJoined, onPeerLeft, onOffer, onAnswer, onIceCandidate,
   *   onChallenge, onHandshakeComplete, onServerError
   */
  constructor(roomName, handlers = {}) {
    this.roomName = roomName;
    this.handlers = handlers;
    this.socket = null;
}

  connect() {
    const scheme = window.location.protocol === "https:" ? "wss" : "ws";
    const url = `${scheme}://${window.location.host}/ws/signaling/${encodeURIComponent(this.roomName)}/`;

    this.socket = new WebSocket(url);

    this.socket.addEventListener("open", () => {
      this.handlers.onOpen?.();
    });

    this.socket.addEventListener("close", (event) => {
      this.handlers.onClose?.(event);
    });

    this.socket.addEventListener("error", (event) => {
      this.handlers.onError?.(event);
    });

    this.socket.addEventListener("message", (event) => {
      let data;
      try {
        data = JSON.parse(event.data);
      } catch (err) {
        console.error("Mensagem WS não é JSON válido:", event.data);
        return;
      }
      this._dispatch(data);
    });
  }

  disconnect() {
    this.socket?.close(1000, "cliente encerrou");
    this.socket = null;
  }

  get isOpen() {
    return this.socket?.readyState === WebSocket.OPEN;
  }

  // envio de mensagens 

  sendOffer(sdp) {
    this._send({ type: "offer", sdp });
  }

  sendAnswer(sdp) {
    this._send({ type: "answer", sdp });
  }

  sendIceCandidate(candidate) {
    this._send({ type: "ice_candidate", candidate });
  }

  sendChallengeResponse(token) {
    this._send({ type: "challenge_response", token });
  }

  ping() {
    this._send({ type: "ping" });
  }

  // internos

  _send(payload) {
    if (!this.isOpen) {
      console.warn("Tentativa de enviar mensagem com WebSocket fechado:", payload);
      return;
    }
    this.socket.send(JSON.stringify(payload));
  }

  _dispatch(data) {
    switch (data.type) {
      case "role":
        this.handlers.onRole?.(data.role);
        break;
      case "peer_joined":
        this.handlers.onPeerJoined?.();
        break;
      case "peer_left":
        this.handlers.onPeerLeft?.();
        break;
      case "offer":
        this.handlers.onOffer?.(data.sdp);
        break;
      case "answer":
        this.handlers.onAnswer?.(data.sdp);
        break;
      case "ice_candidate":
        this.handlers.onIceCandidate?.(data.candidate);
        break;
      case "challenge":
        this.handlers.onChallenge?.(data.token);
        break;
      case "handshake_complete":
        this.handlers.onHandshakeComplete?.();
        break;
      case "error":
        this.handlers.onServerError?.(data.message);
        break;
      case "pong":
        break;
      default:
        console.warn("Tipo de mensagem WS desconhecido:", data);
    }
  }
}
