const sentence = document.querySelector('#sentence');
const generate = document.querySelector('#generate');
const sample = document.querySelector('#sample');
const statusPanel = document.querySelector('#statusPanel');
const progress = document.querySelector('#progress');
const errorBox = document.querySelector('#error');
const results = document.querySelector('#results');
const profileTitle = document.querySelector('#profileTitle');
const profilePath = document.querySelector('#profilePath');
const installCommand = document.querySelector('#installCommand');
const downloadZip = document.querySelector('#downloadZip');
const playDemo = document.querySelector('#playDemo');
const viewDiagram = document.querySelector('#viewDiagram');
const viewPrompt = document.querySelector('#viewPrompt');
const viewValidation = document.querySelector('#viewValidation');
const diagramFrame = document.querySelector('#diagramFrame');

sample.addEventListener('click', () => {
  sentence.value = 'a support ticket triage agent';
});

generate.addEventListener('click', async () => {
  const value = sentence.value.trim();
  if (!value) return;
  generate.disabled = true;
  statusPanel.hidden = false;
  results.hidden = true;
  errorBox.hidden = true;
  progress.innerHTML = '<li>Submitting job</li>';
  try {
    const response = await fetch('/api/jobs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sentence: value })
    });
    const created = await response.json();
    if (!response.ok) throw new Error(created.error || 'failed to create job');
    await poll(created.status_url);
  } catch (err) {
    showError(err.message || String(err));
  } finally {
    generate.disabled = false;
  }
});

async function poll(url) {
  for (;;) {
    const response = await fetch(url);
    const job = await response.json();
    renderJob(job);
    if (job.status === 'complete') return;
    if (job.status === 'failed') throw new Error(job.error || 'generation failed');
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
}

function renderJob(job) {
  const items = job.progress || [job.status || 'running'];
  progress.innerHTML = items.map(item => `<li>${escapeHtml(item)}</li>`).join('');
  if (job.status === 'complete') {
    const result = job.result;
    profileTitle.textContent = result.display_name;
    profilePath.textContent = result.profile_dir;
    installCommand.textContent = result.install_command;
    downloadZip.href = result.zip_url;
    playDemo.href = result.demo_url;
    viewDiagram.href = result.diagram_url;
    viewPrompt.href = result.prompt_url;
    viewValidation.href = result.validation_url;
    diagramFrame.src = result.diagram_url;
    results.hidden = false;
  }
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = false;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, char => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&#39;',
    '"': '&quot;'
  })[char]);
}
