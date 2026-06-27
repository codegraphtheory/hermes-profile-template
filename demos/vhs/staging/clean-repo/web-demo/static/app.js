const appWindow = document.querySelector('#window');
const promptPanel = document.querySelector('#promptPanel');
const progressPanel = document.querySelector('#progressPanel');
const sentence = document.querySelector('#sentence');
const generate = document.querySelector('#generate');
const stageList = document.querySelector('#stageList');
const activityLog = document.querySelector('#activityLog');
const fullActivityLog = document.querySelector('#fullActivityLog');
const statusDot = document.querySelector('#statusDot');
const statusLabel = document.querySelector('#statusLabel');
const currentActivity = document.querySelector('#currentActivity');
const headline = document.querySelector('#headline');
const inputEcho = document.querySelector('#inputEcho');
const newRun = document.querySelector('#newRun');
const progressBack = document.querySelector('#progressBack');
const resultsBack = document.querySelector('#resultsBack');
const errorBox = document.querySelector('#error');
const results = document.querySelector('#results');
const profileTitle = document.querySelector('#profileTitle');
const profilePath = document.querySelector('#profilePath');
const installCommand = document.querySelector('#installCommand');
const qualityPill = document.querySelector('#qualityPill');
const qualityChecks = document.querySelector('#qualityChecks');
const generatedFiles = document.querySelector('#generatedFiles');
const fileEmpty = document.querySelector('#fileEmpty');
const fileModal = document.querySelector('#fileModal');
const fileModalBackdrop = document.querySelector('#fileModalBackdrop');
const fileModalClose = document.querySelector('#fileModalClose');
const fileModalTitle = document.querySelector('#fileModalTitle');
const fileModalContent = document.querySelector('#fileModalContent');
const downloadZip = document.querySelector('#downloadZip');
const playDemo = document.querySelector('#playDemo');
const openLiveSession = document.querySelector('#openLiveSession');
const viewPrompt = document.querySelector('#viewPrompt');
const viewValidation = document.querySelector('#viewValidation');
const liveModal = document.querySelector('#liveModal');
const liveModalBackdrop = document.querySelector('#liveModalBackdrop');
const liveModalClose = document.querySelector('#liveModalClose');
const liveComposer = document.querySelector('#liveComposer');
const livePromptModal = document.querySelector('#livePromptModal');
const runLiveDemoModal = document.querySelector('#runLiveDemoModal');
const liveStatusModal = document.querySelector('#liveStatusModal');
const liveLogModal = document.querySelector('#liveLogModal');
const liveTranscript = document.querySelector('#liveTranscript');
const toggleLiveLog = document.querySelector('#toggleLiveLog');

const STAGES = [
  {
    id: 'prompt',
    title: 'Hermes prompt pass',
    detail: 'Calling Hermes to expand the sentence into a mature profile prompt.',
    panelTitle: 'Prompt engineering',
    panelBody: 'The simple sentence becomes a complete agent design brief that is preserved in docs/profile-prompt.md.',
    artifact: 'docs/profile-prompt.md'
  },
  {
    id: 'params',
    title: 'Generation params',
    detail: 'Writing profile.params.yaml with scope, refusals, toolsets, topics, and env placeholders.',
    panelTitle: 'Structured params',
    panelBody: 'The design brief is translated into deterministic YAML so the profile can be regenerated and reviewed.',
    artifact: 'templates/profile.params.yaml'
  },
  {
    id: 'repo',
    title: 'Profile repository',
    detail: 'Creating SOUL.md, distribution.yaml, README, config, scripts, docs, and bundled skills.',
    panelTitle: 'Installable repo',
    panelBody: 'The backend is assembling a real Hermes profile distribution, not a text mockup.',
    artifact: 'SOUL.md, distribution.yaml, skills/'
  },
  {
    id: 'demo',
    title: 'Demo',
    detail: 'Rendering a local demo page for this exact profile.',
    panelTitle: 'Demo surface',
    panelBody: 'A safe, publishable demo is created so viewers can understand how the generated profile behaves.',
    artifact: 'demo/index.html'
  },
  {
    id: 'validation',
    title: 'Hermes quality review',
    detail: 'Calling Hermes again to review the generated profile and produce demo talking points.',
    panelTitle: 'LLM review',
    panelBody: 'Hermes inspects the generated files and writes an honest quality review for the demo.',
    artifact: 'docs/llm-quality-review.md'
  }
];

let activeStage = 0;
let stageTimer = null;
let currentStatusUrl = null;
let currentJobId = null;
let jobEvents = null;
let currentState = 'prompt';

renderScaffold();
transitionTo('prompt', { immediate: true });
sentence.focus();

function transitionTo(nextState, options = {}) {
  if (!['prompt', 'progress', 'results'].includes(nextState)) return;
  const previousState = currentState;
  currentState = nextState;
  appWindow.dataset.state = nextState;
  for (const panel of [promptPanel, progressPanel, results]) {
    const isActive = panel.dataset.panel === nextState;
    panel.hidden = false;
    panel.classList.toggle('is-active', isActive);
    panel.classList.toggle('is-exiting', panel.dataset.panel === previousState && !isActive && !options.immediate);
    panel.setAttribute('aria-hidden', String(!isActive));
    if (!isActive) {
      window.setTimeout(() => {
        if (!panel.classList.contains('is-active')) panel.hidden = true;
        panel.classList.remove('is-exiting');
      }, options.immediate ? 0 : 360);
    }
  }
  if (nextState === 'prompt') window.setTimeout(() => sentence.focus(), options.immediate ? 0 : 220);
}

generate.addEventListener('click', startGeneration);
sentence.addEventListener('keydown', event => {
  if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
    event.preventDefault();
    startGeneration();
  }
});
newRun.addEventListener('click', resetExperience);
progressBack.addEventListener('click', resetExperience);
resultsBack.addEventListener('click', () => transitionTo('progress'));
liveComposer.addEventListener('submit', startLiveDemo);
livePromptModal.addEventListener('keydown', event => {
  if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
    event.preventDefault();
    liveComposer.requestSubmit();
  }
});
openLiveSession.addEventListener('click', openLiveModal);
toggleLiveLog.addEventListener('click', toggleLiveSessionLog);
liveModalClose.addEventListener('click', closeLiveModal);
liveModalBackdrop.addEventListener('click', closeLiveModal);
fileModalClose.addEventListener('click', closeFileModal);
fileModalBackdrop.addEventListener('click', closeFileModal);
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && !fileModal.hidden) closeFileModal();
  if (event.key === 'Escape' && !liveModal.hidden) closeLiveModal();
});

async function startGeneration() {
  const value = normalizeSentence(sentence.value);
  if (!value) return;
  sentence.value = value;
  transitionTo('progress');
  closeFileModal();
  closeLiveModal();
  errorBox.hidden = true;
  generate.disabled = true;
  inputEcho.textContent = value;
  headline.textContent = 'Building your Hermes profile';
  statusLabel.textContent = 'Starting';
  statusDot.className = 'status-dot';
  activeStage = 0;
  renderScaffold();
  renderActivity(['Submitting job']);

  try {
    const response = await fetch('/api/jobs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sentence: value })
    });
    const created = await response.json();
    if (!response.ok) throw new Error(created.error || 'failed to create job');
    currentStatusUrl = created.status_url;
    currentJobId = created.job_id;
    await streamJob(created.status_url, created.job_id);
  } catch (err) {
    showError(err.message || String(err));
  } finally {
    generate.disabled = false;
  }
}

async function poll(url) {
  for (;;) {
    const response = await fetch(url);
    const job = await response.json();
    renderJob(job);
    if (job.status === 'complete') return;
    if (job.status === 'failed') throw new Error(job.error || 'generation failed');
    await new Promise(resolve => setTimeout(resolve, 850));
  }
}

async function streamJob(statusUrl, jobId) {
  if (!window.EventSource) return poll(statusUrl);
  return new Promise((resolve, reject) => {
    let settled = false;
    jobEvents = new EventSource(`/api/jobs/${jobId}/events`);
    jobEvents.onmessage = event => {
      const job = JSON.parse(event.data);
      renderJob(job);
      if (job.status === 'complete') {
        settled = true;
        jobEvents.close();
        resolve();
      } else if (job.status === 'failed') {
        settled = true;
        jobEvents.close();
        reject(new Error(job.error || 'generation failed'));
      }
    };
    jobEvents.onerror = () => {
      jobEvents.close();
      if (!settled) poll(statusUrl).then(resolve).catch(reject);
    };
  });
}

function renderJob(job) {
  renderActivity(job.progress || []);
  if (job.status === 'queued') {
    statusLabel.textContent = 'Queued';
    return;
  }
  if (job.status === 'running') {
    statusLabel.textContent = 'Generating';
    const serverStep = typeof job.stage_index === 'number' ? job.stage_index : null;
    if (serverStep !== null) activeStage = Math.max(activeStage, Math.min(serverStep, STAGES.length - 1));
    renderScaffold();
    return;
  }
  if (job.status === 'complete') {
    clearInterval(stageTimer);
    activeStage = STAGES.length;
    statusLabel.textContent = 'Complete';
    statusDot.className = 'status-dot complete';
    headline.textContent = 'Your profile is ready';
    currentJobId = job.job_id || currentJobId;
    renderScaffold();
    renderResults(job.result);
    return;
  }
}

function tickStages() {
  if (activeStage < STAGES.length - 1) {
    activeStage += 1;
    renderScaffold();
  }
}

function renderActivity(items) {
  const latest = items[items.length - 1] || 'Waiting for work to start.';
  currentActivity.textContent = summarizeProgress(latest, true);
  currentActivity.title = latest;
  const visibleItems = compactProgress(items).slice(-6);
  activityLog.innerHTML = visibleItems.map((item, index, visible) => {
    const className = index === visible.length - 1 ? ' class="latest"' : '';
    return `<div${className} title="${escapeAttr(item.raw)}">${escapeHtml(item.label)}</div>`;
  }).join('');
  fullActivityLog.innerHTML = items.slice(-12).map((item, index, visible) => {
    const className = index === visible.length - 1 ? ' class="latest"' : '';
    return `<div${className}>${escapeHtml(item)}</div>`;
  }).join('');
  fullActivityLog.scrollTop = fullActivityLog.scrollHeight;
}

function compactProgress(items) {
  const compacted = [];
  let lastLabel = '';
  for (const raw of items) {
    const label = summarizeProgress(raw, false);
    if (label === lastLabel && !/\d+s/.test(label)) continue;
    compacted.push({ raw, label });
    lastLabel = label;
  }
  return compacted;
}

function summarizeProgress(message, detailed) {
  const text = String(message || '').trim();
  const elapsed = text.match(/\((\d+s elapsed)\)/);
  if (text.startsWith('Waiting for Hermes LLM response')) {
    return elapsed ? `Waiting for Hermes: ${elapsed[1].replace(' elapsed', '')}` : 'Waiting for Hermes';
  }
  if (text.startsWith('Hermes LLM call started')) return 'Hermes call started';
  if (text.startsWith('Using Hermes provider')) return text.replace('Using Hermes provider ', 'Using ');
  if (text.startsWith('Reading profile idea')) return 'Preparing prompt';
  if (text.startsWith('Starting Hermes prompt')) return 'Starting prompt pass';
  if (text.startsWith('Hermes expanded')) return 'Prompt expanded';
  if (text.startsWith('Prompt pass complete')) return 'Preparing generator';
  if (text.startsWith('Launching profile repository generator')) return 'Launching generator';
  if (text.startsWith('Generator process started')) return 'Writing profile repo';
  if (text.startsWith('Generator still running')) return elapsed ? `Writing files: ${elapsed[1].replace(' elapsed', '')}` : 'Writing files';
  if (text.startsWith('Profile repository created')) return 'Repo created';
  if (text.startsWith('Mature prompt written')) return 'Prompt saved';
  if (text.startsWith('Playable demo written')) return 'Demo saved';
  if (text.startsWith('Generator validation passed')) return 'Validation passed';
  if (text.startsWith('Indexed ')) return text.replace(' important generated files for inline inspection', ' files indexed');
  if (text.startsWith('Preview ready:')) return detailed ? text : 'File previews ready';
  if (text.startsWith('Download package ready')) return 'Zip ready';
  return detailed || text.length <= 42 ? text : `${text.slice(0, 39)}...`;
}

function renderScaffold() {
  stageList.innerHTML = STAGES.map((stage, index) => {
    const state = index < activeStage ? 'done' : index === activeStage ? 'active' : 'pending';
    const marker = index < activeStage ? '✓' : String(index + 1).padStart(2, '0');
    return `
      <li class="stage ${state}">
        <span class="stage-index">${marker}</span>
        <span>
          <span class="stage-title">${escapeHtml(stage.title)}</span>
        </span>
      </li>`;
  }).join('');
}

function renderResults(result) {
  profileTitle.textContent = result.display_name;
  profilePath.textContent = result.profile_dir;
  installCommand.textContent = result.install_command;
  qualityPill.textContent = result.quality_summary || 'Validated';
  qualityChecks.innerHTML = (result.quality_checks || []).map(check => `
    <div class="quality-check">
      <b>✓</b>
      <span>${escapeHtml(check)}</span>
    </div>`).join('');
  const files = result.generated_files || [];
  fileEmpty.hidden = files.length > 0;
  generatedFiles.innerHTML = files.map(file => `
    <button class="file-row" type="button" data-url="${escapeAttr(file.url || '')}" data-path="${escapeAttr(file.path || file)}">
      <span>${escapeHtml(file.path || file)}</span>
      <small>${escapeHtml(file.role || 'Inspect')}</small>
    </button>`).join('');
  generatedFiles.querySelectorAll('.file-row').forEach(button => {
    button.addEventListener('click', () => loadFilePreview(button.dataset.url, button.dataset.path));
  });
  downloadZip.href = result.zip_url;
  playDemo.href = result.demo_url;
  viewPrompt.href = result.prompt_url;
  viewValidation.href = result.validation_url;
  openLiveSession.disabled = false;
  runLiveDemoModal.disabled = false;
  setLiveStatus('Ready to call Hermes with the generated profile.');
  liveLogModal.innerHTML = '';
  transitionTo('results');
}

async function startLiveDemo(event) {
  if (event) event.preventDefault();
  if (!currentJobId) return;
  const message = livePromptModal.value.trim();
  if (!message) return;
  appendChatMessage('user', message);
  livePromptModal.value = '';
  const pending = appendChatMessage('assistant', 'Hermes is thinking...');
  setLiveRunning(true);
  setLiveStatus('Starting live Hermes call');
  renderLiveLog(['Submitting live Hermes request']);
  try {
    const response = await fetch(`/api/jobs/${currentJobId}/live-demo`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
    const created = await response.json();
    if (!response.ok) throw new Error(created.error || 'failed to start live demo');
    await pollLiveDemo(created.status_url, pending);
  } catch (err) {
    setLiveStatus('Live demo failed');
    pending.querySelector('.message-body').textContent = err.message || String(err);
    pending.classList.add('failed-message');
  } finally {
    setLiveRunning(false);
    livePromptModal.focus();
  }
}

async function pollLiveDemo(url, pendingMessage) {
  for (;;) {
    const response = await fetch(url);
    const run = await response.json();
    if (!response.ok) throw new Error(run.error || 'live demo failed');
    renderLiveRun(run, pendingMessage);
    if (run.status === 'complete') return;
    if (run.status === 'failed') throw new Error(run.error || 'live demo failed');
    await new Promise(resolve => setTimeout(resolve, 650));
  }
}

function renderLiveRun(run, pendingMessage) {
  setLiveStatus(run.status === 'complete' ? 'Hermes response received' : 'Hermes is working');
  renderLiveLog(run.progress || []);
  if (run.response) {
    pendingMessage.querySelector('.message-body').textContent = run.response;
    pendingMessage.classList.remove('pending-message');
    scrollTranscriptToBottom();
  }
}

function renderLiveLog(items) {
  liveLogModal.innerHTML = items.slice(-24).map((item, index, visible) => {
    const className = index === visible.length - 1 ? ' class="latest"' : '';
    return `<div${className}>${escapeHtml(item)}</div>`;
  }).join('');
  liveLogModal.scrollTop = liveLogModal.scrollHeight;
}

function setLiveStatus(message) {
  liveStatusModal.textContent = message;
}

function setLiveRunning(isRunning) {
  runLiveDemoModal.disabled = isRunning;
}

function appendChatMessage(role, text) {
  const message = document.createElement('div');
  message.className = `message ${role === 'user' ? 'user-message' : 'assistant-message'}${role === 'assistant' && text.endsWith('...') ? ' pending-message' : ''}`;
  message.innerHTML = `
    <div class="message-role">${role === 'user' ? 'You' : 'Hermes'}</div>
    <div class="message-body"></div>`;
  message.querySelector('.message-body').textContent = text;
  liveTranscript.appendChild(message);
  scrollTranscriptToBottom();
  return message;
}

function scrollTranscriptToBottom() {
  liveTranscript.scrollTop = liveTranscript.scrollHeight;
}

function toggleLiveSessionLog() {
  liveLogModal.hidden = !liveLogModal.hidden;
  toggleLiveLog.textContent = liveLogModal.hidden ? 'Show log' : 'Hide log';
}

function resetLiveTranscript() {
  liveTranscript.innerHTML = `
    <div class="message assistant-message">
      <div class="message-role">Hermes</div>
      <div class="message-body">Generate a profile, then ask the agent anything here. This fullscreen session calls the generated Hermes profile, not the static preview.</div>
    </div>`;
}

async function loadFilePreview(url, path) {
  if (!url) return;
  fileModal.hidden = false;
  document.body.classList.add('modal-open');
  fileModalTitle.textContent = `Loading ${path}`;
  fileModalContent.textContent = '';
  try {
    const response = await fetch(url);
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || 'failed to load file');
    fileModalTitle.textContent = payload.path + (payload.truncated ? ' (truncated)' : '');
    fileModalContent.textContent = payload.content;
    fileModalClose.focus();
  } catch (err) {
    fileModalTitle.textContent = path || 'File preview';
    fileModalContent.textContent = err.message || String(err);
  }
}

function closeFileModal() {
  fileModal.hidden = true;
  document.body.classList.remove('modal-open');
}

function openLiveModal() {
  liveModal.hidden = false;
  document.body.classList.add('modal-open');
  livePromptModal.focus();
}

function closeLiveModal() {
  liveModal.hidden = true;
  document.body.classList.remove('modal-open');
}

function resetExperience() {
  clearInterval(stageTimer);
  if (jobEvents) jobEvents.close();
  jobEvents = null;
  currentStatusUrl = null;
  currentJobId = null;
  activeStage = 0;
  transitionTo('prompt');
  closeFileModal();
  closeLiveModal();
  fileModalContent.textContent = '';
  liveLogModal.innerHTML = '';
  resetLiveTranscript();
  setLiveStatus('Ready after generation completes.');
  setLiveRunning(false);
  errorBox.hidden = true;
  generate.disabled = false;
  statusDot.className = 'status-dot';
  statusLabel.textContent = 'Waiting';
  currentActivity.textContent = 'No job running.';
  fullActivityLog.innerHTML = '';
  headline.textContent = 'Building your Hermes profile';
  renderScaffold();
  renderActivity([]);
  setTimeout(() => {
    sentence.focus();
    sentence.select();
  }, 120);
}

function showError(message) {
  clearInterval(stageTimer);
  statusLabel.textContent = 'Failed';
  statusDot.className = 'status-dot failed';
  headline.textContent = 'Generation failed';
  errorBox.textContent = message;
  errorBox.hidden = false;
}

function normalizeSentence(value) {
  return value.trim();
}

function escapeAttr(value) {
  return escapeHtml(value).replace(/`/g, '&#96;');
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'\"]/g, char => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&#39;',
    '"': '&quot;'
  })[char]);
}
