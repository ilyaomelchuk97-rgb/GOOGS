// Light browser-free checks of badge labels, chat room layout and safe toast text.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('web/main.js','utf8').replace(/\ninit\(\);\s*$/,'\n');
const elements=[];
const document={hidden:false,addEventListener(){},querySelectorAll(){return elements},querySelector(){return null}};
const context=vm.createContext({document,window:{addEventListener(){}},sessionStorage:{getItem(){return ''}},console,URL,fetch(){throw Error('not expected')},setTimeout,clearTimeout,setInterval,clearInterval});
vm.runInContext(source,context);
vm.runInContext(`S.user={id:1,name:'Сотрудник'};S.unread={general:108,direct:{'2':3}};S.chatData={users:[{id:2,name:'Пётр Иванов',role:'employee',avatar_stored:1,avatar_revision:1}],messages:[{id:1,sender_id:2,sender_name:'Пётр Иванов',body:'Привет',created_at:'2026-10-07 09:30:00',avatar_stored:1,avatar_revision:1}]}`,context);
assert(context.unreadBadge('general').includes('99+'));
assert(context.unreadBadge('2').includes('>3</span>'));
assert(context.chatRoomsHTML().includes('Пётр Иванов'));
assert(context.chatRoomsHTML().includes('data-unread-room="2"'));
assert(context.chatMessagesHTML().includes('data-avatar-id="2"'));
const rich={bubble:'#112233',glow:true,glow_color:'#ff0099',border_effect:20,flower:20,branch:20,logo:20};
vm.runInContext('S.chatData.messages[0].style='+JSON.stringify(rich),context);
assert(context.chatMessagesHTML().includes('effect-20'));
assert(context.chatMessagesHTML().includes('ornament-logo-20'));
assert(context.chatDecor(rich).includes('/mingas-official-logo.webp'));
assert(!context.normalizedStyle({bubble:'red; background:url(x)',border_effect:21}).bubble);
assert((context.chatEditorHTML('message').match(/<option value="20"/g)||[]).length===4);
const css=fs.readFileSync('web/styles.css','utf8');
for(const category of ['effect','ornament-flower','ornament-branch','ornament-logo']){
 for(let i=1;i<=20;i++)assert(css.includes('.'+category+'-'+i+'{'),category+' '+i);
}
vm.runInContext("S.chatRoom='2';S.chatData.theme={flower:7,border_effect:9};S.chatDesignOpen='room'",context);
assert(context.chatPage().includes('Рамка чата'));
assert(context.chatPage().includes('ornament-flower-7'));
assert(context.chatPage().includes('Показать всем участникам'));
assert(context.navList().indexOf('Обзор')<context.navList().indexOf('Чат'));
assert(context.navList().indexOf('Чат')<context.navList().indexOf('Мои работы'));
for(const room of ['general','2','all'])elements.push({dataset:{unreadRoom:room},hidden:false,textContent:''});
context.updateUnreadUI();assert.deepEqual(elements.map(x=>x.textContent),['99+','3','99+']);
vm.runInContext("S.unread={general:0,direct:{}}",context);context.updateUnreadUI();assert(elements.every(x=>x.hidden));
(async()=>{
 const paths=[],toasts=[];
 let step=0;
 context.api=async path=>{paths.push(path);return step++===0?
  {direct:{'2':1},general:0,notices:[],cursor:10}:
  {direct:{'2':2},general:1,notices:[{sender_name:'Пётр Иванов'}],cursor:11}};
 context.notify=text=>toasts.push(text);
 await context.pollChatStatus();await context.pollChatStatus();
 assert.deepEqual(paths,['/api/chat/status','/api/chat/status?after=10']);
 assert.deepEqual(toasts,['Вам пришло новое сообщение от „Пётр Иванов“']);
 console.log('OK: меню, 99+, отдельные бейджи, аватары и уведомление');
})().catch(e=>{console.error(e);process.exitCode=1});
