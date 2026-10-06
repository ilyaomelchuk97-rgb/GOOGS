// Forma → личный Google Диск. Вставьте весь файл в НОВЫЙ проект Apps Script.
// Секреты вводятся только в Project Settings → Script properties, НЕ в этот файл.
// Один запуск в каждом часу 08–17 (включительно), Europe/Minsk; минуты неточные.
const FORMA_TIMEZONE = 'Europe/Minsk';

function settings_() {
  const props = PropertiesService.getScriptProperties();
  const url = String(props.getProperty('FORMA_URL') || '').replace(/\/$/, '');
  const key = String(props.getProperty('BACKUP_TOKEN') || '');
  if (!/^https:\/\/[a-z0-9-]+\.onrender\.com$/i.test(url)) {
    throw new Error('Set FORMA_URL to the HTTPS onrender.com address without a path');
  }
  if (key.length < 32) throw new Error('Set a strong BACKUP_TOKEN (at least 32 characters)');
  return { props, url, key };
}

function setup() {
  const { props } = settings_();
  // Create a private folder in the script owner's My Drive, unless supplied.
  let folderId = props.getProperty('FOLDER_ID');
  if (folderId) DriveApp.getFolderById(folderId).getName();
  else {
    const folder = DriveApp.createFolder('Forma — резервные копии');
    folderId = folder.getId();
    props.setProperty('FOLDER_ID', folderId);
  }
  // Safe to rerun: avoid duplicated hourly triggers for this function.
  ScriptApp.getProjectTriggers()
    .filter(trigger => trigger.getHandlerFunction() === 'runBackup')
    .forEach(trigger => ScriptApp.deleteTrigger(trigger));
  ScriptApp.newTrigger('runBackup').timeBased().everyHours(1).create();
  console.log('Hourly trigger installed. Folder ID: ' + folderId);
  console.log('Time window: 08:00–17:59 Europe/Minsk; Google chooses the minute.');
}

function runBackup() { backup_(false); }

// Run once manually after setup to test immediately, even outside 08–17.
function testBackupNow() { backup_(true); }

function backup_(force) {
  const now = new Date();
  const hour = Number(Utilities.formatDate(now, FORMA_TIMEZONE, 'H'));
  if (!force && (hour < 8 || hour > 17)) return;
  const slot = Utilities.formatDate(now, FORMA_TIMEZONE, 'yyyy-MM-dd_HH');
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(30000)) throw new Error('Another backup is in progress; retry later');
  try {
    const { props, url, key } = settings_();
    if (!force && props.getProperty('LAST_BACKUP_SLOT') === slot) return;
    const folderId = props.getProperty('FOLDER_ID');
    if (!folderId) throw new Error('Run setup() first');
    let previous = props.getProperty('LAST_CONTENT_FINGERPRINT') || '';
    const savedFileId = props.getProperty('LAST_BACKUP_FILE_ID');
    // If the last successful ZIP was removed, don't suppress the next backup.
    if (previous && savedFileId) {
      try {
        if (DriveApp.getFileById(savedFileId).isTrashed()) previous = '';
      } catch (_) { previous = ''; }
    } else previous = '';
    const headers = { 'X-Forma-Backup-Key': key };
    if (previous) headers['X-Forma-If-Unchanged'] = previous;
    const response = UrlFetchApp.fetch(url + '/internal/backup', {
      method: 'post', headers,
      followRedirects: false,
      muteHttpExceptions: true
    });
    const code = response.getResponseCode();
    if (code !== 200 && code !== 204) {
      // Don't log response bodies, URLs with secrets, or private backup data.
      throw new Error('Forma backup failed: HTTP ' + code);
    }
    const responseHeaders = response.getAllHeaders();
    const headerKey = Object.keys(responseHeaders).find(k => k.toLowerCase() === 'x-forma-data-signature');
    const signature = headerKey ? String(responseHeaders[headerKey]) : '';
    if (!/^[a-f0-9]{64}$/.test(signature)) throw new Error('Missing data signature; backup not marked successful');
    if (code === 204 && previous && signature === previous) {
      props.setProperty('LAST_BACKUP_SLOT', slot);
      console.log('No changes in work data since the last saved ZIP; skipped ' + slot);
      return;
    }
    if (code !== 200) throw new Error('Unexpected empty response; backup not saved');
    const blob = response.getBlob();
    const bytes = blob.getBytes();
    if (bytes.length < 100 || bytes[0] !== 80 || bytes[1] !== 75) {
      throw new Error('Response is not a valid ZIP header; backup not saved');
    }
    const stamp = Utilities.formatDate(new Date(), FORMA_TIMEZONE, 'yyyy-MM-dd_HH-mm-ss');
    const filename = 'Forma_' + stamp + '_Minsk.zip';
    const file = DriveApp.getFolderById(folderId).createFile(blob.setName(filename).setContentType('application/zip'));
    props.setProperties({
      'LAST_BACKUP_SLOT': slot,
      'LAST_CONTENT_FINGERPRINT': signature,
      'LAST_BACKUP_FILE_ID': file.getId()
    });
    console.log('Saved ' + file.getName() + ' (' + file.getSize() + ' bytes)');
  } finally {
    lock.releaseLock();
  }
}
