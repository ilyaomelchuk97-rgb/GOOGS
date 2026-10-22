/* Forma calls: server-authorized invitations; LiveKit SFU when configured, small P2P mesh otherwise. */
let callActive=null,callPollBusy=false,callKnown=new Set(),callUserId=null;
const callRoot=document.createElement('div');callRoot.id='call-root';document.body.append(callRoot);
function callRoom(room){return room==='general'||room.startsWith('group:')?room:'dm:'+String(Math.min(Number(room),S.user.id))+':'+String(Math.max(Number(room),S.user.id))}
function callLabel(room){if(room==='general')return 'Общий чат';if(room.startsWith('group:'))return S.groups?.find(x=>'group:'+x.id===room)?.title||'Закрытая беседа';return S.chatData?.users?.find(x=>String(x.id)===room.split(':').find(n=>Number(n)!==S.user.id))?.name||'Личный чат'}
function callInvitation(call){
 const box=document.createElement('div');box.className='call-invitation';box.dataset.callId=call.id;
 const title=document.createElement('b');title.textContent='Приглашение на звонок · '+callLabel(call.room);
 const sub=document.createElement('span');sub.textContent=call.mode==='p2p'?'Резервный P2P: не более 4 человек; без TURN связь через некоторые сети невозможна.':'LiveKit · до 15 человек';
 const join=document.createElement('button');join.type='button';join.className='btn primary';join.textContent='Присоединиться';join.onclick=()=>joinCall(call);
 const close=document.createElement('button');close.type='button';close.className='btn secondary';close.textContent='Скрыть';close.onclick=()=>box.remove();
 box.append(title,sub,join,close);callRoot.append(box);
}
async function refreshCalls(){
 if(!S.user||callPollBusy||document.hidden)return;
 if(callUserId!==S.user.id){callKnown.clear();callUserId=S.user.id;for(const box of callRoot.querySelectorAll('.call-invitation'))box.remove()}
 callPollBusy=true;
 try{
  const result=await api('/api/calls');S.calls=result.calls||[];
  const live=new Set(S.calls.map(c=>c.id));
  if(callActive&&!live.has(callActive.id))await leaveCall(false);
  for(const box of callRoot.querySelectorAll('.call-invitation'))if(!live.has(Number(box.dataset.callId)))box.remove();
  for(const c of S.calls){
   if(!callKnown.has(c.id)&&(!callActive||callActive.id!==c.id))callInvitation(c);
   callKnown.add(c.id);
  }
 }catch(e){console.warn('Приглашения временно недоступны',e.message)}finally{callPollBusy=false}
}
function callVideoStatus(text){
 const note=callRoot.querySelector('.call-media-status');if(note){note.textContent=text;note.hidden=!text}
}
function frameMediaBlocked(){
 try{return window.self!==window.top&&(['camera','microphone'].some(feature=>
  (document.permissionsPolicy||document.featurePolicy)?.allowsFeature(feature)===false))}catch{return false}
}
function callTile(id,label,media,muted=false){
 const grid=callRoot.querySelector('.call-tiles');if(!grid)return;
 let tile=[...grid.children].find(n=>n.dataset.tile===id);
 if(!tile){tile=document.createElement('div');tile.dataset.tile=id;tile.className='call-tile';
  const caption=document.createElement('strong');caption.textContent=label;tile.append(caption);grid.append(tile)}
 const stream=media instanceof MediaStream?media:media instanceof MediaStreamTrack?new MediaStream([media]):null;
 const status=tile.querySelector('.call-tile-status')||document.createElement('span');
 status.className='call-tile-status';if(!status.isConnected)tile.append(status);
 if(!stream){if(!tile.querySelector('video'))status.textContent='Подключён · ожидаем видео';return}
 const video=stream.getVideoTracks();
 if(!video.length){
  status.textContent='Камера выключена или недоступна';
  const audio=stream.getAudioTracks();
  if(audio.length){let speaker=tile.querySelector('audio');if(!speaker){speaker=document.createElement('audio');speaker.autoplay=true;tile.prepend(speaker)}
   speaker.srcObject=stream;speaker.play().catch(()=>{speaker.controls=true;status.textContent='Нажмите ▶ для воспроизведения звука'})}
  return
 }
 status.textContent='';tile.querySelector('audio')?.remove();
 let player=tile.querySelector('video');if(!player){player=document.createElement('video');player.autoplay=true;player.playsInline=true;player.muted=muted;tile.prepend(player)}
 player.srcObject=stream;
 player.play().then(()=>{if(player.isConnected)player.controls=false}).catch(()=>{
  player.controls=true;status.textContent='Нажмите ▶ для воспроизведения видео и звука';
 });
}
function removeCallTile(id){const grid=callRoot.querySelector('.call-tiles');if(grid)for(const el of grid.children)if(el.dataset.tile===id)el.remove()}
function updateCallExpand(panel){
 const button=panel.querySelector('[data-call="expand"]');if(!button)return;
 const expanded=document.fullscreenElement===panel||panel.classList.contains('is-maximized');
 button.textContent=expanded?'⛶ Свернуть':'⛶ На весь экран';
 button.setAttribute('aria-label',expanded?'Свернуть видеозвонок':'Развернуть видеозвонок на весь экран');
}
async function toggleCallExpand(){
 const panel=callRoot.querySelector('.call-panel');if(!panel)return;
 if(document.fullscreenElement===panel){await document.exitFullscreen();return}
 if(panel.classList.contains('is-maximized')){panel.classList.remove('is-maximized');updateCallExpand(panel);return}
 if(panel.requestFullscreen)try{await panel.requestFullscreen();updateCallExpand(panel);return}catch{}
 // A sandboxed iframe may deny the native Fullscreen API. Maximize inside it.
 panel.classList.add('is-maximized');updateCallExpand(panel)
}
function initCallDragging(panel){
 const header=panel.querySelector('.call-handle');if(!header)return;
 header.addEventListener('pointerdown',event=>{
  if(event.button!==0||event.target.closest('button,select,input,label')||panel.classList.contains('is-maximized')||document.fullscreenElement===panel)return;
  const rect=panel.getBoundingClientRect(),x=event.clientX-rect.left,y=event.clientY-rect.top;
  panel.classList.add('is-dragging');panel.style.left=rect.left+'px';panel.style.top=rect.top+'px';
  panel.style.right='auto';panel.style.bottom='auto';
  const move=e=>{
   panel.style.left=Math.max(0,Math.min(window.innerWidth-rect.width,e.clientX-x))+'px';
   panel.style.top=Math.max(0,Math.min(window.innerHeight-rect.height,e.clientY-y))+'px';
  };
  const finish=()=>{panel.classList.remove('is-dragging');window.removeEventListener('pointermove',move);window.removeEventListener('pointerup',finish);window.removeEventListener('pointercancel',finish)};
  window.addEventListener('pointermove',move);window.addEventListener('pointerup',finish,{once:true});window.addEventListener('pointercancel',finish,{once:true});
  event.preventDefault();
 });
}
document.addEventListener('fullscreenchange',()=>{const panel=callRoot.querySelector('.call-panel');if(panel)updateCallExpand(panel)});
function renderCallPanel(call){
 callRoot.querySelector('.call-panel')?.remove();
 const panel=document.createElement('section');panel.className='call-panel';panel.setAttribute('aria-label','Видеозвонок');
 panel.innerHTML=`<header class="call-handle" title="Перетащите окно за заголовок"><strong>Видеозвонок · ${esc(callLabel(call.room))}</strong><span class="call-mode"></span><button class="btn secondary" data-call="expand" type="button" aria-label="Развернуть видеозвонок на весь экран">⛶ На весь экран</button><button class="btn secondary" data-call="leave" type="button">Выйти</button></header><div class="call-tiles"></div><footer><button class="btn secondary" data-call="mic" type="button">Микрофон</button><button class="btn secondary" data-call="camera" type="button">Камера</button><label>Камера <select class="call-camera-select" aria-label="Выбор камеры"></select></label><button class="btn secondary" data-call="screen" type="button">Показать экран / окно / вкладку</button></footer><p class="call-media-status" role="status" hidden></p><p class="call-note"></p>`;
 panel.querySelector('.call-mode').textContent=call.mode==='p2p'?'P2P · максимум 4':'LiveKit · максимум 15';
 panel.querySelector('.call-note').textContent=call.mode==='p2p'?'P2P без TURN: соединение может не состояться за NAT; для большой группы настройте LiveKit Cloud. Запись не ведётся.':'Запись не ведётся. Экран, окно или вкладку выбираете в диалоге браузера.';
 callRoot.append(panel);callTile('self','Вы',call.local,true);
 const missing=[];if(!call.local.getVideoTracks().length)missing.push('камера');if(!call.local.getAudioTracks().length)missing.push('микрофон');
 if(missing.length)callVideoStatus('Вы подключились без '+missing.join(' и ')+'. Собеседник не увидит ваше видео, если камера не разрешена. Для предпросмотра откройте сайт отдельно в новой вкладке браузера.');
 initCallDragging(panel);
}
async function cameraList(){
 if(!callActive)return;
 const select=callRoot.querySelector('.call-camera-select');if(!select)return;
 const devices=(await navigator.mediaDevices.enumerateDevices()).filter(d=>d.kind==='videoinput');
 select.replaceChildren();for(const [i,d] of devices.entries()){
  const option=document.createElement('option');option.value=d.deviceId;option.textContent=d.label||'Камера '+(i+1);select.append(option)
 }
 const current=callActive.local.getVideoTracks()[0]?.getSettings().deviceId;if(current)select.value=current;
}
async function joinCall(invitation){
 if(callActive){notify('Сначала выйдите из текущего звонка',true);return false}
 if(!navigator.mediaDevices?.getUserMedia){notify('Камера и микрофон недоступны: откройте предпросмотр отдельной вкладкой HTTPS и разрешите устройства',true);return false}
 // Media permission is requested only after an explicit click on Join.
 let local;
 try{local=await navigator.mediaDevices.getUserMedia({audio:true,video:true})}
 catch(firstError){try{local=await navigator.mediaDevices.getUserMedia({audio:true,video:false});
   notify('Камера не разрешена: собеседник не увидит ваше видео. Проверьте разрешения браузера.',true)}
  catch{try{local=await navigator.mediaDevices.getUserMedia({audio:false,video:true});
    notify('Микрофон не разрешён: собеседник не услышит вас.',true)}
   catch{
    const reason=frameMediaBlocked()?'Предпросмотр запрещает доступ к камере и микрофону. Откройте сайт в отдельной вкладке по HTTPS.':
      'Браузер не дал доступ к камере и микрофону ('+firstError.name+'). Проверьте разрешения сайта и устройства.';
    if(!confirm(reason+'\nПодключиться только для просмотра, без изображения и звука с вашей стороны?'))return false;
    local=new MediaStream()
   }}}

 let joined;
 try{joined=await api('/api/calls/join','POST',{id:invitation.id})}
 catch(e){local.getTracks().forEach(t=>t.stop());notify(e.message,true);return false}
 const call={...joined,id:invitation.id,local,pcs:new Map(),peers:new Map(),cursor:0,pendingSignals:[],roomConnection:null,screen:null,busy:false,lastHeartbeat:0,peersState:[]};
 callActive=call;for(const box of callRoot.querySelectorAll('.call-invitation'))if(Number(box.dataset.callId)===call.id)box.remove();
 renderCallPanel(call);
 try{
  if(call.mode==='livekit'){call.connecting=true;await livekitConnect(call);call.connecting=false;}
  await cameraList();
  call.timer=setInterval(()=>callTick(call),2000);await callTick(call);
 }catch(e){
  if(call.mode==='livekit'&&confirm('LiveKit недоступен: '+e.message+'. Перейти на прямой P2P (до 4 человек, без TURN и без гарантии связи за NAT)?')){
   try{await api('/api/calls/fallback','POST',{id:call.id,connection:call.connection});
    call.mode='p2p';call.roomConnection?.disconnect();call.roomConnection=null;
    callRoot.querySelector('.call-mode').textContent='P2P · максимум 4';
    callRoot.querySelector('.call-note').textContent='Резервный P2P без TURN: связь за некоторыми NAT может не работать. Запись не ведётся.';
    await cameraList();call.timer=setInterval(()=>callTick(call),2000);await callTick(call);return true
   }catch(fallbackError){notify('Переход на P2P не выполнен: '+fallbackError.message,true)}
  }else notify('Не удалось подключиться: '+e.message,true);
  await leaveCall();return false
 }
 return true;
}
async function livekitConnect(call){
 if(!window.LivekitClient?.Room)throw Error('SDK LiveKit не загружен');
 const kit=window.LivekitClient,room=new kit.Room({adaptiveStream:true,dynacast:true});call.roomConnection=room;
 room.on(kit.RoomEvent.ParticipantConnected,person=>callTile(person.identity,person.name||'Участник',null));
 room.on(kit.RoomEvent.ParticipantDisconnected,person=>removeCallTile(person.identity));
 room.on(kit.RoomEvent.TrackSubscribed,(track,pub,person)=>{if(track.kind==='video')callTile(person.identity,person.name||'Участник',track.mediaStreamTrack);else if(track.kind==='audio'){
  const audio=track.attach();audio.dataset.audio=person.identity+':'+track.sid;callRoot.querySelector('.call-panel')?.append(audio)}
 });
 room.on(kit.RoomEvent.TrackUnsubscribed,(track,pub,person)=>{
  if(track.kind==='video'){const tile=callRoot.querySelector('.call-tile[data-tile="'+person.identity+'"]');tile?.querySelector('video')?.remove();callTile(person.identity,person.name||'Участник',null)}
  else callRoot.querySelectorAll('audio[data-audio]').forEach(a=>{if(a.dataset.audio===person.identity+':'+track.sid)a.remove()})
 });
 room.on(kit.RoomEvent.Disconnected,()=>{if(callActive===call&&call.mode==='livekit'&&!call.connecting)leaveCall(true)});
 await room.connect(call.url,call.token);
 for(const person of room.remoteParticipants.values())callTile(person.identity,person.name||'Участник',null);
 for(const track of call.local.getTracks())await room.localParticipant.publishTrack(track,{source:track.kind==='video'?kit.Track.Source.Camera:kit.Track.Source.Microphone});
}
async function sendSignal(call,target,signal){await api('/api/calls/signals','POST',{id:call.id,connection:call.connection,target,signal})}
function peerConnection(call,peer){
 if(call.pcs.has(peer.connection))return call.pcs.get(peer.connection);
 const pc=new RTCPeerConnection({iceServers:[{urls:'stun:stun.l.google.com:19302'}]});call.pcs.set(peer.connection,pc);
 for(const track of call.local.getTracks())pc.addTrack(track,call.local);
 if(call.screen)for(const track of call.screen.getTracks())pc.addTrack(track,call.screen);
 pc.ontrack=e=>callTile(peer.connection,e.track.kind==='video'?peer.name:peer.name,e.streams[0]||e.track);
 pc.onconnectionstatechange=()=>{
  if(pc.connectionState==='failed'||pc.connectionState==='disconnected'){
   const tile=callRoot.querySelector('.call-tile[data-tile="'+peer.connection+'"]');
   if(tile&&!tile.querySelector('video'))tile.querySelector('.call-tile-status').textContent='P2P-соединение не установлено. Откройте сайт в отдельной вкладке; для сложных сетей настройте LiveKit.';
  }
 };
 pc.onicecandidate=e=>{if(e.candidate)sendSignal(call,peer.connection,{type:'candidate',candidate:e.candidate.toJSON()}).catch(console.warn)};
 pc.pendingCandidates=[];pc.makingOffer=false;pc.ignoreOffer=false;
 pc.onnegotiationneeded=async()=>{try{pc.makingOffer=true;await pc.setLocalDescription();await sendSignal(call,peer.connection,{type:'offer',sdp:pc.localDescription})}catch(e){console.warn('P2P negotiation',e)}finally{pc.makingOffer=false}};
 return pc;
}
async function callTick(call){
 if(callActive!==call||call.busy)return;call.busy=true;
 try{
  if(!call.lastHeartbeat||Date.now()-call.lastHeartbeat>8000||(call.mode==='p2p'&&call.pendingSignals.length)){
   const state=await api('/api/calls/heartbeat','POST',{id:call.id,connection:call.connection});
   call.lastHeartbeat=Date.now();call.peersState=state.peers;
  }
  if(call.mode==='p2p'){
   const available=new Set(call.peersState.map(x=>x.connection));
   for(const [id,pc] of call.pcs)if(!available.has(id)){pc.close();call.pcs.delete(id);call.peers.delete(id);removeCallTile(id)}
   for(const peer of call.peersState){call.peers.set(peer.connection,peer);callTile(peer.connection,peer.name,null);peerConnection(call,peer)}
   const result=await api(`/api/calls/signals?id=${call.id}&connection=${call.connection}&after=${call.cursor}`);
   const incoming=[...call.pendingSignals,...result.signals];call.pendingSignals=[];
   for(const entry of incoming){call.cursor=Math.max(call.cursor,entry.id);const peer=call.peers.get(entry.sender);
    if(!peer){if(call.pendingSignals.length<100)call.pendingSignals.push(entry);continue}
    const pc=peerConnection(call,peer),s=entry.signal;
    try{if(s.type==='offer'){const collision=pc.makingOffer||pc.signalingState!=='stable';pc.ignoreOffer=call.connection<entry.sender&&collision;if(pc.ignoreOffer)continue;
      if(collision)await pc.setLocalDescription({type:'rollback'});await pc.setRemoteDescription(s.sdp);
      for(const ice of pc.pendingCandidates.splice(0))await pc.addIceCandidate(ice);
      await pc.setLocalDescription();await sendSignal(call,entry.sender,{type:'answer',sdp:pc.localDescription})}
     else if(s.type==='answer'&&pc.signalingState==='have-local-offer'){await pc.setRemoteDescription(s.sdp);pc.ignoreOffer=false;for(const ice of pc.pendingCandidates.splice(0))await pc.addIceCandidate(ice)}
     else if(s.type==='candidate'&&!pc.ignoreOffer){if(pc.remoteDescription)await pc.addIceCandidate(s.candidate);else pc.pendingCandidates.push(s.candidate)}
    }catch(e){console.warn('P2P signal',e)}
   }
  }
 }catch(e){notify('Звонок завершён или доступ отозван: '+e.message,true);await leaveCall(false)}finally{call.busy=false}
}
async function leaveCall(send=true){
 const call=callActive;if(!call)return;callActive=null;clearInterval(call.timer);
 call.roomConnection?.disconnect();for(const pc of call.pcs.values())pc.close();
 call.local.getTracks().forEach(t=>t.stop());call.screen?.getTracks().forEach(t=>t.stop());
 callRoot.querySelector('.call-panel')?.remove();
 if(send)try{await api('/api/calls/leave','POST',{id:call.id,connection:call.connection})}catch(e){console.warn('Leave call',e.message)}
}
async function replaceCamera(){
 const call=callActive;if(!call)return;
 const deviceId=callRoot.querySelector('.call-camera-select')?.value;
 try{const stream=await navigator.mediaDevices.getUserMedia({video:deviceId?{deviceId:{exact:deviceId}}:true,audio:false});
  const track=stream.getVideoTracks()[0],old=call.local.getVideoTracks()[0];
  if(call.mode==='livekit'){const participant=call.roomConnection.localParticipant;
   if(old){const publication=participant.getTrackPublication(window.LivekitClient.Track.Source.Camera);if(publication)await participant.unpublishTrack(old)}
   await participant.publishTrack(track,{source:window.LivekitClient.Track.Source.Camera});
  }else for(const pc of call.pcs.values()){
   const sender=pc.getSenders().find(s=>s.track===old);
   if(sender)await sender.replaceTrack(track);else pc.addTrack(track,call.local);
  }
  if(old){call.local.removeTrack(old);old.stop()}call.local.addTrack(track);callTile('self','Вы',call.local,true);await cameraList();
 }catch(e){notify('Камера недоступна: '+e.message,true)}
}
async function shareScreen(){
 const call=callActive;if(!call)return;
 if(call.screen){call.screen.getTracks().forEach(t=>t.stop());return}
 try{const screen=await navigator.mediaDevices.getDisplayMedia({video:true,audio:false});if(callActive!==call){screen.getTracks().forEach(t=>t.stop());return}
  call.screen=screen;const track=screen.getVideoTracks()[0];
  if(call.mode==='livekit')await call.roomConnection.localParticipant.publishTrack(track,{source:window.LivekitClient.Track.Source.ScreenShare});
  else for(const pc of call.pcs.values())pc.addTrack(track,screen);
  callTile('screen','Ваш экран',screen,true);
  track.onended=async()=>{if(call.screen!==screen)return;call.screen=null;
   if(call.mode==='livekit')try{await call.roomConnection.localParticipant.unpublishTrack(track)}catch{};
   for(const pc of call.pcs.values())for(const sender of pc.getSenders())if(sender.track===track)pc.removeTrack(sender);
   removeCallTile('screen');};
 }catch(e){notify('Показ экрана не начался: '+e.message,true)}
}
document.addEventListener('click',async e=>{
 const start=e.target.closest('[data-action="call-start"]');if(start){
  try{const result=await api('/api/calls','POST',{room:S.chatRoom});await refreshCalls();const joined=await joinCall({...result,room:callRoom(S.chatRoom)});
   if(!joined&&!result.existing)try{await api('/api/calls/cancel','POST',{id:result.id})}catch{}}catch(err){notify(err.message,true)}return
 }
 const btn=e.target.closest('[data-call]');if(!btn||!callActive)return;
 const call=callActive;
 if(btn.dataset.call==='leave')await leaveCall();
 if(btn.dataset.call==='expand')await toggleCallExpand();
 if(btn.dataset.call==='mic'){const t=call.local.getAudioTracks()[0];if(t){t.enabled=!t.enabled;btn.textContent=t.enabled?'Микрофон':'Микрофон выключен'}}
 if(btn.dataset.call==='camera'){const t=call.local.getVideoTracks()[0];if(t){t.enabled=!t.enabled;btn.textContent=t.enabled?'Камера':'Камера выключена'}else await replaceCamera()}
 if(btn.dataset.call==='screen')await shareScreen();
});
document.addEventListener('change',e=>{if(e.target.matches('.call-camera-select'))replaceCamera()});
window.addEventListener('pagehide',()=>{if(callActive){const c=callActive;leaveCall();/* best effort; heartbeat expiry is authoritative */}});
function resetCallUi(){if(callActive)leaveCall(false);callKnown.clear();callUserId=null;callRoot.replaceChildren()}
setInterval(refreshCalls,4500);
