const appWindow = document.querySelector('#window');
const composerPane = document.querySelector('#composerPane');
const sentence = document.querySelector('#sentence');
const generate = document.querySelector('#generate');
const workbench = document.querySelector('#workbench');
const stageList = document.querySelector('#stageList');
const activityLog = document.querySelector('#activityLog');
const panelGrid = document.querySelector('#panelGrid');
const statusDot = document.querySelector('#statusDot');
const statusLabel = document.querySelector('#statusLabel');
const headline = document.querySelector('#headline');
const inputEcho = document.querySelector('#inputEcho');
const newRun = document.querySelector('#newRun');
const errorBox = document.querySelector('#error');
const results = document.querySelector('#results');
const profileTitle = document.querySelector('#profileTitle');
const profilePath = document.querySelector('#profilePath');
const installCommand = document.querySelector('#installCommand');
const qualityPill = document.querySelector('#qualityPill');
const qualityChecks = document.querySelector('#qualityChecks');
const generatedFiles = document.querySelector('#generatedFiles');
const filePreview = document.querySelector('#filePreview');
const filePreviewTitle = document.querySelector('#filePreviewTitle');
const filePreviewContent = document.querySelector('#filePreviewContent');
const downloadZip = document.querySelector('#downloadZip');
const playDemo = document.querySelector('#playDemo');
const openDemoInline = document.querySelector('#openDemoInline');
const viewDiagram = document.querySelector('#viewDiagram');
const viewPrompt = document.querySelector('#viewPrompt');
const viewValidation = document.querySelector('#viewValidation');
const demoFrame = document.querySelector('#demoFrame');
const diagramFrame = document.querySelector('#diagramFrame');

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
    title: 'Playable demo',
    detail: 'Rendering a static mini conversation and a local demo page for this exact profile.',
    panelTitle: 'Demo surface',
    panelBody: 'A safe, publishable demo is created so viewers can understand how the generated profile behaves.',
    artifact: 'demo/index.html'
  },
  {
    id: 'diagram',
    title: 'Output diagram',
    detail: 'Drawing the profile contents map and how the sentence became an installable repo.',
    panelTitle: 'Contents diagram',
    panelBody: 'The diagram explains the generated files and why each part exists.',
    artifact: 'docs/output-diagram.svg'
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

renderScaffold();
sentence.focus();

generate.addEventListener('click', startGeneration);
sentence.addEventListener('keydown', event => {
  if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
    event.preventDefault();
    startGeneration();
  }
});
newRun.addEventListener('click', resetExperience);

async function startGeneration() {
  const value = normalizeSentence(sentence.value);
  if (!value) return;
  sentence.value = value;
  appWindow.classList.add('is-working');
  workbench.hidden = false;
  results.hidden = true;
  filePreview.hidden = true;
  filePreviewContent.textContent = '';
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
    await poll(created.status_url);
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
  activityLog.innerHTML = items.slice(-8).map(item => `<div>${escapeHtml(item)}</div>`).join('');
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
          <span class="stage-detail">${escapeHtml(stage.detail)}</span>
        </span>
      </li>`;
  }).join('');

  panelGrid.innerHTML = STAGES.slice(0, Math.max(1, Math.min(activeStage + 1, STAGES.length))).map((stage, index) => {
    const state = index < activeStage ? 'done' : index === activeStage ? 'active' : 'pending';
    return `
      <article class="work-panel panel ${state}" style="animation-delay:${index * 70}ms">
        <span>${String(index + 1).padStart(2, '0')} ${escapeHtml(stage.title)}</span>
        <h3>${escapeHtml(stage.panelTitle)}</h3>
        <p>${escapeHtml(stage.panelBody)}</p>
        <code>${escapeHtml(stage.artifact)}</code>
      </article>`;
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
  generatedFiles.innerHTML = (result.generated_files || []).map(file => `
    <button class="file-row" type="button" data-url="${escapeAttr(file.url || '')}" data-path="${escapeAttr(file.path || file)}">
      <span>${escapeHtml(file.path || file)}</span>
      <small>${escapeHtml(file.role || '')}</small>
    </button>`).join('');
  generatedFiles.querySelectorAll('.file-row').forEach(button => {
    button.addEventListener('click', () => loadFilePreview(button.dataset.url, button.dataset.path));
  });
  const firstFile = result.generated_files && result.generated_files[0];
  if (firstFile && firstFile.url) loadFilePreview(firstFile.url, firstFile.path);
  downloadZip.href = result.zip_url;
  playDemo.href = result.demo_url;
  openDemoInline.href = result.demo_url;
  viewDiagram.href = result.diagram_url;
  viewPrompt.href = result.prompt_url;
  viewValidation.href = result.validation_url;
  demoFrame.src = result.demo_url;
  diagramFrame.src = result.diagram_url;
  results.hidden = false;
}

async function loadFilePreview(url, path) {
  if (!url) return;
  filePreview.hidden = false;
  filePreviewTitle.textContent = `Loading ${path}`;
  filePreviewContent.textContent = '';
  try {
    const response = await fetch(url);
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || 'failed to load file');
    filePreviewTitle.textContent = payload.path + (payload.truncated ? ' (truncated)' : '');
    filePreviewContent.textContent = payload.content;
  } catch (err) {
    filePreviewTitle.textContent = path || 'File preview';
    filePreviewContent.textContent = err.message || String(err);
  }
}

function resetExperience() {
  clearInterval(stageTimer);
  currentStatusUrl = null;
  activeStage = 0;
  appWindow.classList.remove('is-working');
  workbench.hidden = true;
  results.hidden = true;
  filePreview.hidden = true;
  filePreviewContent.textContent = '';
  errorBox.hidden = true;
  generate.disabled = false;
  statusDot.className = 'status-dot';
  statusLabel.textContent = 'Waiting';
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
