const $=s=>document.querySelector(s);
const icons={grid:'<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',party:'<path d="M12 2 20 20 3 17 12 2ZM9 7l5 2M7 11l10 4M19 3v2m-7-4 1 2M21 10l-2 1M3 5l2 1"/>',message:'<path d="M20 11.5c0 4.7-3.6 8-8.5 8-1.2 0-2.2-.2-3.2-.5L4 20l1-4a7.6 7.6 0 0 1-1.5-4.5c0-4.7 3.5-8 8.5-8s8 3.3 8 8Z"/><path d="M8 10h8M8 13h5"/>',clipboard:'<rect x="5" y="5" width="14" height="16" rx="2"/><path d="M9 5V3h6v2M9 12h6M9 16h5"/>',chart:'<path d="M3 3v18h18M7 16l4-4 3 2 5-7"/>',calendar:'<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4M17 3v4M3 10h18"/>',users:'<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',layers:'<path d="m12 2 9 5-9 5-9-5 9-5ZM3 12l9 5 9-5M3 17l9 5 9-5"/>',history:'<path d="M3 12a9 9 0 1 0 3-6.7L3 8M3 3v5h5M12 7v5l3 2"/>',plus:'<path d="M12 5v14M5 12h14"/>',chevLeft:'<path d="m15 18-6-6 6-6"/>',chevRight:'<path d="m9 18 6-6-6-6"/>',download:'<path d="M12 3v12m0 0 4-4m-4 4-4-4M4 17v3h16v-3"/>',search:'<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',logout:'<path d="M10 17l5-5-5-5m5 5H3m9-9h6a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-6"/>',x:'<path d="M18 6 6 18M6 6l12 12"/>',edit:'<path d="m15 5 4 4M4 20l4.5-1 11-11a2.1 2.1 0 0 0-3-3l-11 11L4 20Z"/>',trash:'<path d="M3 6h18M8 6V4h8v2M6 6l1 15h10l1-15M10 10v7M14 10v7"/>',check:'<path d="m4 12 5 5L20 6"/>',clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',info:'<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',menu:'<path d="M4 7h16M4 12h16M4 17h16"/>',sparkle:'<path d="m12 3 1.9 6.1L20 11l-6.1 1.9L12 19l-1.9-6.1L4 11l6.1-1.9L12 3ZM19 18l.7 1.3L21 20l-1.3.7L19 22l-.7-1.3L17 20l1.3-.7L19 18Z"/>',lock:'<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',arrow:'<path d="M5 12h14m-6-6 6 6-6 6"/>',briefcase:'<rect x="3" y="7" width="18" height="14" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M3 13h18"/>',filter:'<path d="M4 7h16M7 12h10m-7 5h4"/>',more:'<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>'};
function ic(name,cls=''){return `<svg class="ico ${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${icons[name]||icons.grid}</svg>`}
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function fmt(n,dec=1){return Number(n||0).toLocaleString('ru-RU',{maximumFractionDigits:dec})}
function pct(n){return n==null?'—':Number(n).toLocaleString('ru-RU',{minimumFractionDigits:2,maximumFractionDigits:2})+' %'}
function initials(name){return String(name||'?').split(/\s+/).slice(0,2).map(s=>s[0]||'').join('').toUpperCase()}
const months=['январь','февраль','март','апрель','май','июнь','июль','август','сентябрь','октябрь','ноябрь','декабрь'];
function monthName(ym){const [y,m]=ym.split('-').map(Number);return months[m-1]+' '+y}
function displayDate(d){if(!d)return '';const [y,m,day]=d.slice(0,10).split('-');return `${day}.${m}.${y}`}
function logDate(d){if(!d)return '';return new Date(d.replace(' ','T')+'Z').toLocaleDateString('ru-RU',{timeZone:'Europe/Minsk',day:'2-digit',month:'2-digit',year:'numeric'})}
function dayTime(d){if(!d)return '';const date=new Date(d.replace(' ','T')+'Z');return logDate(d)+' · '+date.toLocaleTimeString('ru-RU',{timeZone:'Europe/Minsk',hour:'2-digit',minute:'2-digit'})}
function dateShift(date,days){let d=new Date(date+'T12:00:00');d.setDate(d.getDate()+days);return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`}
function dayType(day){const d=new Date(day+'T12:00:00').getDay();return d!==0&&d!==6}
const S={user:null,data:null,month:null,today:null,page:'overview',report:null,logs:null,search:'',userFilter:'',categoryFilter:'',menuOpen:false,modal:null,attendanceChoice:'absent',prankOnline:[],prankTarget:null,presencePeople:[],presenceOnline:false,presenceOpen:false,backupStatus:null,backupPreview:null,backupFile:null};
let authToken='',tokenInUrl=false;
try{authToken=sessionStorage.getItem('forma-session')||''}catch{}
function setToken(token){authToken=token||'';tokenInUrl=false;try{if(authToken)sessionStorage.setItem('forma-session',authToken);else sessionStorage.removeItem('forma-session')}catch{}}
function authedPath(path){return tokenInUrl&&authToken?path+(path.includes('?')?'&':'?')+'forma_ticket='+encodeURIComponent(authToken):path}
async function api(path,method='GET',body){
 const opt={method,credentials:'same-origin',headers:{}};
 if(authToken)opt.headers['X-Forma-Session']=authToken;
 if(body!==undefined){opt.headers['Content-Type']='application/json';opt.body=JSON.stringify(body)}
 let res;try{res=await fetch(authedPath(path),opt)}catch{throw Error('Не удаётся подключиться к серверу. Обновите превью и попробуйте снова.')}
 // Некоторые предпросмотры удаляют все заголовки авторизации. В таком случае
 // повторяем запрос с резервным токеном в URL API (только после неудачного входа).
 if(res.status===401&&authToken&&path!='/api/login'&&!tokenInUrl){
   tokenInUrl=true;
   try{res=await fetch(authedPath(path),opt)}catch{tokenInUrl=false;throw Error('Не удаётся подключиться к серверу')}
 }
 let result;try{result=await res.json()}catch{throw Error('Сервер недоступен')}
 if(!res.ok){if(res.status===401&&path!='/api/login'){setToken('');S.user=null;stopPrankPolling();clearPrankEffect();showLogin()}throw Error(result.error||'Ошибка запроса')}
 return result
}
function notify(message,error=false){const box=document.createElement('div');box.className='toast'+(error?' error':'');box.textContent=message;$('#toast-area').appendChild(box);setTimeout(()=>box.remove(),3600)}
async function init(){try{let session=await api('/api/session');if(!session.user&&authToken&&!tokenInUrl){tokenInUrl=true;session=await api('/api/session');if(!session.user)setToken('')}S.today=session.today;S.user=session.user;S.month=session.today.slice(0,7);if(S.user){await load();startPrankPolling()}else showLogin()}catch(e){showLogin();notify(e.message,true)}}
async function load(){S.data=await api('/api/bootstrap?month='+S.month);S.user=S.data.user;S.today=S.data.today;if(S.page==='report'&&isAdmin())S.report=await api('/api/report?month='+S.month);if(S.page==='activity'&&isAdmin())S.logs=await api('/api/logs');if(S.page==='backup'&&isAdmin())S.backupStatus=await api('/api/backup/status');render()}
function isAdmin(){return S.user?.role==='admin'}
function showLogin(){S.user=null;S.menuOpen=false;document.body.classList.remove('menu-open');$('#app').innerHTML=`<div class="login-screen"><div class="login-art"><div class="quote"><div class="hero-kicker login-kicker"><span class="login-pulse-dot" aria-hidden="true"></span>Пространство вашей команды</div><h1>Каждый день —<br><em>результат.</em></h1><p>Отмечайте выполненную работу, следите за графиком и собирайте отчётность без бесконечных таблиц.</p><div class="login-preview">${[31,54,43,72,61,85,64,105,94,127,109,136].map((h,i)=>`<i style="height:${h}px;opacity:${.35+i*.052}"></i>`).join('')}</div></div></div><div class="login-panel"><form id="login-form" class="login-box"><span class="pill">◉ &nbsp;Добро пожаловать</span><h2>Рады вас видеть!</h2><p>Войдите в личный кабинет, чтобы продолжить работу с командой.</p><div class="field"><label for="login-username">Логин</label><input id="login-username" name="username" placeholder="Ваш логин" autocomplete="username" required autofocus></div><div class="field"><label for="login-password">Пароль</label><input id="login-password" name="password" type="password" placeholder="Введите пароль" autocomplete="current-password" required></div><div class="form-error" id="login-error"></div><button type="submit" class="btn primary">Войти в систему ${ic('arrow')}</button><div class="login-foot">Для входа администратора: логин <b>admin</b>, пароль <b>admin</b>. Данные сотрудников — в файле <b>initial_credentials.txt</b>.</div></form></div></div>`}
const NAV=[['overview','Обзор','grid'],['entries','Мои работы','clipboard'],['report','Сводный отчёт','chart'],['attendance','Табель','calendar'],['team','Сотрудники','users'],['catalog','Каталог работ','layers'],['activity','Журнал действий','history'],['backup','Резервные копии','download'],['prank','Прикол','party']];
function presenceListHTML(){
 const people=S.presencePeople;
 return `<div class="presence-popover-head"><b>Сейчас в сети</b><span>${people.length}</span></div><div class="presence-people">${people.map(u=>`<div class="presence-person"><div class="avatar">${esc(initials(u.name))}</div><span class="presence-person-name">${esc(u.name)}${u.id===S.user?.id?'<small>Вы</small>':''}${u.role==='admin'&&u.name.toLowerCase()!=='администратор'?'<small>Администратор</small>':''}</span><span class="presence-person-dot" aria-label="В сети"></span></div>`).join('')}</div>`;
}
function presenceHTML(){
 const active=S.presenceOnline,open=active&&S.presenceOpen;
 return `<div class="presence-widget" id="presence-widget"><button type="button" id="presence-toggle" class="presence-toggle ${active?'online':''}" data-action="presence-toggle" aria-label="${active?'В сети. Показать пользователей в сети':'Не в сети'}" aria-expanded="${open}" aria-controls="presence-popover" ${active?'':'disabled'}><span class="presence-light" aria-hidden="true"></span><span class="presence-label">${active?'В сети · '+S.presencePeople.length:'Не в сети'}</span>${active?ic('chevRight'):''}</button><div id="presence-popover" class="presence-popover" role="region" aria-label="Пользователи в сети" ${open?'':'hidden'}>${open?presenceListHTML():''}</div></div>`;
}
function updatePresenceWidget(){
 const button=$('#presence-toggle'),popover=$('#presence-popover');if(!button||!popover)return;
 const active=S.presenceOnline,open=active&&S.presenceOpen;
 button.disabled=!active;button.classList.toggle('online',active);
 button.setAttribute('aria-expanded',String(open));
 button.setAttribute('aria-label',active?'В сети. Показать пользователей в сети':'Не в сети');
 button.querySelector('.presence-label').textContent=active?'В сети · '+S.presencePeople.length:'Не в сети';
 const arrow=button.querySelector('svg');if(arrow&&!active)arrow.remove();
 else if(!arrow&&active)button.insertAdjacentHTML('beforeend',ic('chevRight'));
 popover.hidden=!open;if(open)popover.innerHTML=presenceListHTML();
}
function setPresenceOffline(){S.presenceOnline=false;S.presencePeople=[];S.presenceOpen=false;updatePresenceWidget()}
async function refreshPresence(){
 if(navigator.onLine===false){setPresenceOffline();return}
 const info=await api('/api/presence');
 S.presencePeople=info.users;S.presenceOnline=!!S.user&&info.users.some(u=>u.id===S.user.id);
 if(!S.presenceOnline)S.presenceOpen=false;
 presenceSeen=Date.now();updatePresenceWidget();
}
function navList(){return NAV.filter(([id])=>isAdmin()||!['report','team','catalog','activity','backup','prank'].includes(id)).map(([id,label,icon])=>`<button class="nav-link ${S.page===id?'active':''}" data-nav="${id}">${ic(icon)}<span>${label}</span></button>`).join('')}
function render(){if(!S.user)return showLogin();document.body.classList.toggle('menu-open',S.menuOpen);const label=NAV.find(n=>n[0]===S.page)?.[1]||'Обзор';$('#app').innerHTML=`<div class="layout"><div id="sidebar-backdrop" class="sidebar-backdrop ${S.menuOpen?'show':''}" data-action="close-menu" aria-hidden="true"></div><aside id="app-sidebar" class="sidebar ${S.menuOpen?'open':''}" aria-label="Навигация по разделам" aria-hidden="${!S.menuOpen}" ${S.menuOpen?'':'inert'}><div class="side-top"><div class="side-title">Отчёт по работе <span>ГООГС СЭОГС</span></div><button class="sidebar-close icon-btn" type="button" data-action="close-menu" title="Закрыть меню" aria-label="Закрыть меню">${ic('x')}</button></div><div class="side-section">Рабочее пространство</div><nav class="nav">${navList()}</nav><div class="side-bottom"><div class="side-note"><div class="note-icon">${ic('sparkle')}</div><b>Всё под контролем</b><p>Работы, табель и отчёты — в одном удобном пространстве команды.</p></div><div class="side-user"><div class="avatar">${esc(initials(S.user.name))}</div><div class="meta"><b>${esc(S.user.name)}</b><small>${isAdmin()?'Администратор':'Сотрудник'}</small></div><button title="Выйти" data-action="logout">${ic('logout')}</button></div></div></aside><main class="main"><header class="topbar"><button id="menu-toggle" class="icon-btn mobile-menu" type="button" data-action="menu" title="Открыть меню" aria-label="Открыть меню" aria-controls="app-sidebar" aria-expanded="${S.menuOpen}">${ic('menu')}</button><div class="breadcrumbs">Рабочее пространство <span>/</span> <span>${esc(label)}</span></div>${presenceHTML()}<div class="topbar-right"><span class="top-date">${ic('calendar')} ${new Date(S.today+'T12:00:00').toLocaleDateString('ru-RU',{day:'numeric',month:'long',year:'numeric'})}</span><div class="top-divider"></div>${isAdmin()?`<button class="icon-btn" data-modal="password" title="Сменить пароль">${ic('lock')}</button>`:''}<div class="avatar">${esc(initials(S.user.name))}</div></div></header><div class="content">${pageHTML()}</div></main></div><div id="modal-root"></div>`;if(S.modal)renderModal()}
function setMenuOpen(open){
 S.menuOpen=!!open;
 const sidebar=$('#app-sidebar'),backdrop=$('#sidebar-backdrop'),trigger=$('#menu-toggle');
 if(!sidebar||!backdrop||!trigger)return;
 sidebar.classList.toggle('open',S.menuOpen);
 sidebar.inert=!S.menuOpen;
 sidebar.setAttribute('aria-hidden',String(!S.menuOpen));
 backdrop.classList.toggle('show',S.menuOpen);
 trigger.setAttribute('aria-expanded',String(S.menuOpen));
 trigger.setAttribute('aria-label',S.menuOpen?'Закрыть меню':'Открыть меню');
 trigger.title=S.menuOpen?'Закрыть меню':'Открыть меню';
 document.body.classList.toggle('menu-open',S.menuOpen);
 if(S.menuOpen)sidebar.querySelector('.sidebar-close')?.focus();else trigger.focus();
}
function pageHTML(){switch(S.page){case 'entries':return entriesPage();case 'report':return reportPage();case 'attendance':return attendancePage();case 'team':return teamPage();case 'catalog':return catalogPage();case 'activity':return activityPage();case 'backup':return isAdmin()?backupPage():overviewPage();case 'prank':return isAdmin()?prankPage():overviewPage();default:return overviewPage()}}
function monthControl(){return `<div class="month-switch"><button data-action="prev-month" title="Предыдущий месяц">${ic('chevLeft')}</button><strong>${monthName(S.month)}</strong><button data-action="next-month" title="Следующий месяц">${ic('chevRight')}</button></div>`}
function head(eyebrow,title,subtitle,actions=''){return `<div class="page-head"><div><div class="eyebrow">${eyebrow}</div><h1>${title}</h1><p class="subheading">${subtitle}</p></div><div class="actions">${actions}</div></div>`}
function filteredEntries(){return S.data.entries.filter(e=>(!S.userFilter||String(e.user_id)===S.userFilter)&&(!S.categoryFilter||S.data.tasks.find(t=>t.id===e.task_id)?.category===S.categoryFilter)&&(!S.search||(`${S.data.tasks.find(t=>t.id===e.task_id)?.title||''} ${S.data.users.find(u=>u.id===e.user_id)?.name||''} ${e.note||''}`).toLowerCase().includes(S.search.toLowerCase())))}
function currentUsers(){return S.data.users.filter(u=>u.is_staff||!isAdmin())}
function counts(){const entries=S.data.entries,unique=new Set(entries.map(x=>x.user_id));return {quantity:entries.reduce((a,e)=>a+Number(e.quantity),0),hours:entries.reduce((a,e)=>a+Number(e.quantity)*Number(S.data.tasks.find(t=>t.id===e.task_id)?.norm||0),0),records:entries.length,people:unique.size}}
function attendanceStatus(uid,day){const override=S.data.attendance.find(a=>a.user_id===uid&&a.day===day);return override||{status:dayType(day)?'present':'off',reason:''}}
function defaultHours(day){const d=new Date(day+'T12:00:00').getDay();return d>=1&&d<=4?8.25:d===5?7:0}
function hourData(uid,day,source=S.data){
 const personal=source.personal_hours?.find(h=>h.user_id===uid&&h.day===day);
 const global=source.daily_hours?.find(h=>h.day===day);
 if(personal)return {hours:Number(personal.hours),origin:'personal'};
 if(global)return {hours:Number(global.hours),origin:'global'};
 return {hours:defaultHours(day),origin:'schedule'}
}
function tabHours(uid,day,source=S.data){
 const att=source.attendance?.find(a=>a.user_id===uid&&a.day===day);
 if((att?.status|| (dayType(day)?'present':'off'))!=='present')return 0;
 return hourData(uid,day,source).hours
}
function statCard(label,value,foot,icon,tone){return `<div class="stat-card"><div class="stat-top"><span class="stat-label">${label}</span><div class="stat-icon ${tone}">${ic(icon)}</div></div><div class="stat-value">${value}</div><div class="stat-foot">${foot}</div></div>`}
function heroChart(){let monthEntries=S.data.entries,totals=Array.from({length:7},(_,i)=>{let date=dateShift(S.today,-6+i);return monthEntries.filter(e=>e.work_date===date).reduce((a,e)=>a+Number(e.quantity)*Number(S.data.tasks.find(t=>t.id===e.task_id)?.norm||0),0)});let max=Math.max(...totals,1);let pts=totals.map((n,i)=>`${i*58+8},${130-n/max*95}`).join(' ');let area=`8,145 ${pts} 356,145`;return `<div class="hero-graphic"><svg viewBox="0 0 365 150" preserveAspectRatio="none"><defs><linearGradient id="heroGrad" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#5fe0b8" stop-opacity=".28"/><stop offset="1" stop-color="#5fe0b8" stop-opacity="0"/></linearGradient></defs><path d="M5 140H360 M5 95H360 M5 50H360" stroke="#ffffff18" stroke-dasharray="3 6"/><polygon points="${area}" fill="url(#heroGrad)"/><polyline points="${pts}" fill="none" stroke="#6ae2bd" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>${pts.split(' ').map((p,i)=>`<circle cx="${p.split(',')[0]}" cy="${p.split(',')[1]}" r="3.5" fill="#7cebc4" stroke="#215458" stroke-width="2"/>`).join('')}</svg><div class="hero-floating"><b>${fmt(totals.reduce((a,b)=>a+b,0))}</b><small>нормо-часов за 7 дней</small></div></div>`}
function workChart(){let last=14,byday=Array.from({length:last},(_,i)=>{let day=S.month+'-'+String(i+1).padStart(2,'0');return S.data.entries.filter(e=>e.work_date===day).reduce((a,e)=>a+Number(e.quantity)*Number(S.data.tasks.find(t=>t.id===e.task_id)?.norm||0),0)});let daycount=Number(new Date(Number(S.month.slice(0,4)),Number(S.month.slice(5)),0).getDate());byday=Array.from({length:daycount},(_,i)=>{let day=S.month+'-'+String(i+1).padStart(2,'0');return S.data.entries.filter(e=>e.work_date===day).reduce((a,e)=>a+Number(e.quantity)*Number(S.data.tasks.find(t=>t.id===e.task_id)?.norm||0),0)});let max=Math.max(...byday,1),W=650,H=150,barW=(W-20)/byday.length;return `<div class="chart-holder"><svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none"><path d="M2 126H650 M2 86H650 M2 46H650" stroke="#edf1f2" stroke-dasharray="4 5"/>${byday.map((n,i)=>`<rect x="${10+i*barW+barW*.12}" y="${126-n/max*99}" width="${barW*.72}" height="${Math.max(n/max*99,0)}" rx="3" fill="${S.month+'-'+String(i+1).padStart(2,'0')===S.today?'#0b957e':'#5ccbb0'}" opacity="${n?1:0}"/>`).join('')}</svg></div><div class="chart-axis"><span>01 ${months[Number(S.month.slice(5))-1].slice(0,3)}.</span><span>${String(Math.ceil(daycount/2)).padStart(2,'0')} ${months[Number(S.month.slice(5))-1].slice(0,3)}.</span><span>${daycount} ${months[Number(S.month.slice(5))-1].slice(0,3)}.</span></div>`}
function topTasks(){const totals=new Map();S.data.entries.forEach(e=>totals.set(e.task_id,(totals.get(e.task_id)||0)+Number(e.quantity)*Number(S.data.tasks.find(t=>t.id===e.task_id)?.norm||0)));const rows=[...totals].sort((a,b)=>b[1]-a[1]).slice(0,5),max=rows[0]?.[1]||1;return rows.length?rows.map(([id,n],i)=>{let task=S.data.tasks.find(t=>t.id===id);return `<div class="task-row"><span class="rank">${String(i+1).padStart(2,'0')}</span><div class="task-info"><b title="${esc(task?.title)}">${esc(task?.title)}</b><small>${esc(task?.category)}</small><div class="progress-track"><i style="width:${n/max*100}%"></i></div></div><span class="number">${fmt(n)} ч</span></div>`}).join(''):emptyState('Пока нет записей','Добавьте первую выполненную работу')}
function emptyState(title,desc){return `<div class="empty">${ic('clipboard')}<b>${esc(title)}</b>${esc(desc)}</div>`}
function activityRow(a){const actionLabels={login:'Вход в систему',logout:'Выход из системы',entry:'Отмечена работа',delete_entry:'Удалена работа',attendance:'Изменён табель',user_added:'Добавлен сотрудник',user_updated:'Изменён сотрудник',task_added:'Добавлена работа',task_updated:'Изменена работа',password:'Смена пароля',import:'Импорт данных',comment:'Комментарий к ячейке'};return `<div class="activity-item"><div class="activity-icon ${a.action.includes('user')?'blue':''}">${ic(a.action==='attendance'?'calendar':a.action==='comment'?'message':a.action.includes('user')?'users':a.action.includes('task')?'layers':a.action==='login'?'lock':'check')}</div><div style="min-width:0;flex:1"><b>${esc(actionLabels[a.action]||a.action)} · ${esc(a.actor||'Система')}</b><p title="${esc(a.detail)}">${esc(a.detail)}</p></div><small>${esc(logDate(a.created_at))}</small></div>`}
function overviewPage(){let c=counts(),total=activeUsers().length;return `${head('КОМАНДА / ОБЗОР',`Здравствуйте, ${esc(S.user.name.split(' ')[0])}! 👋`,'Ваше пространство для работы, результатов и планирования.',monthControl())}<div class="hero"><div class="hero-copy"><div class="hero-kicker">Рабочий ритм · ${monthName(S.month)}</div><h2>Важные дела —<br>в одном пространстве.</h2><p>Отмечайте выполненное сегодня, а мы соберём всё в наглядный отчёт для команды.</p><button class="btn" data-nav="entries">${ic('plus')} Отметить работу</button><div class="month-statline"><span><strong>${fmt(c.records,0)}</strong> записей за месяц</span><span><strong>${fmt(c.hours)}</strong> нормо-часов</span></div></div>${heroChart()}</div><div class="stats-grid">${statCard('Отметок о работе',fmt(c.records,0),'ежедневных записей за месяц','clipboard','mint')}${statCard('Нормативное время',fmt(c.hours)+' ч','рассчитано по нормам работ','clock','blue')}${statCard('Видов работ',new Set(S.data.entries.map(e=>e.task_id)).size,'с результатом за этот месяц','layers','orange')}${statCard(isAdmin()?'Активных сотрудников':'Моя активность',isAdmin()?fmt(total,0):fmt(S.data.entries.filter(e=>e.user_id===S.user.id).length,0),isAdmin()?'в рабочем пространстве':'личных отметок за месяц','users','rose')}</div><div class="dash-grid"><div class="card card-pad"><div class="card-head"><div><h3>Динамика выполненной работы</h3><p>Нормо-часы по дням · ${monthName(S.month)}</p></div><button class="text-link" data-nav="${isAdmin()?'report':'entries'}">Подробнее ${ic('arrow')}</button></div>${workChart()}<div class="chart-legend"><span class="square"></span> Нормативное время, ч</div></div><div class="card card-pad"><div class="card-head"><div><h3>Направления работ</h3><p>По нормативному времени</p></div><button class="text-link" data-nav="${isAdmin()?'catalog':'entries'}">Все работы ${ic('arrow')}</button></div>${topTasks()}</div></div><div class="dash-grid section-spacer"><div class="card card-pad"><div class="card-head"><div><h3>${isAdmin()?'Последние действия':'Быстрый доступ'}</h3><p>${isAdmin()?'Что происходит в пространстве':'Самые важные инструменты всегда рядом'}</p></div>${isAdmin()?`<button class="text-link" data-nav="activity">Весь журнал ${ic('arrow')}</button>`:''}</div>${isAdmin()?(S.data.recent.length?S.data.recent.slice(0,4).map(activityRow).join(''):emptyState('Пока пусто','Действия появятся здесь')):`<div class="quick-panel"><button class="quick-action" data-nav="entries"><span class="q-icon">${ic('plus')}</span><b>Добавить работу</b><small>Зафиксировать результат</small></button><button class="quick-action" data-nav="attendance"><span class="q-icon">${ic('calendar')}</span><b>Мой табель</b><small>График и отсутствие</small></button><button class="quick-action" data-nav="entries"><span class="q-icon">${ic('clipboard')}</span><b>Мои записи</b><small>История за месяц</small></button></div>`}</div><div class="card card-pad"><div class="card-head"><div><h3>График команды</h3><p>Автоматический табель 5/2</p></div><button class="text-link" data-nav="attendance">Табель ${ic('arrow')}</button></div>${(() => {let date=S.today; if(S.month!==date.slice(0,7))date=S.month+'-01';const present=activeUsers().filter(u=>attendanceStatus(u.id,date).status==='present').length,absent=activeUsers().filter(u=>attendanceStatus(u.id,date).status==='absent').length;return `<div style="display:flex;gap:11px;margin-bottom:20px"><div style="flex:1;background:#edfaf3;padding:16px;border-radius:11px"><span style="font-size:22px;color:#20a883;font-weight:800">${present}</span><p class="small-note">На работе</p></div><div style="flex:1;background:#fff2f0;padding:16px;border-radius:11px"><span style="font-size:22px;color:#e2716b;font-weight:800">${absent}</span><p class="small-note">Отсутствуют</p></div></div><div class="hint">${ic('info')} По графику будние дни отмечены зелёным автоматически. Отсутствия отмечаются вручную с указанием причины.</div>`})()}</div></div>`}
function activeUsers(){return currentUsers().filter(u=>u.active)}
function sheetOwner(){
 if(!isAdmin())return S.user;
 return S.data.users.find(u=>String(u.id)===S.userFilter)||S.data.users.find(u=>u.active)||S.data.users[0];
}
function sheetComment(uid,task,day){
 return S.data.comments?.find(c=>c.user_id===uid&&c.task_id===task&&c.work_date===day)?.body
   ||S.data.entries.find(e=>e.user_id===uid&&e.task_id===task&&e.work_date===day)?.note||'';
}
function entriesPage(){
 const owner=sheetOwner();
 if(!owner)return head('ЛИЧНЫЙ ЖУРНАЛ','Мои работы','Сначала добавьте сотрудника во вкладке «Сотрудники».');
 const [year,mon]=S.month.split('-').map(Number),dayCount=new Date(year,mon,0).getDate();
 const entries=S.data.entries.filter(e=>e.user_id===owner.id);
 const notes=(S.data.comments||[]).filter(c=>c.user_id===owner.id);
 const indexed=new Map(entries.map(e=>[e.task_id+'|'+e.work_date,e]));
 const indexedNotes=new Map(notes.map(c=>[c.task_id+'|'+c.work_date,c.body]));
 const tasks=S.data.tasks.filter(t=>(t.active||entries.some(e=>e.task_id===t.id)||notes.some(c=>c.task_id===t.id))&&(!S.search||t.title.toLowerCase().includes(S.search.toLowerCase())));
 const days=Array.from({length:dayCount},(_,i)=>`${S.month}-${String(i+1).padStart(2,'0')}`);
 const nameSelect=isAdmin()?`<select class="select-sm sheet-person-select" data-filter="user" aria-label="Сотрудник">${S.data.users.map(u=>`<option value="${u.id}" ${u.id===owner.id?'selected':''}>${esc(u.name)}${u.active?'':' (архив)'}</option>`).join('')}</select>`:'';
 const recordedDays=new Set(entries.map(e=>e.work_date)).size;
 const totalTime=entries.reduce((sum,e)=>sum+Number(e.quantity)*(S.data.tasks.find(t=>t.id===e.task_id)?.norm||0),0);
 const header=days.map(d=>{
   const dow=new Date(d+'T12:00:00').getDay(),abbr=['вс','пн','вт','ср','чт','пт','сб'][dow];
   return `<th class="sheet-date-head ${dayType(d)?'':'weekend'} ${d===S.today?'today':''}" title="${displayDate(d)}"><span>${d.slice(-2)}</span><small>${abbr}</small></th>`
 }).join('');
 const body=tasks.map(t=>{
   let total=0,filled=0;
   const cells=days.map(d=>{
     const key=t.id+'|'+d,e=indexed.get(key),note=indexedNotes.get(key)||e?.note||'',future=d>S.today,locked=future||!owner.active||(!t.active&&!e);
     if(e){total+=Number(e.quantity);filled++}
     const label=`${t.title} · ${displayDate(d)}`;
     return `<td class="sheet-day ${dayType(d)?'':'weekend'} ${d===S.today?'today':''} ${e?'filled':''} ${note?'with-note':''} ${future?'sheet-future':''}"><div class="sheet-cell">
       <input class="sheet-input" type="text" inputmode="decimal" autocomplete="off" spellcheck="false" data-cell="1" data-task="${t.id}" data-day="${d}" data-user="${owner.id}" value="${e?esc(fmt(e.quantity,6)):''}" placeholder="·" aria-label="Количество: ${esc(label)}" title="${esc(label)}${note?' · Комментарий: '+esc(note):''}" ${locked?'disabled':''}>
       ${!future&&(t.active||e||note)&&owner.active?`<button type="button" class="sheet-note ${note?'has-note':''}" data-modal="cell-comment" data-user="${owner.id}" data-task="${t.id}" data-day="${d}" aria-label="Комментарий: ${esc(label)}" title="${note?esc(note):'Добавить комментарий'}">${ic('message')}</button>`:''}
       </div></td>`
   }).join('');
   return `<tr><th class="sheet-task" scope="row"><span title="${esc(t.title)}">${esc(t.title)}</span>${!t.active?'<small>Архив</small>':''}</th><td class="sheet-unit">${esc(t.unit)}</td>${cells}<td class="sheet-total"><b>${filled?fmt(total,6):'—'}</b><small>${filled?filled+' дн.':''}</small></td></tr>`
 }).join('');
 const footer=days.map(d=>`<td class="sheet-day-count">${tasks.filter(t=>indexed.has(t.id+'|'+d)).length||'—'}</td>`).join('');
 return `${head('ЛИЧНЫЙ ЖУРНАЛ',isAdmin()?`Работы · ${esc(owner.name)}`:'Мои работы','Персональная таблица как в Excel: работа × дата. Введите количество в ячейку и добавьте комментарий.',`${nameSelect}${monthControl()}`)}
 <div class="sheet-overview"><div><span>${ic('clipboard')}</span><b>${entries.length}</b><small>заполненных ячеек</small></div><div><span>${ic('calendar')}</span><b>${recordedDays}</b><small>дней с работами</small></div><div><span>${ic('clock')}</span><b>${fmt(totalTime,2)} ч</b><small>нормативное время</small></div><p class="sheet-save-status" aria-live="polite">${esc(S.sheetSaved||'Изменения сохраняются после выхода из ячейки')}</p></div>
 <section class="sheet-panel"><div class="sheet-toolbar"><div class="search-input">${ic('search')}<input data-filter="search" value="${esc(S.search)}" placeholder="Найти работу…" autocomplete="off"></div><div class="sheet-toolbar-meta"><span class="badge green">${tasks.length} видов работ</span><span>← Листайте таблицу по горизонтали →</span></div></div>
 <div class="work-sheet-scroll"><table class="work-sheet"><thead><tr><th class="sheet-task">Выполняемые работы</th><th class="sheet-unit">Ед. изм.</th>${header}<th class="sheet-total">Итого<br>за месяц</th></tr></thead><tbody>${body||`<tr><td class="empty" colspan="${dayCount+3}">Нет работ по этому запросу.</td></tr>`}</tbody><tfoot><tr><th class="sheet-task">Заполнено ячеек</th><td class="sheet-unit">за день</td>${footer}<td class="sheet-total">${tasks.reduce((sum,t)=>sum+days.filter(d=>indexed.has(t.id+'|'+d)).length,0)}</td></tr></tfoot></table></div>
 <div class="sheet-bottom-tip">${ic('info')} Нажмите на ячейку и впишите количество. Чтобы очистить количество, удалите значение или введите 0 — комментарий останется. ${ic('message')} Значок у ячейки открывает комментарий; он доступен и без количества. Записи за будущие дни недоступны.</div></section>`
}

function reportPage(){if(!isAdmin())return overviewPage();let r=S.report;if(!r)return `<div class="empty">Загружаем отчёт…</div>`;let users=r.users,rows=r.rows,ids=new Map(),byTask=new Map();rows.forEach(x=>{ids.set(x.task_id+'-'+x.user_id,x);let prev=byTask.get(x.task_id)||{q:0,h:0};prev.q+=Number(x.quantity);prev.h+=Number(x.hours);byTask.set(x.task_id,prev)});let activeTasks=r.tasks.filter(t=>t.active||byTask.has(t.id));let quantity=rows.reduce((a,x)=>a+Number(x.quantity),0),hours=rows.reduce((a,x)=>a+Number(x.hours),0);const daysInMonth=new Date(Number(S.month.slice(0,4)),Number(S.month.slice(5)),0).getDate();const tabTotal=users.reduce((sum,u)=>sum+Array.from({length:daysInMonth},(_,i)=>tabHours(u.id,S.month+'-'+String(i+1).padStart(2,'0'),r)).reduce((a,b)=>a+b,0),0);return `${head('АНАЛИТИКА / ОТЧЁТ','Сводный отчёт','Все результаты команды, собранные автоматически из персональных записей.',`${monthControl()}<button class="btn secondary" data-action="export">${ic('download')} Скачать Excel</button>`)}<div class="report-summary"><div class="summary-tile"><small>Сумма количества*</small><b>${fmt(quantity,2)}</b></div><div class="summary-tile"><small>Нормативное время</small><b>${fmt(hours,2)} ч</b></div><div class="summary-tile"><small>Рабочих часов по табелю</small><b>${fmt(tabTotal,2)} ч</b></div><div class="summary-tile"><small>Сотрудников в отчёте</small><b>${new Set(rows.map(x=>x.user_id)).size} <span class="muted-small">/ ${users.length}</span></b></div></div><p class="report-caption">Сводная таблица · ${monthName(S.month)} · Количество / нормо-часы</p><div class="card table-wrap"><table class="data-table report-table"><thead><tr><th>Выполняемая работа</th><th>Ед.</th><th>Норма, ч</th>${users.map(u=>`<th>${esc(u.name)}</th>`).join('')}<th>Итого</th></tr></thead><tbody>${activeTasks.map(t=>{let total=byTask.get(t.id)||{q:0,h:0};return `<tr><td><div class="truncate strong" style="max-width:310px" title="${esc(t.title)}">${esc(t.title)}</div><span class="entry-date">${esc(t.category)}</span></td><td class="muted">${esc(t.unit)}</td><td class="num">${fmt(t.norm,3)}</td>${users.map(u=>{let row=ids.get(t.id+'-'+u.id);return `<td>${row?`<span class="report-cell">${fmt(row.quantity,2)}<small>${fmt(row.hours,2)} ч</small></span>`:'<span class="report-empty">—</span>'}</td>`}).join('')}<td><span class="report-cell">${fmt(total.q,2)}<small>${fmt(total.h,2)} ч</small></span></td></tr>`}).join('')}<tr class="total-row"><td>ИТОГО ПО КОМАНДЕ</td><td>—</td><td>—</td>${users.map(u=>{let ur=rows.filter(x=>x.user_id===u.id);return `<td><span class="report-cell">${fmt(ur.reduce((a,x)=>a+Number(x.quantity),0),2)}<small>${fmt(ur.reduce((a,x)=>a+Number(x.hours),0),2)} ч</small></span></td>`}).join('')}<td><span class="report-cell">${fmt(quantity,2)}<small>${fmt(hours,2)} ч</small></span></td></tr>
<tr class="report-hours-row"><td class="report-row-label">РАБОЧИЕ ЧАСЫ ЗА МЕСЯЦ <small>по табелю · с учётом отсутствий</small></td><td>ч</td><td>—</td>${users.map(u=>{const p=r.productivity?.find(x=>x.user_id===u.id);return `<td class="num">${fmt(p?.work_hours,2)} ч</td>`}).join('')}<td class="num">${fmt(r.productivity_total?.work_hours,2)} ч</td></tr>
<tr class="report-productivity-row"><td class="report-row-label">ПРОИЗВОДИТЕЛЬНОСТЬ <small>округлённые нормо-часы / рабочие часы × 100 %</small></td><td>%</td><td>—</td>${users.map(u=>{const p=r.productivity?.find(x=>x.user_id===u.id);return `<td class="report-percent" title="${p?'Нормо-часы (округл.): '+p.rounded_norm_hours+'; рабочие часы: '+p.work_hours:''}">${pct(p?.percent)}</td>`}).join('')}<td class="report-percent">${pct(r.productivity_total?.percent)}</td></tr></tbody></table></div><div class="hint section-spacer">${ic('info')} Новые работы автоматически появляются здесь и у каждого сотрудника. Общая сумма количества объединяет разные единицы (шт., м. и другие) — сравнивайте результат по отдельным видам работ или в нормо-часах. Производительность, как в исходном Excel: округлённые до целого нормо-часы выполненных работ ÷ рабочие часы по табелю за месяц × 100 %. При 0 рабочих часов показываем «—». В Excel также есть табель по дням, записи и комментарии.</div>`}
function attendancePage(){
 const [year,month]=S.month.split('-').map(Number),days=new Date(year,month,0).getDate(),users=activeUsers();
 const workDays=Array.from({length:days},(_,i)=>i+1).filter(i=>dayType(S.month+'-'+String(i).padStart(2,'0'))).length;
 const actions=`${monthControl()}${isAdmin()?`<button class="btn primary" data-modal="global-hours">${ic('clock')} Часы для всех</button>`:''}`;
 const headers=Array.from({length:days},(_,i)=>{
   const day=S.month+'-'+String(i+1).padStart(2,'0'),overridden=S.data.daily_hours?.some(h=>h.day===day);
   return `<th class="${dayType(day)?'':'weekend-th'}" title="${displayDate(day)}">${isAdmin()?`<button class="day-head-btn ${overridden?'overridden':''}" data-modal="global-hours" data-day="${day}" title="Часы для всех · ${displayDate(day)}">${String(i+1).padStart(2,'0')}${overridden?'<i></i>':''}</button>`:String(i+1).padStart(2,'0')}</th>`
 }).join('');
 const body=users.map(u=>{
   let present=0,absent=0,total=0;
   const cells=Array.from({length:days},(_,i)=>{
     const day=S.month+'-'+String(i+1).padStart(2,'0'),record=attendanceStatus(u.id,day),status=record.status;
     const info=hourData(u.id,day),hours=tabHours(u.id,day);
     if(status==='present')present++;
     if(status==='absent')absent++;
     total+=hours;
     const source=info.origin==='personal'?'индивидуально':info.origin==='global'?'общее изменение':'по графику';
     const tooltip=`${u.name} · ${displayDate(day)} · ${status==='absent'?'Отсутствует: '+record.reason:status==='off'?'Выходной':'На работе: '+fmt(hours,2)+' ч ('+source+')'}`;
     return `<td>${isAdmin()?`<button class="day-cell ${status} ${day===S.today?'today':''} ${day>S.today?'future':''} ${info.origin==='personal'?'personal-override':''}" data-modal="attendance" data-user="${u.id}" data-day="${day}" title="${esc(tooltip)}"><span>${status==='off'?'—':fmt(hours,2)}</span></button>`:`<span class="day-cell readonly ${status} ${day===S.today?'today':''} ${day>S.today?'future':''} ${info.origin==='personal'?'personal-override':''}" title="${esc(tooltip)}"><span>${status==='off'?'—':fmt(hours,2)}</span></span>`}</td>`
   }).join('');
   return `<tr><td class="sticky-person">${esc(u.name)}</td>${cells}<td class="totals">${present}</td><td class="totals red">${absent}</td><td class="totals">${fmt(total,2)}</td></tr>`
 }).join('');
 return `${head('ГРАФИК РАБОТЫ','Табель и человеко-часы',isAdmin()?'График команды: изменение часов на дату для всех и отдельно для каждого.':'Ваш график 5/2 и учтённые часы по дням.',actions)}
 <div class="hours-summary"><div><span>ПН — ЧТ</span><strong>8,25 ч</strong><small>каждый рабочий день</small></div><div><span>ПЯТНИЦА</span><strong>7 ч</strong><small>сокращённый день</small></div><div><span>СБ — ВС</span><strong>0 ч</strong><small>по умолчанию выходные</small></div></div>
 <div class="card"><div class="attendance-wrap"><div class="card-head"><div><h3>${monthName(S.month)[0].toUpperCase()+monthName(S.month).slice(1)} · график 5/2</h3><p>${workDays} плановых рабочих дней · ${isAdmin()?'нажмите на ячейку, чтобы изменить день; на число в шапке — часы для всех':'просмотр без возможности изменения'}</p></div><div class="attendance-legend"><div class="legend-item"><span class="square present"></span> На работе</div><div class="legend-item"><span class="square absent"></span> Отсутствует</div><div class="legend-item"><span class="square off"></span> Выходной</div></div></div>
 <div class="attendance-scroll"><table class="attendance-table"><thead><tr><th class="sticky-person">Сотрудник</th>${headers}<th>На работе</th><th>Отсут.</th><th>Часов</th></tr></thead><tbody>${body}</tbody></table></div></div>
 <div class="att-card-info">В ячейках — часы по табелю: зелёный день по графику или ручной отметке, красный — отсутствие (0 ч), серый — выходной (0 ч). Суммы справа включают весь выбранный месяц, в том числе будущие дни по плану. Индивидуальные часы имеют приоритет перед общей настройкой дня.</div></div>
 <div class="hint section-spacer">${ic('info')} По умолчанию часы являются плановыми, а не подтверждением фактического выхода. ${isAdmin()?'Для работы в выходной отметьте сотруднику «На работе» и при необходимости задайте часы.':'Изменить табель может только администратор.'} Праздники автоматически не исключаются.</div>`
}

const backupNames={users:'Учётные записи',tasks:'Виды работ',entries:'Записи работ',cell_comments:'Комментарии',attendance:'Отметки табеля',daily_hours:'Общие часы',personal_hours:'Личные часы',activity:'События журнала'};
function backupDate(iso){return iso?new Date(iso.replace(' ','T').replace(/(\d{2}:\d{2}:\d{2})$/,'$1Z')).toLocaleString('ru-RU',{timeZone:'Europe/Minsk'}):'—'}
function backupPage(){
 const status=S.backupStatus,now=status?.current,view=S.backupPreview;
 const latest=(info)=>`<div class="backup-info-grid"><div><small>Самая ранняя работа</small><b>${displayDate(info?.first_work_date)||'—'}</b></div><div><small>Последняя работа</small><b>${displayDate(info?.last_work_date)||'—'}</b></div><div><small>Последнее действие</small><b>${backupDate(info?.last_activity)}</b></div><div><small>Администраторов / сотрудников</small><b>${info?.active_admins??'—'} / ${info?.staff??'—'}</b></div></div>`;
 return `${head('АДМИНИСТРАТОР / ДАННЫЕ','Резервные копии','Сохраните данные, сравните старый архив с текущей базой и при необходимости восстановите.',`<button class="btn secondary" data-action="backup-refresh">${ic('history')} Обновить</button>`)}
 <div class="backup-grid"><section class="card card-pad"><div class="card-head"><div><h3>Текущая база</h3><p>Скачайте копию на свой компьютер и храните её отдельно от сайта.</p></div></div>
 ${now?latest(now):'<p>Загрузка данных…</p>'}<div class="backup-key-counts"><b>${now?.counts?.entries??'—'}</b> записей работ · <b>${now?.counts?.tasks??'—'}</b> видов работ · <b>${now?.counts?.users??'—'}</b> учётных записей</div>
 <button type="button" class="btn primary" data-action="backup-download">${ic('download')} Скачать резервную копию ZIP</button>
 <p class="backup-subnote">Архив содержит данные и хеши паролей, но не содержит действующих сеансов. Храните файл в безопасном месте.</p></section>
 <section class="card card-pad"><div class="card-head"><div><h3>Загрузить старую копию</h3><p>Перед восстановлением сначала просмотрите различия.</p></div></div>
 <label class="backup-file-label" for="backup-file">${ic('download')} ${esc(S.backupFile?.name||'Выбрать ZIP-архив Forma')}</label><input type="file" id="backup-file" accept=".zip,application/zip"><div class="backup-buttons"><button type="button" class="btn secondary" data-action="backup-inspect" ${S.backupFile?'':'disabled'}>Сравнить с текущей базой</button></div>
 <p class="backup-subnote">Максимум 25 МБ. Данные не изменятся, пока вы не подтвердите восстановление.</p></section></div>
 ${view?`<section class="card card-pad backup-comparison"><h2>Сравнение с копией от ${esc(backupDate(view.created_at))}</h2><p>При восстановлении текущие данные будут <b>полностью заменены</b> данными копии. Разница = в копии минус сейчас.</p><div class="backup-compare-scroll"><table class="data-table"><thead><tr><th>Данные</th><th>Сейчас</th><th>В копии</th><th>Разница</th></tr></thead><tbody>${Object.entries(backupNames).map(([key,label])=>{let row=view.comparison[key];return `<tr><td>${label}</td><td>${row.now}</td><td>${row.backup}</td><td class="${row.difference<0?'backup-negative':''}">${row.difference>0?'+':''}${row.difference}</td></tr>`}).join('')}</tbody></table></div><h3>Даты и права</h3><div class="backup-double"><div><b>Сейчас</b>${latest(view.current)}</div><div><b>В копии</b>${latest(view.backup)}</div></div>
 <div class="backup-alert">Восстановление вернёт учётные записи, пароли, роли, работы, табель и историю на дату копии. Все пользователи будут выведены из системы и должны войти снова. Перед заменой будет создан страховочный ZIP на сервере, но на бесплатном Render локальные файлы не сохраняются — обязательно скачайте копию себе.</div>
 <label class="backup-confirm-label" for="backup-confirm">Для полной замены введите <b>ВОССТАНОВИТЬ</b></label><input id="backup-confirm" class="backup-confirm-input" autocomplete="off" placeholder="ВОССТАНОВИТЬ"><button type="button" class="btn danger" data-action="backup-restore" disabled>Восстановить всю базу</button></section>`:''}
 ${status?.safety?.length?`<section class="card card-pad backup-safety"><h3>Автоматические копии перед восстановлением</h3><p>Скачайте их с сервера: на бесплатном хостинге местные файлы не долговечны.</p>${status.safety.map(item=>`<div class="backup-safety-item"><span>${esc(item.name)} · ${(item.size/1024).toFixed(0)} КБ</span><button type="button" class="btn secondary" data-action="backup-safety" data-name="${esc(item.name)}">${ic('download')} Скачать</button></div>`).join('')}</section>`:''}`;
}
function prankPage(){
 const people=S.data.users.filter(u=>u.active&&u.is_staff);
 const selected=people.some(u=>u.id===Number(S.prankTarget))?Number(S.prankTarget):people[0]?.id;
 S.prankTarget=selected??null;
 const online=S.prankOnline.includes(selected);
 return `${head('ДЛЯ АДМИНИСТРАТОРА / РАЗВЛЕЧЕНИЯ','Прикол','Выберите сотрудника, у которого открыт сайт, и отправьте эффект. Сначала можно испытать его у себя.')}
 <div class="prank-target card"><div class="prank-target-icon">${ic('users')}</div><div class="prank-target-info"><h3>Кому отправить?</h3><p>Эффект появится только у пользователя, который сейчас в сети на этом сайте.</p></div>
 <select id="prank-user" aria-label="Выберите сотрудника" ${people.length?'':'disabled'}>${people.map(u=>`<option value="${u.id}" ${u.id===selected?'selected':''}>${esc(u.name)}</option>`).join('')}</select><span class="prank-presence ${online?'online':''}" id="prank-presence">${online?'● Сейчас в сети':'○ Не в сети'}</span></div>
 <div class="prank-cards">
 <section class="card prank-card"><div class="prank-art people-art" aria-hidden="true"><span>🕺</span><span>💃</span><span>🕺</span></div><div class="prank-card-content"><span class="prank-kicker">ЭФФЕКТ 01</span><h2>Прыгающие человечки</h2><p>40 человечков быстро летают по экрану. Каждый отскакивает от краёв 10 раз и исчезает.</p><div class="prank-buttons"><button class="btn secondary" type="button" data-action="prank-test-people">${ic('sparkle')} Тест у себя</button><button class="btn primary prank-send" type="button" data-action="prank-send-people" ${online?'':'disabled'}>${ic('arrow')} Отправить</button></div></div></section>
 <section class="card prank-card"><div class="prank-art speech-art" aria-hidden="true">🔊 <span>Привет!</span></div><div class="prank-card-content"><span class="prank-kicker">ЭФФЕКТ 02</span><h2>Сообщение голосом</h2><p>Текст появится поверх страницы, а голос компьютера попробует прочитать его вслух.</p><label for="prank-text">Текст сообщения</label><textarea id="prank-text" maxlength="400" rows="4" placeholder="Напишите сообщение для сотрудника…"></textarea><div class="prank-buttons"><button class="btn secondary" type="button" data-action="prank-test-speech">${ic('message')} Тест у себя</button><button class="btn primary prank-send" type="button" data-action="prank-send-speech" ${online?'':'disabled'}>${ic('arrow')} Отправить</button></div></div></section>
 <section class="card prank-card"><div class="prank-art cat-art" aria-hidden="true"><div class="prank-cat-sprite"></div></div><div class="prank-card-content"><span class="prank-kicker">ЭФФЕКТ 03</span><h2>Кот-курьер</h2><p>Рыжий посыльный пробежит по нижнему краю экрана и принесёт ваше короткое сообщение. Не мешает работе.</p><label for="prank-cat-text">Послание кота</label><input id="prank-cat-text" type="text" maxlength="140" value="Кот-курьер принёс вам хорошее настроение!" placeholder="Что передать сотруднику?"><div class="prank-buttons"><button class="btn secondary" type="button" data-action="prank-test-cat">${ic('sparkle')} Тест у себя</button><button class="btn primary prank-send" type="button" data-action="prank-send-cat" ${online?'':'disabled'}>${ic('arrow')} Отправить</button></div></div></section>
 <section class="card prank-card"><div class="prank-art achievement-art" aria-hidden="true"><span class="achievement-art-icon">🏆</span><span class="achievement-art-label">Достижение!</span>✨</div><div class="prank-card-content"><span class="prank-kicker">ЭФФЕКТ 04</span><h2>Достижение разблокировано</h2><p>Праздничная плашка с небольшим конфетти. Название придумайте сами — без оценок результатов и персональных данных.</p><label for="prank-achievement-text">Название достижения</label><input id="prank-achievement-text" type="text" maxlength="80" value="Повелитель таблиц" placeholder="Например: Король пятницы"><div class="prank-buttons"><button class="btn secondary" type="button" data-action="prank-test-achievement">${ic('sparkle')} Тест у себя</button><button class="btn primary prank-send" type="button" data-action="prank-send-achievement" ${online?'':'disabled'}>${ic('arrow')} Отправить</button></div></div></section>
 <section class="card prank-card"><div class="prank-art parade-art" aria-hidden="true"><span>🚶</span><span>💃</span><span>🚶</span><span>🕺</span><span>🚶</span></div><div class="prank-card-content"><span class="prank-kicker">ЭФФЕКТ 05</span><h2>Мини-парад</h2><p>Небольшая весёлая процессия марширует по нижнему краю экрана и уходит сама через несколько секунд.</p><div class="prank-buttons"><button class="btn secondary" type="button" data-action="prank-test-parade">${ic('sparkle')} Тест у себя</button><button class="btn primary prank-send" type="button" data-action="prank-send-parade" ${online?'':'disabled'}>${ic('arrow')} Отправить</button></div></div></section>
 </div>
 <div class="prank-hint">${ic('info')} Эффекты видит только выбранный сотрудник с открытой вкладкой. Новые анимации короткие, не перехватывают клики и учитывают настройку уменьшения движения. Для голосового сообщения нужен включённый звук: если он недоступен, текст остаётся на экране.</div>`
}
function teamPage(){let people=S.data.users;return `${head('КОМАНДА','Сотрудники','Создавайте аккаунты, управляйте доступом и следите за результатами.',`<button class="btn primary" data-modal="user">${ic('plus')} Добавить сотрудника</button>`)}<div class="team-grid">${people.map(u=>{let ent=S.data.entries.filter(e=>e.user_id===u.id),hours=ent.reduce((a,e)=>a+Number(e.quantity)*Number(S.data.tasks.find(t=>t.id===e.task_id)?.norm||0),0);return `<div class="team-card ${u.active?'':'inactive'}"><div class="team-card-top"><div class="avatar">${esc(initials(u.name))}</div><span class="badge ${u.active?'green':'gray'}">${u.active?'● Активен':'● Отключён'}</span></div><h3>${esc(u.name)}</h3><p>@${esc(u.username)}${u.role==='admin'?' · Администратор':''}</p><div class="team-card-footer"><span>${ent.length} записей · ${fmt(hours)} ч</span><div><button class="table-icon-btn" title="Изменить сотрудника и права" data-modal="edit-user" data-id="${u.id}">${ic('edit')}</button><button class="table-icon-btn ${u.active?'danger':''}" title="${u.active?'Отключить':'Включить'}" data-action="toggle-user" data-id="${u.id}">${ic(u.active?'lock':'check')}</button></div></div></div>`}).join('')}</div><div class="settings-area"><div class="stat-icon mint">${ic('lock')}</div><div><b style="font-size:11px">Доступ к данным</b><p>Сотрудник меняет только данные в «Мои работы»; табель доступен ему для просмотра. Администратор управляет командой и видит общий отчёт.</p></div></div>`}
function catalogPage(){let tasks=S.data.tasks.filter(t=>!S.search||t.title.toLowerCase().includes(S.search.toLowerCase())||t.category.toLowerCase().includes(S.search.toLowerCase()));return `${head('СПРАВОЧНИК','Каталог работ','Один общий список для всей команды. Добавленные работы сразу доступны сотрудникам.',`<button class="btn primary" data-modal="task">${ic('plus')} Новая работа</button>`)}<div class="card"><div class="filter-bar"><div class="search-input">${ic('search')}<input data-filter="search" value="${esc(S.search)}" placeholder="Найти вид работы…"></div><span class="count-chip">${S.data.tasks.filter(t=>t.active).length} активных работ</span></div><div class="table-wrap"><table class="data-table"><thead><tr><th>Выполняемая работа</th><th>Направление</th><th>Ед. изм.</th><th>Норма, ч</th><th>Статус</th><th class="right">Действия</th></tr></thead><tbody>${tasks.map(t=>`<tr><td><div class="truncate strong" title="${esc(t.title)}">${esc(t.title)}</div></td><td><span class="badge blue">${esc(t.category)}</span></td><td class="muted">${esc(t.unit)}</td><td class="num">${fmt(t.norm,3)}</td><td><span class="badge ${t.active?'green':'gray'}">${t.active?'Активна':'Архив'}</span></td><td class="right"><button class="table-icon-btn" title="Редактировать" data-modal="edit-task" data-id="${t.id}">${ic('edit')}</button><button class="table-icon-btn ${t.active?'danger':''}" title="${t.active?'Архивировать':'Восстановить'}" data-action="toggle-task" data-id="${t.id}">${ic(t.active?'trash':'check')}</button></td></tr>`).join('')}</tbody></table></div><div class="table-footer">${tasks.length} работ · Архивирование сохраняет историю выполненных работ в отчётах</div></div>`}
function activityPage(){return `${head('ИСТОРИЯ / АУДИТ','Журнал действий','Изменения и события в системе сохраняются автоматически.',`<button class="btn secondary" data-action="refresh">${ic('history')} Обновить</button>`)}<div class="card card-pad"><div class="card-head"><div><h3>Последние события</h3><p>До 150 последних действий</p></div><span class="badge green">${S.logs?.logs?.length||0} событий</span></div>${S.logs?.logs?.length?S.logs.logs.map(a=>`<div class="activity-item"><div class="activity-icon ${a.action.includes('user')?'blue':''}">${ic(a.action==='attendance'?'calendar':a.action==='comment'?'message':a.action.includes('user')?'users':a.action.includes('task')?'layers':'check')}</div><div style="min-width:0;flex:1"><b>${esc(a.actor)} · ${esc(({login:'Вход в систему',logout:'Выход',entry:'Отметка работы',delete_entry:'Удаление записи',attendance:'Изменение табеля',user_added:'Новый сотрудник',user_updated:'Изменение сотрудника',task_added:'Новая работа',task_updated:'Изменение работы',password:'Смена пароля',import:'Импорт данных',comment:'Комментарий к ячейке'})[a.action]||a.action)}</b><p style="white-space:normal;max-width:unset">${esc(a.detail)}</p></div><small class="log-date">${esc(dayTime(a.created_at))}</small></div>`).join(''):emptyState('Событий пока нет','Журнал появится после первых действий')}</div>`}
function modalFrame(title,desc,content,submit='Сохранить'){return `<div class="modal-backdrop" data-action="close-modal"><div class="modal" role="dialog" aria-modal="true" aria-label="${esc(title)}"><div class="modal-head"><div><h2>${esc(title)}</h2><p>${esc(desc)}</p></div><button class="close-btn" type="button" data-action="close-modal">${ic('x')}</button></div><form id="modal-form" class="modal-body"><div class="form-grid">${content}<div class="form-error" id="form-error"></div><div class="form-actions"><button class="btn secondary" type="button" data-action="close-modal">Отмена</button><button class="btn primary" type="submit">${submit}</button></div></div></form></div></div>`}
function field(name,label,type='text',value='',extra=''){return `<div class="field"><label for="field-${name}">${label}</label><input id="field-${name}" name="${name}" type="${type}" value="${esc(value)}" ${extra}></div>`}
function renderModal(){let root=$('#modal-root');if(!root)return;let m=S.modal;if(!m){root.innerHTML='';return}let html='';if(m.type==='entry'){
 let existing=S.data.entries.find(e=>e.id===Number(m.id));let date=existing?.work_date||(S.month===S.today.slice(0,7)?S.today:S.month+'-01');let user=existing?.user_id||Number(m.user)||S.user.id;
 let tasks=S.data.tasks.filter(t=>t.active||existing?.task_id===t.id);
 html=modalFrame(existing?'Редактировать запись':'Отметить выполненную работу','Укажите работу, количество и дату выполнения.',`${isAdmin()?`<div class="field"><label>Сотрудник</label><select name="user_id" required>${activeUsers().map(u=>`<option value="${u.id}" ${u.id===user?'selected':''}>${esc(u.name)}</option>`).join('')}</select></div>`:''}<div class="field"><label>Вид работы</label><select name="task_id" required>${tasks.filter(t=>t.active||t.id===existing?.task_id).map(t=>`<option value="${t.id}" ${t.id===existing?.task_id?'selected':''}>${esc(t.title)} · ${esc(t.unit)}</option>`).join('')}</select></div><div class="form-two">${field('date','Дата выполнения','date',date,`max="${S.today}" required`)}${field('quantity','Количество','number',existing?.quantity||'',`min="0.001" max="10000000" step="any" placeholder="Например, 5" required`)}</div><div class="field"><label>Комментарий <span class="muted-small">· необязательно</span></label><textarea name="note" placeholder="Краткое примечание к работе…" maxlength="500">${esc(existing?.note||'')}</textarea><small>Если такая работа уже отмечена за этот день, запись будет обновлена.</small></div>`,existing?'Сохранить изменения':'Добавить запись');
 }else if(m.type==='cell-comment'){
 const uid=Number(m.user),tid=Number(m.task),task=S.data.tasks.find(t=>t.id===tid);
 const owner=S.data.users.find(u=>u.id===uid),entry=S.data.entries.find(e=>e.user_id===uid&&e.task_id===tid&&e.work_date===m.day);
 const note=sheetComment(uid,tid,m.day);
 html=modalFrame('Комментарий к ячейке',`${owner?.name||'Сотрудник'} · ${displayDate(m.day)}`,
 `<div class="sheet-comment-context">${ic('clipboard')} <div><b>${esc(task?.title||'Работа')}</b><small>${entry?fmt(entry.quantity,6)+' '+esc(task?.unit||''):'Количество не указано'}</small></div></div>
 <div class="field"><label>Комментарий <span class="muted-small">· можно без количества</span></label><textarea name="comment" maxlength="500" placeholder="Например, что именно было сделано…">${esc(note)}</textarea><small>Очистите поле и сохраните, чтобы удалить комментарий. До 500 символов.</small></div>`, 'Сохранить комментарий');
 }else if(m.type==='attendance'){
 const uid=Number(m.user),user=S.data.users.find(u=>u.id===uid);
 const record=S.data.attendance.find(a=>a.user_id===uid&&a.day===m.day);
 const own=S.data.personal_hours?.find(h=>h.user_id===uid&&h.day===m.day);
 const common=S.data.daily_hours?.find(h=>h.day===m.day);
 S.attendanceChoice=record?.status||(dayType(m.day)?'present':'clear');
 const otherHours=common?Number(common.hours):defaultHours(m.day);
 const hoursField=isAdmin()?`<div class="field hours-field"><label>Часы для ${esc(user?.name||'сотрудника')} <span class="muted-small">· индивидуально</span></label><input name="hours" type="number" min="0" max="24" step="0.01" value="${own?own.hours:''}" placeholder="${otherHours}" inputmode="decimal"><small>Пустое поле — ${common?'общая норма '+fmt(otherHours,2)+' ч':'норма графика '+fmt(otherHours,2)+' ч'}. Индивидуальная настройка важнее общей. При отсутствии в табеле всегда 0 ч.</small></div>`:'';
 html=modalFrame('Отметка в табеле',`${user?.name||'Сотрудник'} · ${displayDate(m.day)}`,
 `<div class="field"><label>Статус дня</label><div class="status-options"><button type="button" class="status-choice ${S.attendanceChoice==='present'?'selected':''}" data-status="present"><span class="square present"></span>На работе</button><button type="button" class="status-choice ${S.attendanceChoice==='absent'?'selected absence':''}" data-status="absent"><span class="square absent"></span>Отсутствует</button><button type="button" class="status-choice ${S.attendanceChoice==='clear'?'selected':''}" data-status="clear"><span class="square off"></span>По графику</button></div></div>
 <div class="field" id="reason-wrap" style="display:${S.attendanceChoice==='absent'?'block':'none'}"><label>Причина отсутствия</label><input name="reason" maxlength="160" value="${esc(record?.reason||'')}" placeholder="Например, отпуск, больничный" ${S.attendanceChoice==='absent'?'required':''}></div>
 ${hoursField}<div class="hint">${ic('info')} По графику: пн–чт — 8,25 ч, пт — 7 ч, выходные — 0 ч. Статус и часы можно менять независимо.</div>`, 'Сохранить отметку');
 }else if(m.type==='global-hours'){
 const day=m.day||(S.month===S.today.slice(0,7)?S.today:S.month+'-01');
 const override=S.data.daily_hours?.find(h=>h.day===day);
 html=modalFrame('Часы для всех','Измените часы на выбранный день сразу для всей команды.',
 `${field('date','Дата','date',day,'required')}
 <div class="field"><label>Человеко-часов на день</label><input id="field-hours" name="hours" type="number" min="0" max="24" step="0.01" value="${override?.hours??''}" placeholder="${defaultHours(day)}" inputmode="decimal" required><small id="global-current">${override?'Сейчас общее значение: '+fmt(override.hours,2)+' ч':'По графику: '+fmt(defaultHours(day),2)+' ч'}. Оставшиеся индивидуальные значения сохранят свой приоритет.</small></div>
 <button type="button" class="btn soft" data-action="reset-global-hours">${ic('history')} Сбросить общие часы на этот день</button>
 <div class="hint">${ic('info')} Пн–чт: 8,25 ч · пятница: 7 ч · выходные: 0 ч. У отсутствующих сотрудников часы в табеле остаются нулевыми.</div>`, 'Применить для всех');
 }else if(m.type==='user'){
 html=modalFrame('Новый сотрудник','Создайте доступ в личный кабинет.',`${field('name','Имя сотрудника','text','',`placeholder="Фамилия Имя" maxlength="90" required`)}${field('username','Логин','text','',`placeholder="ivanov" pattern="[A-Za-z0-9_.-]{3,40}" autocomplete="off" required`)}${field('password','Временный пароль','text','',`minlength="8" placeholder="Не менее 8 символов" autocomplete="off" required`)}<div class="hint">${ic('info')} Передайте логин и пароль сотруднику лично. При необходимости пароль позже может изменить администратор.</div>`,'Добавить сотрудника');
 }else if(m.type==='edit-user'){
 const u=S.data.users.find(u=>u.id===Number(m.id));html=modalFrame('Редактировать сотрудника',`@${u.username}`,`${field('name','Имя сотрудника','text',u.name,'required')}${field('username','Логин','text',u.username,'pattern="[A-Za-z0-9_.-]{3,40}" maxlength="40" autocomplete="off" required')}<div class="hint">${ic('info')} После смены логина сотрудник войдёт заново с новым логином и прежним паролем. Его работы, табель и права сохранятся.</div><div class="field"><label for="staff-role">Права доступа</label><select id="staff-role" name="role" ${u.id===S.user.id?'disabled':''}><option value="employee" ${u.role==='employee'?'selected':''}>Сотрудник · только «Мои работы»</option><option value="admin" ${u.role==='admin'?'selected':''}>Администратор · полный доступ</option></select><small>${u.id===S.user.id?'Нельзя снять права с самого себя.':'Администратор может управлять пользователями, работами, часами, отчётами и резервными копиями. Работы и табель сотрудника сохранятся.'}</small></div><div class="field"><label>Новый пароль <span class="muted-small">· если нужно сбросить</span></label><input name="password" type="text" minlength="8" autocomplete="off" placeholder="Оставьте пустым, чтобы не менять"><small>При смене пароля все активные сессии сотрудника будут завершены.</small></div>`);
 }else if(m.type==='task'||m.type==='edit-task'){
 const t=S.data.tasks.find(t=>t.id===Number(m.id)),editing=!!t;html=modalFrame(editing?'Изменить работу':'Новая работа',editing?'Обновите параметры вида работы.':'Появится в каталоге у всех сотрудников.',`<div class="field"><label>Название работы</label><textarea name="title" minlength="4" maxlength="300" placeholder="Что выполняет сотрудник?" required>${esc(t?.title||'')}</textarea></div><div class="form-two">${field('unit','Единица измерения','text',t?.unit||'шт.','maxlength="30" required')}${field('norm','Норма, ч / ед.','number',t?.norm??0,'min="0" max="10000" step="any" required')}</div><div class="field"><label>Направление</label><select name="category">${['7ЭГ и документация','МПК Панорама','ПК УРГ','Другое',...(t&&!['7ЭГ и документация','МПК Панорама','ПК УРГ','Другое'].includes(t.category)?[t.category]:[])].map(c=>`<option ${t?.category===c?'selected':''}>${esc(c)}</option>`).join('')}</select></div><div class="hint">${ic('info')} Нормативное время в отчёте = количество × норма.</div>`,editing?'Сохранить':'Добавить работу');
 }else if(m.type==='password'){
 html=modalFrame('Сменить пароль','Новый пароль будет нужен при следующем входе.',`${field('old','Текущий пароль','password','','required autocomplete="current-password"')}${field('new','Новый пароль','password','','minlength="8" required autocomplete="new-password"')}`,'Сменить пароль');
 }root.innerHTML=html;root.querySelector('input,select,textarea')?.focus()}
async function navigate(page){const wasMenuOpen=S.menuOpen;if(wasMenuOpen)setMenuOpen(false);S.modal=null;S.page=page;S.search='';S.userFilter='';S.categoryFilter='';if(page==='report'&&isAdmin())S.report=await api('/api/report?month='+S.month);if(page==='activity'&&isAdmin())S.logs=await api('/api/logs');if(page==='backup'&&isAdmin())S.backupStatus=await api('/api/backup/status');if(page==='prank'&&isAdmin())S.prankOnline=(await api('/api/prank/online')).user_ids;render();if(wasMenuOpen)$('#menu-toggle')?.focus({preventScroll:true});window.scrollTo({top:0,behavior:'smooth'})}
function closeModal(){S.modal=null;$('#modal-root')?.replaceChildren()}
async function saveModal(form){const m=S.modal,fd=new FormData(form),data=Object.fromEntries(fd.entries());const sheetX=$('.work-sheet-scroll')?.scrollLeft||0;try{form.querySelector('button[type=submit]').disabled=true;if(m.type==='entry'){
  const payload={...data,task_id:Number(data.task_id),user_id:Number(data.user_id||S.user.id),quantity:Number(data.quantity)};
  if(m.id)await api('/api/entries/'+m.id,'PATCH',payload);else await api('/api/entries','POST',payload);
  notify('Запись о работе сохранена');
 }else if(m.type==='cell-comment'){
   await api('/api/comments','POST',{user_id:Number(m.user),task_id:Number(m.task),date:m.day,comment:data.comment||''});
   S.sheetSaved='Комментарий сохранён';
 }else if(m.type==='attendance'){
   const uid=Number(m.user),own=S.data.personal_hours?.find(h=>h.user_id===uid&&h.day===m.day);
   if(isAdmin()&&data.hours!==undefined){
     const typed=String(data.hours).trim();
     if(typed!==''&&(!Number.isFinite(Number(typed))||Number(typed)<0||Number(typed)>24))throw Error('Укажите от 0 до 24 часов');
     if(typed!==''&&(!own||Number(own.hours)!==Number(typed)))await api('/api/hours','POST',{user_id:uid,date:m.day,hours:Number(typed)});
     if(typed===''&&own)await api('/api/hours','POST',{user_id:uid,date:m.day,hours:null});
   }
   await api('/api/attendance','POST',{user_id:uid,date:m.day,status:S.attendanceChoice,reason:data.reason||''});
   notify('Табель и часы обновлены')
 }
 else if(m.type==='global-hours'){
   if(String(data.hours).trim()==='')throw Error('Введите количество часов');
   await api('/api/hours','POST',{date:data.date,hours:Number(data.hours)});
   notify('Часы для всей команды обновлены')
 }
 else if(m.type==='user'){await api('/api/users','POST',data);notify('Сотрудник добавлен. Передайте ему данные для входа.')}
 else if(m.type==='edit-user'){
   if(!data.password)delete data.password;
   const ownLoginChanged=Number(m.id)===S.user.id&&data.username.trim().toLowerCase()!==S.user.username.toLowerCase();
   await api('/api/users/'+m.id,'PATCH',data);
   if(ownLoginChanged){setToken('');stopPrankPolling();clearPrankEffect();S.modal=null;S.user=null;S.data=null;showLogin();notify('Логин изменён. Войдите заново с новым логином и прежним паролем.');return}
   notify('Данные сотрудника обновлены');
 }
 else if(m.type==='task'){await api('/api/tasks','POST',{...data,norm:Number(data.norm)});notify('Работа добавлена для всей команды')}
 else if(m.type==='edit-task'){await api('/api/tasks/'+m.id,'PATCH',{...data,norm:Number(data.norm)});notify('Работа обновлена')}
 else if(m.type==='password'){await api('/api/password','POST',data);notify('Пароль изменён')}
 closeModal();await load();if(S.page==='entries'&&$('.work-sheet-scroll'))$('.work-sheet-scroll').scrollLeft=sheetX
 }catch(e){const err=$('#form-error');if(err)err.textContent=e.message;form.querySelector('button[type=submit]').disabled=false}}

async function saveGridCell(input){
 if(!input||input.dataset.saving)return;
 const uid=Number(input.dataset.user),tid=Number(input.dataset.task),day=input.dataset.day;
 const existing=S.data.entries.find(e=>e.user_id===uid&&e.task_id===tid&&e.work_date===day);
 const raw=input.value.trim(),normalized=raw.replace(/\s/g,'').replace(',','.');
 const empty=normalized===''||Number(normalized)===0;
 const quantity=empty?null:Number(normalized);
 if(!empty&&(!Number.isFinite(quantity)||quantity<=0||quantity>10000000)){
   input.value=existing?fmt(existing.quantity,6):'';
   notify('Введите положительное количество (можно использовать запятую)',true);return;
 }
 if((empty&&!existing)||(!empty&&existing&&quantity===Number(existing.quantity)))return;
 const scrollX=$('.work-sheet-scroll')?.scrollLeft||0,scrollY=window.scrollY;
 input.dataset.saving='true';input.classList.add('saving');
 try{
   if(empty){await api('/api/entries/'+existing.id,'DELETE')}
   else{
     const payload={user_id:uid,task_id:tid,date:day,quantity,note:sheetComment(uid,tid,day)};
     if(existing)await api('/api/entries/'+existing.id,'PATCH',payload);
     else await api('/api/entries','POST',payload)
   }
   S.sheetSaved='Сохранено · '+displayDate(day);
   await load();
   const sheet=$('.work-sheet-scroll');if(sheet)sheet.scrollLeft=scrollX;
   window.scrollTo({top:scrollY});
   if(S.gridNext){
     const next=document.querySelector(`.sheet-input[data-task="${S.gridNext.task}"][data-day="${S.gridNext.day}"]`);
     if(next){next.focus();next.select()}
     S.gridNext=null
   }
 }catch(e){input.value=existing?fmt(existing.quantity,6):'';input.classList.remove('saving');delete input.dataset.saving;S.gridNext=null;notify(e.message,true)}
}

// Приколы: короткие события доставляются только открытым вкладкам; тест не обращается к серверу.
let prankInterval=null,prankCursor=null,prankBusy=false,prankTimer=null,prankFrame=null,prankSpeechText='',presenceSeen=0;
function startPrankPolling(){
 if(prankInterval||!S.user)return;
 prankCursor=null;presenceSeen=0;setPresenceOffline();
 pollPranks();prankInterval=setInterval(()=>{if(presenceSeen&&Date.now()-presenceSeen>12000)setPresenceOffline();pollPranks()},3000);
}
function stopPrankPolling(){if(prankInterval)clearInterval(prankInterval);prankInterval=null;prankCursor=null;presenceSeen=0;setPresenceOffline()}
async function pollPranks(){
 if(!S.user||prankBusy)return;
 prankBusy=true;
 try{
  const result=await api('/api/prank/poll'+(prankCursor===null?'':'?after='+prankCursor));
  prankCursor=result.last_id;
  await refreshPresence();
  for(const event of result.events)playPrank(event.kind,event.body);
  if(S.page==='prank'&&isAdmin()){
   S.prankOnline=(await api('/api/prank/online')).user_ids;
   updatePrankPresence();
  }
 }catch(e){setPresenceOffline();console.warn('Связь временно недоступна',e.message)}finally{prankBusy=false}
}
function updatePrankPresence(){
 const online=S.prankOnline.includes(Number(S.prankTarget)),badge=$('#prank-presence');
 if(badge){badge.textContent=online?'● Сейчас в сети':'○ Не в сети';badge.classList.toggle('online',online)}
 document.querySelectorAll('.prank-send').forEach(btn=>btn.disabled=!online);
}
function clearPrankEffect(){
 if(prankTimer)clearTimeout(prankTimer);prankTimer=null;
 if(prankFrame!==null)cancelAnimationFrame(prankFrame);prankFrame=null;
 document.querySelectorAll('.prank-screen').forEach(el=>el.remove());
 if('speechSynthesis' in window)window.speechSynthesis.cancel();
}
function reflectPrankAxis(next,velocity,limit){
 if(limit<=0)return {position:0,velocity:0,hits:0};
 let hits=0;
 while(next<0||next>limit){
  if(next<0)next=-next;else next=2*limit-next;
  velocity=-velocity;hits++;
 }
 return {position:next,velocity,hits};
}
function speakPrank(text){
 if(!('speechSynthesis' in window)||!('SpeechSynthesisUtterance' in window))return false;
 window.speechSynthesis.cancel();
 const utterance=new SpeechSynthesisUtterance(text);utterance.lang='ru-RU';utterance.rate=0.95;
 const voice=window.speechSynthesis.getVoices().find(v=>v.lang?.toLowerCase().startsWith('ru'));
 if(voice)utterance.voice=voice;
 window.speechSynthesis.speak(utterance);return true;
}
function playPrank(kind,text=''){
 clearPrankEffect();
 const layer=document.createElement('div');layer.className='prank-screen';
 if(kind==='people'){
  layer.classList.add('prank-people');layer.setAttribute('aria-label','40 летающих человечков');
  const size=Math.min(68,Math.max(36,window.innerWidth*.05));
  const maxX=Math.max(0,window.innerWidth-size),maxY=Math.max(0,window.innerHeight-size);
  const people=[];
  for(let i=0;i<40;i++){
   const element=document.createElement('span');element.className='prank-person';
   element.textContent=['🕺','💃','🏃','🙋'][i%4];
   element.style.width=element.style.height=size+'px';element.style.fontSize=size*.88+'px';
   layer.appendChild(element);
   const x=((i*.61803398875)%1)*maxX,y=((i*.38196601125)%1)*maxY;
   element.style.transform=`translate3d(${x}px,${y}px,0)`;
   people.push({element,x,y,vx:(500+Math.random()*650)*(Math.random()<.5?-1:1),
    vy:(450+Math.random()*550)*(Math.random()<.5?-1:1),hits:0});
  }
  document.body.appendChild(layer);
  let lastTime=null;
  function fly(time){
   const dt=lastTime===null?0:Math.min(.05,Math.max(0,(time-lastTime)/1000));lastTime=time;
   const edgeX=Math.max(0,window.innerWidth-size),edgeY=Math.max(0,window.innerHeight-size);
   for(let i=people.length-1;i>=0;i--){
    const p=people[i];
    const x=reflectPrankAxis(p.x+p.vx*dt,p.vx,edgeX),y=reflectPrankAxis(p.y+p.vy*dt,p.vy,edgeY);
    p.x=x.position;p.y=y.position;p.vx=x.velocity;p.vy=y.velocity;
    p.hits=Math.min(10,p.hits+x.hits+y.hits);
    if(x.hits||y.hits)p.element.dataset.bounces=String(p.hits);
    if(p.hits===10){p.element.remove();people.splice(i,1)}
    else p.element.style.transform=`translate3d(${p.x}px,${p.y}px,0)`;
   }
   if(people.length&&layer.isConnected)prankFrame=requestAnimationFrame(fly);
   else{layer.remove();prankFrame=null}
  }
  prankFrame=requestAnimationFrame(fly);
 }else if(kind==='speech'){
  prankSpeechText=String(text||'');
  layer.classList.add('prank-speech');layer.innerHTML=`<div class="prank-message" role="alert"><div class="prank-message-icon">🔊</div><small>СООБЩЕНИЕ ДЛЯ ВАС</small><p class="prank-message-text"></p><div class="prank-message-actions"><button type="button" class="btn secondary" data-action="prank-replay">Озвучить</button><button type="button" class="btn primary" data-action="prank-close">Закрыть</button></div></div>`;
  layer.querySelector('.prank-message-text').textContent=prankSpeechText;
  document.body.appendChild(layer);
  if(!speakPrank(prankSpeechText))notify('Голос недоступен в этом браузере: сообщение показано на экране',true);
  prankTimer=setTimeout(clearPrankEffect,Math.min(90000,Math.max(20000,prankSpeechText.length*250)));
 }else if(kind==='cat'){
  layer.classList.add('prank-cat-layer');layer.setAttribute('role','status');
  layer.innerHTML='<div class="prank-cat-runner"><div class="prank-cat-bob"><div class="prank-cat-bubble"><small>СПЕЦИАЛЬНАЯ ДОСТАВКА</small><strong class="prank-cat-copy"></strong></div><div class="prank-cat-sprite" role="img" aria-label="Рыжий кот-курьер перебирает лапами"></div></div></div>';
  layer.querySelector('.prank-cat-copy').textContent=String(text||'').slice(0,140);
  document.body.appendChild(layer);
  prankTimer=setTimeout(clearPrankEffect,9300);
 }else if(kind==='achievement'){
  layer.classList.add('prank-achievement-layer');layer.setAttribute('role','status');
  layer.innerHTML='<div class="prank-achievement-toast"><div class="prank-achievement-medal">🏆</div><div class="prank-achievement-copy"><small>ДОСТИЖЕНИЕ РАЗБЛОКИРОВАНО</small><strong></strong><span>Так держать! ✨</span></div><div class="prank-confetti" aria-hidden="true"></div></div>';
  layer.querySelector('.prank-achievement-copy strong').textContent=String(text||'').slice(0,80);
  const confetti=layer.querySelector('.prank-confetti');
  for(let i=0;i<18;i++){
   const piece=document.createElement('i');
   piece.style.setProperty('--confetti-x',(7+(i*47)%90)+'%');
   piece.style.setProperty('--confetti-delay',(i%7)*.11+'s');
   piece.style.setProperty('--confetti-hue',String([35,152,195,328][i%4]));
   confetti.appendChild(piece);
  }
  document.body.appendChild(layer);
  prankTimer=setTimeout(clearPrankEffect,6900);
 }else if(kind==='parade'){
  layer.classList.add('prank-parade-layer');layer.setAttribute('role','status');
  layer.innerHTML='<div class="prank-parade-track"><div class="prank-parade-banner">Вам — маленький парад! 🎉</div><div class="prank-parade-march" aria-label="Весёлая процессия"></div></div>';
  const march=layer.querySelector('.prank-parade-march');
  ['🚶','💃','🚶','🕺','🚶','🙋','🚶','💃'].forEach((person,i)=>{
   const el=document.createElement('span');el.textContent=person;el.style.animationDelay=(i%3)*.12+'s';march.appendChild(el);
  });
  document.body.appendChild(layer);
  prankTimer=setTimeout(clearPrankEffect,7900);
 }
}
async function sendPrank(kind,button){
 if(!isAdmin())return;
 const target=Number($('#prank-user')?.value);
 const inputId={speech:'prank-text',cat:'prank-cat-text',achievement:'prank-achievement-text'}[kind];
 const text=inputId?($('#'+inputId)?.value.trim()||''):'';
 if(inputId&&!text){notify(kind==='achievement'?'Введите название достижения':'Сначала введите текст сообщения',true);$('#'+inputId)?.focus();return}
 if(!button.dataset.action.startsWith('prank-test-')&&!target){notify('Выберите сотрудника',true);return}
 if(button.dataset.action.startsWith('prank-test-')){playPrank(kind,text);return}
 button.disabled=true;
 try{const result=await api('/api/prank/send','POST',{user_id:target,kind,text});notify('Отправлено: '+result.name)}
 catch(e){notify(e.message,true)}finally{updatePrankPresence()}
}
async function backupRequest(path,method='GET',file=null,extraHeaders={}){
 const opt={method,credentials:'same-origin',headers:{...extraHeaders}};
 if(authToken)opt.headers['X-Forma-Session']=authToken;
 if(file){opt.headers['Content-Type']='application/octet-stream';opt.body=file}
 let response=await fetch(authedPath(path),opt);
 if(response.status===401&&authToken&&!tokenInUrl){tokenInUrl=true;response=await fetch(authedPath(path),opt)}
 if(!response.ok){
  let detail;try{detail=await response.json()}catch{}
  if(response.status===401){setToken('');S.user=null;stopPrankPolling();showLogin()}
  throw Error(detail?.error||'Ошибка резервного копирования');
 }
 return response;
}
function saveBackupBlob(response,name){
 return response.blob().then(blob=>{
  const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;
  document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),20000);
 });
}
document.addEventListener('submit',async e=>{if(e.target.id==='login-form'){e.preventDefault();const form=e.target,btn=form.querySelector('button');btn.disabled=true;$('#login-error').textContent='';try{const d=Object.fromEntries(new FormData(form).entries());const res=await api('/api/login','POST',d);setToken(res.session_token);S.user=res.user;S.page='overview';await load();startPrankPolling()}catch(err){$('#login-error').textContent=err.message}finally{btn.disabled=false}}else if(e.target.id==='modal-form'){e.preventDefault();await saveModal(e.target)}});
document.addEventListener('click',async e=>{if(S.presenceOpen&&!e.target.closest('.presence-widget')){S.presenceOpen=false;updatePresenceWidget()}const nav=e.target.closest('[data-nav]');if(nav){try{await navigate(nav.dataset.nav)}catch(err){notify(err.message,true)}return}const btn=e.target.closest('[data-action],[data-modal],[data-status]');if(!btn)return;if(btn.dataset.modal){S.modal={type:btn.dataset.modal,id:btn.dataset.id,user:btn.dataset.user,task:btn.dataset.task,day:btn.dataset.day};renderModal();return}if(btn.dataset.status){S.attendanceChoice=btn.dataset.status;document.querySelectorAll('.status-choice').forEach(b=>b.classList.toggle('selected',b===btn));$('#reason-wrap').style.display=S.attendanceChoice==='absent'?'block':'none';const reason=$('#reason-wrap input');reason.required=S.attendanceChoice==='absent';return}
 if(btn.dataset.action==='presence-toggle'){if(!S.presenceOnline)return;S.presenceOpen=!S.presenceOpen;updatePresenceWidget();if(S.presenceOpen)try{await refreshPresence()}catch{setPresenceOffline()}return}
 if(btn.dataset.action==='prank-close'){clearPrankEffect();return}
 if(btn.dataset.action==='prank-replay'){speakPrank(prankSpeechText);return}
 if(btn.dataset.action?.startsWith('prank-test-')||btn.dataset.action?.startsWith('prank-send-')){
  const kind=btn.dataset.action.replace(/^prank-(?:test|send)-/,'');
  if(['people','speech','cat','achievement','parade'].includes(kind))await sendPrank(kind,btn);
  return
 }
 if(btn.dataset.action==='close-modal'){if(btn.classList.contains('modal-backdrop')&&e.target!==btn)return;closeModal();return}
 if(btn.dataset.action==='menu'){setMenuOpen(!S.menuOpen);return}if(btn.dataset.action==='close-menu'){setMenuOpen(false);return}
 try{switch(btn.dataset.action){case 'prev-month':case 'next-month':{let [y,m]=S.month.split('-').map(Number);m+=btn.dataset.action==='prev-month'?-1:1;if(m<1){m=12;y--}if(m>12){m=1;y++}if(y<2020||y>Number(S.today.slice(0,4))+1)return;S.month=`${y}-${String(m).padStart(2,'0')}`;await load();break}
 case 'logout':await api('/api/logout','POST');setToken('');S.user=null;S.data=null;stopPrankPolling();clearPrankEffect();showLogin();break;
 case 'refresh':await load();notify('Данные обновлены');break;
 case 'backup-refresh':S.backupStatus=await api('/api/backup/status');S.backupPreview=null;render();break;
 case 'backup-download':{
  const response=await backupRequest('/api/backup/download');
  await saveBackupBlob(response,'forma-backup-'+new Date().toISOString().slice(0,10)+'.zip');
  notify('Резервная копия скачивается');break
 }
 case 'backup-safety':{
  const name=btn.dataset.name;
  const response=await backupRequest('/api/backup/safety?name='+encodeURIComponent(name));
  await saveBackupBlob(response,name);break
 }
 case 'backup-inspect':{
  if(!S.backupFile)throw Error('Выберите ZIP-архив Forma');
  if(S.backupFile.size>25*1024*1024)throw Error('Архив больше 25 МБ');
  btn.disabled=true;
  try{S.backupPreview=await (await backupRequest('/api/backup/inspect','POST',S.backupFile)).json();render()}
  finally{btn.disabled=false}
  break
 }
 case 'backup-restore':{
  if(!S.backupPreview||!S.backupFile||$('#backup-confirm')?.value.trim()!=='ВОССТАНОВИТЬ')throw Error('Сначала сравните архив и подтвердите восстановление');
  if(!confirm('Текущие данные будут ПОЛНОСТЬЮ ЗАМЕНЕНЫ. Вы скачали резервную копию?'))return;
  btn.disabled=true;
  const preview=S.backupPreview;
  const query='archive_hash='+encodeURIComponent(preview.archive_hash)+'&current_signature='+encodeURIComponent(preview.current_signature);
  let result;
  try{result=await (await backupRequest('/api/backup/restore?'+query,'POST',S.backupFile,{'X-Forma-Confirm':'RESTORE'})).json()}
  catch(err){btn.disabled=false;throw err}
  setToken('');S.user=null;S.data=null;stopPrankPolling();clearPrankEffect();S.backupPreview=null;S.backupFile=null;showLogin();
  notify('База восстановлена. Войдите с паролем из загруженной копии. Страховочная копия: '+result.safety_copy);break
 }
 case 'reset-global-hours':{
   const day=$('#field-date')?.value;
   if(!day)throw Error('Укажите дату');
   await api('/api/hours','POST',{date:day,hours:null});
   closeModal();await load();notify('На дату возвращена норма по графику');break
 }
 case 'export':{const response=await fetch(authedPath('/api/export?month='+S.month),{credentials:'same-origin',headers:authToken?{'X-Forma-Session':authToken}:{}});if(!response.ok){const err=await response.json();throw Error(err.error||'Ошибка экспорта')}const blob=await response.blob(),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='forma-report-'+S.month+'.xlsx';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),5000);notify('Excel-отчёт скачивается');break}
 case 'delete-entry':{if(!confirm('Удалить эту запись? Действие попадёт в журнал.'))return;await api('/api/entries/'+btn.dataset.id,'DELETE');notify('Запись удалена');await load();break}
 case 'toggle-user':{let u=S.data.users.find(u=>u.id===Number(btn.dataset.id));if(!confirm(`${u.active?'Отключить':'Включить'} сотрудника ${u.name}?`))return;await api('/api/users/'+u.id,'PATCH',{active:!u.active});notify('Доступ сотрудника обновлён');await load();break}
 case 'toggle-task':{let t=S.data.tasks.find(t=>t.id===Number(btn.dataset.id));if(!confirm(`${t.active?'Архивировать':'Восстановить'} работу «${t.title}»?`))return;await api('/api/tasks/'+t.id,'PATCH',{active:!t.active});notify('Каталог обновлён');await load();break}
 }}catch(err){notify(err.message,true)}});
document.addEventListener('input',e=>{if(e.target.id==='backup-confirm'){$('[data-action="backup-restore"]').disabled=e.target.value.trim()!=='ВОССТАНОВИТЬ';return}if(!e.target.dataset.filter)return;let type=e.target.dataset.filter,value=e.target.value;if(type==='search')S.search=value;if(type==='user')S.userFilter=value;let pos=e.target.selectionStart;let name=e.target.dataset.filter;let prev=document.activeElement;render();let next=document.querySelector(`[data-filter="${name}"]`);if(next){next.focus();if(name==='search')next.setSelectionRange(pos,pos)}});
document.addEventListener('change',e=>{
 if(e.target.id==='backup-file'){S.backupFile=e.target.files?.[0]||null;S.backupPreview=null;render();return}
 if(e.target.id==='prank-user'){S.prankTarget=Number(e.target.value);updatePrankPresence();return}
 if(e.target.dataset.cell){saveGridCell(e.target);return}
 if(e.target.dataset.filter==='user'){S.userFilter=e.target.value;S.sheetSaved='';render()}
 if(e.target.name==='date'&&S.modal?.type==='global-hours'&&e.target.value){
   const record=S.data.daily_hours?.find(h=>h.day===e.target.value);
   const input=$('#field-hours'),hint=$('#global-current');
   if(input){input.value=record?.hours??'';input.placeholder=defaultHours(e.target.value)}
   if(hint)hint.textContent=record?'Сейчас общее значение: '+fmt(record.hours,2)+' ч. Индивидуальные значения сохраняют приоритет.':'По графику: '+fmt(defaultHours(e.target.value),2)+' ч. Индивидуальные значения сохраняют приоритет.';
 }
});
document.addEventListener('keydown',e=>{
 if(e.key==='Escape'&&S.modal){closeModal();return}
 if(e.key==='Escape'&&S.presenceOpen){S.presenceOpen=false;updatePresenceWidget();$('#presence-toggle')?.focus();return}
 if(e.key==='Escape'&&S.menuOpen){setMenuOpen(false);return}
 if(e.target.matches?.('.sheet-input')&&(e.key==='Enter'||e.key==='Tab')){
   const input=e.target,all=[...document.querySelectorAll('.sheet-input:not(:disabled)')];
   const index=all.indexOf(input),next=all[index+(e.shiftKey?-1:1)];
   if(e.key==='Tab'&&!next)return;
   e.preventDefault();
   S.gridNext=next?{task:next.dataset.task,day:next.dataset.day}:null;
   const changed=input.value!==input.defaultValue;
   input.blur();
   if(!changed){if(next){next.focus();next.select()}S.gridNext=null}
 }
});
document.addEventListener('visibilitychange',()=>{if(!document.hidden&&S.user)pollPranks()});
window.addEventListener('offline',setPresenceOffline);window.addEventListener('online',()=>{if(S.user)pollPranks()});
init();
