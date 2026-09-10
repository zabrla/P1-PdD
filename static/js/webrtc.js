(function () {
  const els = {
    room: document.getElementById("room"),
    connectBtn: document.getElementById("connectBtn"),
    disconnectBtn: document.getElementById("disconnectBtn"),
    statusWs: document.getElementById("statusWs"),
    statusRole: document.getElementById("statusRole"),
    statusRtc: document.getElementById("statusRtc"),
    statusHandshake: document.getElementById("statusHandshake"),
    log: document.getElementById("log"),
  };

  const ICE_SERVERS = window.__ICE_SERVERS__ || [
    {
      urls: ["stun:stun.l.google.com:19302"],
    },
  ];

  let signaling = null;
  let pc = null;
  let dataChannel = null;
  let role = null;
  let pendingChallengeToken = null;

  function log(message, kind = "info") {
    const line = document.createElement("div");
    const time = new Date().toLocaleTimeString();

    const prefix = {
      info: "•",
      ok: "✅",
      warn: "⚠️",
      err: "❌",
    }[kind] || "•";

    line.textContent = `[${time}] ${prefix} ${message}`;

    els.log.appendChild(line);
    els.log.scrollTop = els.log.scrollHeight;
  }

  function setBadge(el, text, cls) {
    el.textContent = text;
    el.className = `value ${cls}`;
  }

  function resetUi() {
    setBadge(els.statusWs, "desconectado", "idle");
    setBadge(els.statusRole, "—", "idle");
    setBadge(els.statusRtc, "—", "idle");
    setBadge(els.statusHandshake, "pendente", "idle");

    els.connectBtn.disabled = false;
    els.disconnectBtn.disabled = true;
  }

  // RTCPeerConnection

  function createPeerConnection() {
    const connection = new RTCPeerConnection({iceServers: ICE_SERVERS,});

    connection.addEventListener("icecandidate", (event) => {
      if (event.candidate) {signaling.sendIceCandidate(event.candidate.toJSON());}
    });

    connection.addEventListener("connectionstatechange", () => {
      log(`Estado da conexão WebRTC: ${connection.connectionState}`);

      const map = {
        new: ["novo", "idle"],
        connecting: ["conectando…", "warn"],
        connected: ["conectado", "ok"],
        disconnected: ["desconectado", "warn"],
        failed: ["falhou", "err"],
        closed: ["fechado", "idle"],
      };

      const [text, cls] =
        map[connection.connectionState] ||
        [connection.connectionState, "idle"];

      setBadge(els.statusRtc, text, cls);

      if (connection.connectionState === "failed") {
        log("Conexão P2P direta falhou. Verifique se um servidor TURN está configurado.","err");}
    });

    connection.addEventListener("datachannel", (event) => {
      attachDataChannel(event.channel);
    });

    return connection;
  }

  // DataChannel

  function attachDataChannel(channel) {
    dataChannel = channel;

    dataChannel.addEventListener("open", () => {
      log("DataChannel aberto.", "ok");
      onDataChannelOpen();
    });

    dataChannel.addEventListener("close", () => {
      log("DataChannel fechado.", "warn");
    });

    dataChannel.addEventListener("message", (event) => {
      handleDataChannelMessage(event.data);
    });
  }

  function onDataChannelOpen() {
    if (role === "initiator" && pendingChallengeToken) {
      dataChannel.send(
        JSON.stringify({ kind: "handshake_challenge", token: pendingChallengeToken,})
      );
      log("Token de desafio enviado ao peer via DataChannel.");
    }
  }

  function handleDataChannelMessage(raw) {
    let data;
    try {
      data = JSON.parse(raw);
    } catch {
      log("Mensagem recebida pelo DataChannel não possui formato esperado.", "warn");
      
      return;
    }

    if (data.kind === "handshake_challenge") {
      log("Token de desafio recebido via DataChannel P2P.");
      signaling.sendChallengeResponse(data.token);
      
      return;
    }

    log(`Mensagem desconhecida recebida pelo DataChannel: ${data.kind}`, "warn");
  }

  // Sinalização

  async function startAsInitiator() {

    dataChannel = pc.createDataChannel("handshake");

    attachDataChannel(dataChannel);

    const offer = await pc.createOffer();

    await pc.setLocalDescription(offer);

    signaling.sendOffer(pc.localDescription.sdp);

    log("Offer SDP criada e enviada.");
  }

  async function handleRemoteOffer(sdp) {
    await pc.setRemoteDescription({type: "offer", sdp,});

    const answer = await pc.createAnswer();

    await pc.setLocalDescription(answer);

    signaling.sendAnswer(pc.localDescription.sdp);

    log("Answer SDP criada e enviada.");
  }

  async function handleRemoteAnswer(sdp) {
    await pc.setRemoteDescription({type: "answer",sdp,});

    log("Answer remota aplicada.");
  }

  async function handleRemoteIceCandidate(candidate) {
    try {
      await pc.addIceCandidate(candidate);
    } catch (err) {
      log(`Falha ao adicionar ICE candidate: ${err}`, "err");
    }
  }

  // Conexão

  function connect() {
    const roomName = els.room.value.trim();

    if (!roomName) {
      log("Informe um código de sala.", "err");
      return;
    }

    els.connectBtn.disabled = true;

    signaling = new SignalingClient(roomName, {
      onOpen: () => {
        setBadge(els.statusWs, "conectado", "ok");
        log("WebSocket de sinalização conectado.", "ok");

        els.disconnectBtn.disabled = false;
      },

      onClose: () => {
        setBadge(els.statusWs, "desconectado", "idle");
        log("WebSocket de sinalização desconectado.");
      },

      onError: () => {
        log("Erro na conexão WebSocket.", "err");
      },

      onServerError: (message) => {
        log(`Erro do servidor: ${message}`, "err");
      },

      onRole: (assignedRole) => {
        role = assignedRole;

        setBadge(els.statusRole, role, "ok");

        log(`Papel atribuído pelo servidor: ${role}`);

        pc = createPeerConnection();
      },

      onPeerJoined: async () => {
        log("O outro peer entrou na sala.", "ok");

        if (role === "initiator") {
          await startAsInitiator();
        }
      },

      onPeerLeft: () => {
        log("O outro peer saiu da sala.", "warn");

        setBadge(els.statusRtc, "peer saiu", "warn");
        setBadge(els.statusHandshake, "pendente", "idle");
      },

      onOffer: (sdp) => handleRemoteOffer(sdp),

      onAnswer: (sdp) => handleRemoteAnswer(sdp),

      onIceCandidate: (candidate) =>
        handleRemoteIceCandidate(candidate),

      onChallenge: (token) => {
        pendingChallengeToken = token;

        log("Desafio de validação recebido do servidor (será repassado via P2P).");

        if (dataChannel && dataChannel.readyState === "open") {
          onDataChannelOpen();
        }
      },

      onHandshakeComplete: () => {
        setBadge(els.statusHandshake, "validado ✔", "ok");

        log(
          "Handshake P2P validado com sucesso pelo servidor!",
          "ok"
        );
      },
    });

    signaling.connect();
  }

  function disconnect() {
    dataChannel?.close();
    pc?.close();
    signaling?.disconnect();

    dataChannel = null;
    pc = null;
    signaling = null;
    role = null;
    pendingChallengeToken = null;

    resetUi();

    log("Desconectado.");
  }

  // UI

  els.connectBtn.addEventListener("click", connect);
  els.disconnectBtn.addEventListener("click", disconnect);

  resetUi();
})();