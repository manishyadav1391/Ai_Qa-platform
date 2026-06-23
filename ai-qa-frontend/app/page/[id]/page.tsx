"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import api from "@/services/api";

interface PageInfo {
  id: number;
  title: string;
  url: string;
  status_code: number;
  depth: number;
  crawl_date: string;
  elements: {
    id: number;
    element_type: string;
    name: string;
    locator: string;
    text: string;
  }[];
  testcases: {
    id: number;
    title: string;
    category: string;
    priority: string;
    expected_result: string;
    source: string;
  }[];
  scripts: {
    id: number;
    script_name: string;
    framework: string;
    generation_type: string;
    version: number;
  }[];
  executions: {
    id: number;
    status: string;
    duration: number;
    started_at: string;
    completed_at: string;
  }[];
}

interface TestCase {
  id: number;
  title: string;
  category: string;
  priority: string;
  expected_result: string;
  source: string;
  generated_by: string;
}

interface ScriptInfo {
  script_id: number;
  version: number;
  script_name: string;
  generation_type: string;
  script: string;
}

interface ExecutionResult {
  execution_id: number;
  page_id: number;
  status: string;
  duration: number;
  error: string;
}

interface ExecutionDetail {
  execution_id: number;
  page_id: number;
  script_id: number;
  status: string;
  duration: number;
  started_at: string;
  completed_at: string;
  error_message: string;
  execution_log: string;
  screenshot_path: string;
}

export default function PageDetailPage() {
  const params = useParams();
  const pageId = params.id;

  const [pageInfo, setPageInfo] = useState<PageInfo | null>(null);
  const [testcases, setTestcases] = useState<TestCase[]>([]);
  const [script, setScript] = useState<ScriptInfo | null>(null);
  const [executions, setExecutions] = useState<ExecutionDetail[]>([]);
  const [reportData, setReportData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  // Action states
  const [generatingTests, setGeneratingTests] = useState(false);
  const [generatingAiTests, setGeneratingAiTests] = useState(false);
  const [generatingScript, setGeneratingScript] = useState(false);
  const [generatingAiScript, setGeneratingAiScript] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [lastExecResult, setLastExecResult] = useState<ExecutionResult | null>(null);

  // UI state
  const [activeTab, setActiveTab] = useState<"overview" | "tests" | "script" | "results" | "report">("overview");
  const [toast, setToast] = useState<{ msg: string; type: "success" | "error" } | null>(null);

  useEffect(() => {
    loadAll();
  }, []);

  function showToast(msg: string, type: "success" | "error" = "success") {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 4000);
  }

  async function loadAll() {
    try {
      const [detailRes, testsRes, scriptRes, execsRes, reportRes] = await Promise.allSettled([
        api.get(`/pages/detail/${pageId}`),
        api.get(`/testcases/${pageId}`),
        api.get(`/scripts/${pageId}`),
        api.get(`/execution/history/${pageId}`),
        api.get(`/execution/report/${pageId}`),
      ]);

      if (detailRes.status === "fulfilled") setPageInfo(detailRes.value.data);
      if (testsRes.status === "fulfilled") setTestcases(testsRes.value.data);
      if (scriptRes.status === "fulfilled" && !scriptRes.value.data.error)
        setScript(scriptRes.value.data);
      if (reportRes.status === "fulfilled") setReportData(reportRes.value.data);
      if (execsRes.status === "fulfilled") {
        // Load detailed info for last 5 executions
        const execList = execsRes.value.data.slice(0, 10);
        const detailedExecs: ExecutionDetail[] = [];
        for (const exec of execList) {
          try {
            const res = await api.get(`/execution/${exec.execution_id}`);
            detailedExecs.push(res.data);
          } catch {
            detailedExecs.push({
              execution_id: exec.execution_id,
              page_id: Number(pageId),
              script_id: 0,
              status: exec.status,
              duration: exec.duration,
              started_at: exec.started_at,
              completed_at: exec.completed_at,
              error_message: "",
              execution_log: "",
              screenshot_path: "",
            });
          }
        }
        setExecutions(detailedExecs);
      }
    } catch (err) {
      console.error("Failed to load page data", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateTests() {
    setGeneratingTests(true);
    try {
      const res = await api.post(`/testcases/generate/${pageId}`);
      showToast(`✓ Generated ${res.data.generated} rule-based test cases`);
      const testsRes = await api.get(`/testcases/${pageId}`);
      setTestcases(testsRes.data);
      setActiveTab("tests");
    } catch (err) {
      console.error(err);
      showToast("Failed to generate tests", "error");
    } finally {
      setGeneratingTests(false);
    }
  }

  async function handleGenerateAiTests() {
    setGeneratingAiTests(true);
    try {
      const res = await api.post(`/ai/generate/${pageId}`);
      showToast(`✓ AI generated ${res.data.saved} additional test cases`);
      const testsRes = await api.get(`/testcases/${pageId}`);
      setTestcases(testsRes.data);
      setActiveTab("tests");
    } catch (err) {
      console.error(err);
      showToast("AI test generation failed — check server logs", "error");
    } finally {
      setGeneratingAiTests(false);
    }
  }

  async function handleGenerateScript() {
    setGeneratingScript(true);
    try {
      const res = await api.post(`/scripts/generate/${pageId}`);
      showToast(`✓ Script generated — v${res.data.version}`);
      const scriptRes = await api.get(`/scripts/${pageId}`);
      if (!scriptRes.data.error) setScript(scriptRes.data);
      setActiveTab("script");
    } catch (err) {
      console.error(err);
      showToast("Script generation failed", "error");
    } finally {
      setGeneratingScript(false);
    }
  }

  async function handleGenerateAiScript() {
    setGeneratingAiScript(true);
    try {
      const res = await api.post(`/scripts/ai-generate/${pageId}`);
      showToast(`✓ AI script generated — v${res.data.version}`);
      const scriptRes = await api.get(`/scripts/${pageId}`);
      if (!scriptRes.data.error) setScript(scriptRes.data);
      setActiveTab("script");
    } catch (err) {
      console.error(err);
      showToast("AI script generation failed — check server logs", "error");
    } finally {
      setGeneratingAiScript(false);
    }
  }

  async function handleExecute() {
    setExecuting(true);
    setLastExecResult(null);
    try {
      const res = await api.post(`/execution/run/${pageId}`);
      const result = res.data;
      setLastExecResult(result);
      if (result.status === "PASS") {
        showToast(`✓ Test PASSED in ${result.duration}s`);
      } else {
        showToast(`✕ Test FAILED in ${result.duration}s`, "error");
      }
      // Reload executions & report
      const [execsRes, reportRes] = await Promise.allSettled([
        api.get(`/execution/history/${pageId}`),
        api.get(`/execution/report/${pageId}`)
      ]);

      if (reportRes.status === "fulfilled") {
        setReportData(reportRes.value.data);
      }

      if (execsRes.status === "fulfilled") {
        const execList = execsRes.value.data.slice(0, 10);
        const detailedExecs: ExecutionDetail[] = [];
        for (const exec of execList) {
          try {
            const r = await api.get(`/execution/${exec.execution_id}`);
            detailedExecs.push(r.data);
          } catch {
            detailedExecs.push({ ...exec, execution_id: exec.execution_id, page_id: Number(pageId), script_id: 0, error_message: "", execution_log: "", screenshot_path: "" });
          }
        }
        setExecutions(detailedExecs);
      }
      setActiveTab("results");
    } catch (err) {
      console.error(err);
      showToast("Execution failed — check if script exists", "error");
    } finally {
      setExecuting(false);
    }
  }

  async function handleDownloadReport() {
    try {
      const res = await api.get(`/execution/report/${pageId}`);
      const data = res.data;

      const escapeHtml = (text: string) => {
        if (!text) return "";
        return text
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;")
          .replace(/"/g, "&quot;")
          .replace(/'/g, "&#039;");
      };

      const testcaseRows = data.testcases.map((tc: any) => `
        <tr>
          <td>
            <strong style="color: var(--fg); font-size: 14px;">${escapeHtml(tc.title)}</strong><br>
            <span style="font-size: 12.5px; color: var(--text-sec); display: inline-block; margin-top: 4px;">${escapeHtml(tc.expected_result)}</span>
          </td>
          <td><span class="badge badge--neutral">${escapeHtml(tc.category)}</span></td>
          <td><span class="badge ${tc.priority?.toLowerCase() === 'high' ? 'badge--danger' : tc.priority?.toLowerCase() === 'medium' ? 'badge--warning' : 'badge--neutral'}">${escapeHtml(tc.priority)}</span></td>
          <td><span class="badge ${tc.source === 'ai' ? 'badge--info' : 'badge--success'}">${tc.source === 'ai' ? 'AI' : 'Rules'}</span></td>
        </tr>
      `).join('');

      const executionRows = data.executions.map((ex: any) => `
        <tr>
          <td class="mono" style="font-weight: 600; color: var(--fg);">#${ex.id}</td>
          <td>
            <span class="badge ${ex.status === 'PASS' ? 'badge--success' : 'badge--danger'}">
              ${escapeHtml(ex.status)}
            </span>
          </td>
          <td>${ex.duration ? ex.duration.toFixed(2) + 's' : '—'}</td>
          <td>${formatDate(ex.started_at)}</td>
        </tr>
      `).join('');

      const executionDetails = data.executions.slice(0, 3).map((ex: any) => {
        if (!ex.execution_log && !ex.error_message) return '';
        return `
          <div style="margin-top: 24px; border-bottom: 1px solid var(--border); padding-bottom: 24px;">
            <h4 style="margin: 0 0 12px 0; font-size: 14px; font-weight: 600; color: var(--fg);">Execution Run #${ex.id} Details</h4>
            ${ex.error_message ? `
              <div style="margin-bottom: 14px;">
                <div style="font-size: 11px; text-transform: uppercase; color: var(--danger); font-weight: 600; margin-bottom: 6px; letter-spacing: 0.5px;">Error Output</div>
                <div class="code-viewer"><pre class="error-pre">${escapeHtml(ex.error_message)}</pre></div>
              </div>
            ` : ''}
            ${ex.execution_log ? `
              <div>
                <div style="font-size: 11px; text-transform: uppercase; color: var(--text-sec); font-weight: 600; margin-bottom: 6px; letter-spacing: 0.5px;">Execution Log</div>
                <div class="code-viewer"><pre>${escapeHtml(ex.execution_log)}</pre></div>
              </div>
            ` : ''}
          </div>
        `;
      }).join('');

      const scriptContent = script ? script.script : "No script generated for this page.";

      const htmlContent = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escapeHtml(data.report_title)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0b0d14;
      --fg: #e4e7ef;
      --surface-1: #111421;
      --surface-2: #181c2e;
      --surface-3: #1e2338;
      --border: rgba(255, 255, 255, 0.08);
      --accent: #6c5ce7;
      --success: #10b981;
      --success-bg: rgba(16, 185, 129, 0.1);
      --danger: #ef4444;
      --danger-bg: rgba(239, 68, 68, 0.1);
      --warning: #f59e0b;
      --warning-bg: rgba(245, 158, 11, 0.1);
      --info: #3b82f6;
      --info-bg: rgba(59, 130, 246, 0.1);
      --text-sec: #8890a4;
      --text-mut: #545b70;
    }
    body {
      background: var(--bg);
      color: var(--fg);
      font-family: 'Inter', sans-serif;
      margin: 0;
      padding: 40px;
    }
    .container {
      max-width: 1000px;
      margin: 0 auto;
    }
    .header {
      margin-bottom: 30px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 20px;
    }
    .title {
      font-size: 28px;
      font-weight: 700;
      margin: 0 0 8px 0;
      letter-spacing: -0.5px;
    }
    .subtitle {
      color: var(--text-sec);
      font-size: 14px;
      margin: 0;
    }
    .meta-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 30px;
    }
    .card {
      background: var(--surface-2);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
      position: relative;
    }
    .card-title {
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      color: var(--text-mut);
      letter-spacing: 0.8px;
      margin-bottom: 8px;
    }
    .card-value {
      font-size: 24px;
      font-weight: 700;
      margin: 0;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      padding: 4px 8px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
      line-height: 1;
    }
    .badge--success { background: var(--success-bg); color: var(--success); }
    .badge--danger { background: var(--danger-bg); color: var(--danger); }
    .badge--warning { background: var(--warning-bg); color: var(--warning); }
    .badge--info { background: var(--info-bg); color: var(--info); }
    .badge--neutral { background: rgba(255, 255, 255, 0.05); color: var(--text-sec); }
    
    .section-title {
      font-size: 18px;
      font-weight: 600;
      margin: 40px 0 16px 0;
      border-left: 3px solid var(--accent);
      padding-left: 10px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      background: var(--surface-2);
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
      margin-bottom: 30px;
    }
    th {
      text-align: left;
      padding: 12px 20px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      color: var(--text-mut);
      background: rgba(0, 0, 0, 0.15);
      border-bottom: 1px solid var(--border);
      letter-spacing: 0.8px;
    }
    td {
      padding: 14px 20px;
      font-size: 13.5px;
      border-bottom: 1px solid var(--border);
      color: var(--text-sec);
      vertical-align: middle;
    }
    tr:last-child td {
      border-bottom: none;
    }
    .mono {
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
    }
    .code-viewer {
      background: var(--surface-1);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px;
      overflow-x: auto;
      max-height: 400px;
    }
    pre {
      margin: 0;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12.5px;
      line-height: 1.6;
      color: var(--text-sec);
    }
    .error-pre {
      color: var(--danger);
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1 class="title">${escapeHtml(data.report_title)}</h1>
      <p class="subtitle">Generated dynamically on ${formatDate(data.generated_at)} for <a href="${escapeHtml(data.page.url)}" target="_blank" style="color: var(--accent); text-decoration: none;">${escapeHtml(data.page.url)}</a></p>
    </div>

    <div class="meta-grid">
      <div class="card">
        <div class="card-title">Pass Rate</div>
        <div class="card-value" style="color: ${parseFloat(data.summary.pass_rate) >= 80 ? 'var(--success)' : parseFloat(data.summary.pass_rate) >= 50 ? 'var(--warning)' : 'var(--danger)'};">${data.summary.total_executions > 0 ? data.summary.pass_rate : 'N/A'}</div>
      </div>
      <div class="card">
        <div class="card-title">Executions</div>
        <div class="card-value">${data.summary.passed} passed / ${data.summary.total_executions} runs</div>
      </div>
      <div class="card">
        <div class="card-title">Test Cases Coverage</div>
        <div class="card-value">${data.summary.total_testcases} cases</div>
      </div>
    </div>

    <h2 class="section-title">Test Cases Details</h2>
    <table>
      <thead>
        <tr>
          <th>Test Case</th>
          <th>Category</th>
          <th>Priority</th>
          <th>Source</th>
        </tr>
      </thead>
      <tbody>
        ${testcaseRows || '<tr><td colspan="4" style="text-align: center;">No test cases defined.</td></tr>'}
      </tbody>
    </table>

    <h2 class="section-title">Automation Playwright Script</h2>
    <div class="code-viewer">
      <pre>${escapeHtml(scriptContent)}</pre>
    </div>

    <h2 class="section-title">Execution History</h2>
    <table>
      <thead>
        <tr>
          <th>Run ID</th>
          <th>Status</th>
          <th>Duration</th>
          <th>Time</th>
        </tr>
      </thead>
      <tbody>
        ${executionRows || '<tr><td colspan="4" style="text-align: center;">No executions recorded.</td></tr>'}
      </tbody>
    </table>

    ${executionDetails ? `
      <h2 class="section-title">Execution Logs</h2>
      <div class="card" style="padding: 24px;">
        ${executionDetails}
      </div>
    ` : ''}
  </div>
</body>
</html>`;

      const blob = new Blob([htmlContent], {
        type: "text/html;charset=utf-8",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `qa-report-page-${pageId}.html`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showToast("✓ Professional HTML Report downloaded");
    } catch (err) {
      console.error(err);
      showToast("Failed to download report", "error");
    }
  }

  function getPriorityClass(priority: string) {
    const p = priority?.toLowerCase();
    if (p === "high") return "badge--danger";
    if (p === "medium") return "badge--warning";
    return "badge--neutral";
  }

  function formatDate(dateStr: string | null) {
    if (!dateStr) return "—";
    const d = new Date(dateStr);
    return d.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  if (loading) {
    return (
      <div>
        <div className="page-header">
          <div className="breadcrumb">
            <Link href="/">Dashboard</Link>
            <span className="breadcrumb-sep">/</span>
            <Link href="/projects">Projects</Link>
            <span className="breadcrumb-sep">/</span>
            <span>Loading...</span>
          </div>
          <h1 className="page-title">Loading Page...</h1>
        </div>
        <div className="stats-grid">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="stat-card">
              <div className="skeleton" style={{ width: "50%", height: 12, marginBottom: 12 }} />
              <div className="skeleton" style={{ width: "40%", height: 28 }} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Toast */}
      {toast && (
        <div className={`toast animate-in animate-in-1 ${toast.type === "success" ? "toast--success" : "toast--error"}`}>
          {toast.msg}
          <button className="toast-close" onClick={() => setToast(null)}>✕</button>
        </div>
      )}

      {/* Header */}
      <div className="page-header">
        <div className="breadcrumb">
          <Link href="/">Dashboard</Link>
          <span className="breadcrumb-sep">/</span>
          <Link href="/projects">Projects</Link>
          <span className="breadcrumb-sep">/</span>
          <span>{pageInfo?.title || `Page #${pageId}`}</span>
        </div>

        <div className="page-header-row">
          <div>
            <h1 className="page-title">{pageInfo?.title || "Page Detail"}</h1>
            <p className="page-subtitle">{pageInfo?.url}</p>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              id="download-report-btn"
              className="btn btn-secondary"
              onClick={handleDownloadReport}
            >
              📥 Download Report
            </button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="stats-grid">
        <div 
          className="stat-card stat-card--blue stat-card--interactive animate-in animate-in-1"
          onClick={() => setActiveTab("overview")}
        >
          <div className="stat-label">Elements</div>
          <div className="stat-value">{pageInfo?.elements.length || 0}</div>
          <div className="stat-icon stat-icon--blue">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="20" height="20">
              <polyline points="16 18 22 12 16 6" />
              <polyline points="8 6 2 12 8 18" />
            </svg>
          </div>
        </div>
        <div 
          className="stat-card stat-card--green stat-card--interactive animate-in animate-in-2"
          onClick={() => setActiveTab("tests")}
        >
          <div className="stat-label">Test Cases</div>
          <div className="stat-value">{testcases.length}</div>
          <div className="stat-icon stat-icon--green">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="20" height="20">
              <path d="M9 11l3 3L22 4" />
              <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
            </svg>
          </div>
        </div>
        <div 
          className="stat-card stat-card--purple stat-card--interactive animate-in animate-in-3"
          onClick={() => setActiveTab("script")}
        >
          <div className="stat-label">Script</div>
          <div className="stat-value" style={{ fontSize: script ? 22 : 32 }}>
            {script ? `v${script.version}` : "—"}
          </div>
          <div className="stat-icon stat-icon--purple">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="20" height="20">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
          </div>
        </div>
        <div 
          className="stat-card stat-card--orange stat-card--interactive animate-in animate-in-4"
          onClick={() => setActiveTab("results")}
        >
          <div className="stat-label">Executions</div>
          <div className="stat-value">{executions.length}</div>
          <div className="stat-icon stat-icon--orange">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="20" height="20">
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
          </div>
        </div>
      </div>

      {/* Workflow Action Bar */}
      <div className="workflow-bar animate-in animate-in-5">
        <div className="workflow-bar-title">Workflow Actions</div>
        <div className="workflow-bar-actions">
          <button
            id="gen-tests-btn"
            className="btn btn-secondary btn-sm"
            onClick={handleGenerateTests}
            disabled={generatingTests}
          >
            {generatingTests ? "Generating..." : "🧪 Generate Tests"}
          </button>
          <button
            id="gen-ai-tests-btn"
            className="btn btn-secondary btn-sm"
            onClick={handleGenerateAiTests}
            disabled={generatingAiTests}
          >
            {generatingAiTests ? "AI Working..." : "🤖 AI Tests"}
          </button>
          <span className="workflow-divider" />
          <button
            id="gen-script-btn"
            className="btn btn-secondary btn-sm"
            onClick={handleGenerateScript}
            disabled={generatingScript}
          >
            {generatingScript ? "Generating..." : "📝 Generate Script"}
          </button>
          <button
            id="gen-ai-script-btn"
            className="btn btn-secondary btn-sm"
            onClick={handleGenerateAiScript}
            disabled={generatingAiScript}
          >
            {generatingAiScript ? "AI Working..." : "🤖 AI Script"}
          </button>
          <span className="workflow-divider" />
          <button
            id="execute-btn"
            className="btn btn-primary btn-sm"
            onClick={handleExecute}
            disabled={executing || !script}
            title={!script ? "Generate a script first" : "Run test"}
          >
            {executing ? "Running..." : "▶ Execute"}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        {(["overview", "tests", "script", "results", "report"] as const).map((tab) => (
          <button
            key={tab}
            className={`tab ${activeTab === tab ? "tab--active" : ""}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab === "overview" && "Overview"}
            {tab === "tests" && `Tests (${testcases.length})`}
            {tab === "script" && "Script"}
            {tab === "results" && `Results (${executions.length})`}
            {tab === "report" && "Report"}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {/* ──── Overview Tab ──── */}
        {activeTab === "overview" && (
          <div className="detail-grid animate-in animate-in-1">
            <div className="detail-section">
              <div className="detail-section-header">
                Page Info
              </div>
              <div className="detail-section-body">
                <div className="detail-item">
                  <span className="detail-item-label">URL</span>
                  <span className="detail-item-value truncate" style={{ maxWidth: 300 }}>{pageInfo?.url}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-item-label">Status Code</span>
                  <span className={`detail-item-value mono status-${pageInfo?.status_code}`}>
                    {pageInfo?.status_code}
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-item-label">Depth</span>
                  <span className="detail-item-value">{pageInfo?.depth}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-item-label">Crawl Date</span>
                  <span className="detail-item-value">{formatDate(pageInfo?.crawl_date || null)}</span>
                </div>
              </div>
            </div>

            <div className="detail-section">
              <div className="detail-section-header">
                Elements ({pageInfo?.elements.length || 0})
              </div>
              <div className="detail-section-body">
                {pageInfo?.elements.length === 0 ? (
                  <div className="text-muted" style={{ padding: "12px 0", textAlign: "center", fontSize: 13 }}>
                    No elements detected
                  </div>
                ) : (
                  pageInfo?.elements.slice(0, 10).map((el) => (
                    <div key={el.id} className="detail-item">
                      <span className="detail-item-label" style={{ display: "flex", gap: 8, alignItems: "center" }}>
                        <span className="badge badge--info" style={{ fontSize: 10 }}>{el.element_type}</span>
                        {el.name || el.text || "—"}
                      </span>
                      <span className="detail-item-value mono" style={{ fontSize: 11, color: "var(--text-muted)" }}>
                        {el.locator?.slice(0, 40)}
                      </span>
                    </div>
                  ))
                )}
                {(pageInfo?.elements.length || 0) > 10 && (
                  <div className="text-muted" style={{ padding: "8px 0", textAlign: "center", fontSize: 12 }}>
                    + {(pageInfo?.elements.length || 0) - 10} more elements
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ──── Tests Tab ──── */}
        {activeTab === "tests" && (
          <div className="animate-in animate-in-1">
            {testcases.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">🧪</div>
                <div className="empty-state-title">No Test Cases Yet</div>
                <div className="empty-state-desc">
                  Click &quot;Generate Tests&quot; or &quot;AI Tests&quot; to create test cases for this page.
                </div>
              </div>
            ) : (
              <div className="data-table-wrapper">
                <div className="data-table-header">
                  <div className="data-table-title">Test Cases</div>
                  <div style={{ display: "flex", gap: 8 }}>
                    <span className="badge badge--success">{testcases.filter((t) => t.source === "rule-based").length} Rule-Based</span>
                    <span className="badge badge--info">{testcases.filter((t) => t.source === "ai").length} AI</span>
                  </div>
                </div>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Test Case</th>
                      <th>Category</th>
                      <th>Priority</th>
                      <th>Expected Result</th>
                      <th>Source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {testcases.map((tc) => (
                      <tr key={tc.id}>
                        <td>
                          <span className="table-page-title">{tc.title}</span>
                        </td>
                        <td>
                          <span className="badge badge--neutral">{tc.category}</span>
                        </td>
                        <td>
                          <span className={`badge ${getPriorityClass(tc.priority)}`}>
                            {tc.priority}
                          </span>
                        </td>
                        <td>
                          <span className="text-secondary" style={{ fontSize: 13 }}>
                            {tc.expected_result}
                          </span>
                        </td>
                        <td>
                          <span className={`badge ${tc.source === "ai" ? "badge--info" : "badge--success"}`}>
                            {tc.source === "ai" ? "AI" : "Rules"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ──── Script Tab ──── */}
        {activeTab === "script" && (
          <div className="animate-in animate-in-1">
            {!script ? (
              <div className="empty-state">
                <div className="empty-state-icon">📝</div>
                <div className="empty-state-title">No Script Generated</div>
                <div className="empty-state-desc">
                  Click &quot;Generate Script&quot; or &quot;AI Script&quot; to create a Playwright automation script.
                </div>
              </div>
            ) : (
              <div className="detail-section">
                <div className="detail-section-header">
                  <span>
                    {script.script_name}
                    <span className="badge badge--info" style={{ marginLeft: 8, fontSize: 10 }}>
                      v{script.version}
                    </span>
                    <span className={`badge ${script.generation_type === "ai" ? "badge--warning" : "badge--success"}`} style={{ marginLeft: 4, fontSize: 10 }}>
                      {script.generation_type === "ai" ? "AI" : "Template"}
                    </span>
                  </span>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => {
                      navigator.clipboard.writeText(script.script);
                      showToast("✓ Script copied to clipboard");
                    }}
                  >
                    📋 Copy
                  </button>
                </div>
                <div className="code-viewer">
                  <pre className="code-block">{script.script}</pre>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ──── Results Tab ──── */}
        {activeTab === "results" && (
          <div className="animate-in animate-in-1">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
              <h2 className="data-table-title" style={{ fontSize: 18 }}>Executions</h2>
              {executions.length > 0 && (
                <button
                  className="btn btn-primary btn-sm"
                  onClick={handleExecute}
                  disabled={executing || !script}
                  title={!script ? "Generate a script first" : "Run test"}
                >
                  {executing ? "Running..." : "▶ Run Execution"}
                </button>
              )}
            </div>

            {executions.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">▶</div>
                <div className="empty-state-title">No Executions Yet</div>
                <div className="empty-state-desc" style={{ marginBottom: 16 }}>
                  Generate a script and click &quot;Execute&quot; to run your test.
                </div>
                {script && (
                  <button
                    className="btn btn-primary"
                    onClick={handleExecute}
                    disabled={executing}
                  >
                    {executing ? "Running..." : "▶ Run Test Execution"}
                  </button>
                )}
              </div>
            ) : (
              <>
                {/* Latest execution detail */}
                {executions[0] && (
                  <div className="detail-section" style={{ marginBottom: 20 }}>
                    <div className="detail-section-header">
                      <span>Latest Execution</span>
                      <span className={`badge ${executions[0].status === "PASS" ? "badge--success" : "badge--danger"}`}>
                        <span className={`badge-dot ${executions[0].status === "PASS" ? "badge-dot--success" : "badge-dot--danger"}`} />
                        {executions[0].status}
                      </span>
                    </div>
                    <div className="detail-section-body">
                      <div className="detail-item">
                        <span className="detail-item-label">Duration</span>
                        <span className="detail-item-value">{executions[0].duration ? `${executions[0].duration.toFixed(2)}s` : "—"}</span>
                      </div>
                      <div className="detail-item">
                        <span className="detail-item-label">Started</span>
                        <span className="detail-item-value">{formatDate(executions[0].started_at)}</span>
                      </div>
                      {executions[0].error_message && (
                        <div style={{ marginTop: 12 }}>
                          <div className="text-muted" style={{ fontSize: 11, marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.5px" }}>Error Output</div>
                          <div className="code-viewer">
                            <pre className="code-block code-block--error">{executions[0].error_message}</pre>
                          </div>
                        </div>
                      )}
                      {executions[0].execution_log && (
                        <div style={{ marginTop: 12 }}>
                          <div className="text-muted" style={{ fontSize: 11, marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.5px" }}>Execution Log</div>
                          <div className="code-viewer">
                            <pre className="code-block">{executions[0].execution_log}</pre>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Execution history table */}
                {executions.length > 1 && (
                  <div className="data-table-wrapper">
                    <div className="data-table-header">
                      <div className="data-table-title">Execution History</div>
                    </div>
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Run ID</th>
                          <th>Status</th>
                          <th>Duration</th>
                          <th>Time</th>
                          <th style={{ textAlign: "right" }}>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {executions.map((exec) => (
                          <tr key={exec.execution_id}>
                            <td><span className="mono">#{exec.execution_id}</span></td>
                            <td>
                              <span className={`badge ${exec.status === "PASS" ? "badge--success" : "badge--danger"}`}>
                                <span className={`badge-dot ${exec.status === "PASS" ? "badge-dot--success" : "badge-dot--danger"}`} />
                                {exec.status}
                              </span>
                            </td>
                            <td>
                              <span className="text-secondary">{exec.duration ? `${exec.duration.toFixed(2)}s` : "—"}</span>
                            </td>
                            <td>
                              <span className="text-muted" style={{ fontSize: 12 }}>{formatDate(exec.started_at)}</span>
                            </td>
                            <td style={{ textAlign: "right" }}>
                              <button
                                className="btn btn-secondary btn-sm"
                                style={{ padding: "4px 8px", fontSize: 11 }}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleExecute();
                                }}
                                disabled={executing || !script}
                              >
                                ⚡ Re-run
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* ──── Report Tab ──── */}
        {activeTab === "report" && (
          <div className="animate-in animate-in-1">
            {!reportData ? (
              <div className="empty-state">
                <div className="empty-state-icon">📊</div>
                <div className="empty-state-title">No Report Available</div>
                <div className="empty-state-desc">
                  Run an execution or wait for the system to finish crawling to load report data.
                </div>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
                {/* Executive Header */}
                <div className="workflow-bar" style={{ margin: 0 }}>
                  <div>
                    <h2 className="workflow-bar-title" style={{ fontSize: 16 }}>Executive QA Status Report</h2>
                    <p className="text-muted" style={{ fontSize: 12, marginTop: 4 }}>
                      Generated at: {formatDate(reportData.generated_at)}
                    </p>
                  </div>
                  <div style={{ display: "flex", gap: 8 }}>
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={handleDownloadReport}
                    >
                      📥 Download HTML Report
                    </button>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={async () => {
                        try {
                          const res = await api.get(`/execution/report/${pageId}`);
                          const blob = new Blob([JSON.stringify(res.data, null, 2)], {
                            type: "application/json",
                          });
                          const url = URL.createObjectURL(blob);
                          const a = document.createElement("a");
                          a.href = url;
                          a.download = `qa-report-page-${pageId}.json`;
                          document.body.appendChild(a);
                          a.click();
                          document.body.removeChild(a);
                          URL.revokeObjectURL(url);
                          showToast("✓ Raw JSON downloaded");
                        } catch (err) {
                          console.error(err);
                          showToast("Failed to download JSON", "error");
                        }
                      }}
                    >
                      ⚙️ JSON Export
                    </button>
                  </div>
                </div>

                {/* Dashboard Summary Cards */}
                <div className="stats-grid" style={{ marginBottom: 0 }}>
                  <div className="stat-card" style={{ display: "flex", alignItems: "center", gap: 20 }}>
                    {/* Radial/circular pass rate indicator */}
                    <div style={{ position: "relative", width: 70, height: 70, display: "flex", alignItems: "center", justifyContent: "center" }}>
                      <svg width="70" height="70" viewBox="0 0 36 36" style={{ transform: "rotate(-90deg)" }}>
                        <path
                          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                          fill="none"
                          stroke="rgba(255, 255, 255, 0.05)"
                          strokeWidth="3.5"
                        />
                        {reportData.summary.total_executions > 0 && (
                          <path
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none"
                            stroke={
                              parseFloat(reportData.summary.pass_rate) >= 80
                                ? "var(--success)"
                                : parseFloat(reportData.summary.pass_rate) >= 50
                                ? "var(--warning)"
                                : "var(--danger)"
                            }
                            strokeWidth="3.5"
                            strokeDasharray={`${parseFloat(reportData.summary.pass_rate)}, 100`}
                          />
                        )}
                      </svg>
                      <div style={{ position: "absolute", fontSize: 15, fontWeight: 700 }}>
                        {reportData.summary.total_executions > 0 ? reportData.summary.pass_rate : "N/A"}
                      </div>
                    </div>
                    <div>
                      <div className="stat-label">Pass Rate</div>
                      <div className="stat-value" style={{ fontSize: 20 }}>
                        {reportData.summary.total_executions > 0 ? `${reportData.summary.passed} / ${reportData.summary.total_executions} Pass` : "No runs"}
                      </div>
                    </div>
                  </div>

                  <div className="stat-card">
                    <div className="stat-label">Executions Breakdown</div>
                    <div style={{ display: "flex", gap: 16, marginTop: 8 }}>
                      <div>
                        <span className="badge badge--success" style={{ fontSize: 14, padding: "6px 12px" }}>
                          ✓ {reportData.summary.passed} Passed
                        </span>
                      </div>
                      <div>
                        <span className="badge badge--danger" style={{ fontSize: 14, padding: "6px 12px" }}>
                          ✕ {reportData.summary.failed} Failed
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="stat-card">
                    <div className="stat-label">Coverage Details</div>
                    <div className="stat-value" style={{ fontSize: 24, marginTop: 4 }}>
                      {reportData.summary.total_testcases} <span style={{ fontSize: 14, color: "var(--text-secondary)", fontWeight: 500 }}>Tests Generated</span>
                    </div>
                    <div className="text-muted" style={{ fontSize: 11, marginTop: 4 }}>
                      Analyzing {reportData.summary.total_elements} DOM elements
                    </div>
                  </div>
                </div>

                {/* Main page details & components list */}
                <div className="detail-grid" style={{ marginTop: 0 }}>
                  <div className="detail-section">
                    <div className="detail-section-header">Target Details</div>
                    <div className="detail-section-body">
                      <div className="detail-item">
                        <span className="detail-item-label">Title</span>
                        <span className="detail-item-value">{reportData.page.title || "Untitled"}</span>
                      </div>
                      <div className="detail-item">
                        <span className="detail-item-label">URL</span>
                        <span className="detail-item-value truncate" style={{ maxWidth: 220 }} title={reportData.page.url}>{reportData.page.url}</span>
                      </div>
                      <div className="detail-item">
                        <span className="detail-item-label">Status Code</span>
                        <span className={`detail-item-value mono status-${reportData.page.status_code}`}>{reportData.page.status_code || "—"}</span>
                      </div>
                      <div className="detail-item">
                        <span className="detail-item-label">Latest Script Version</span>
                        <span className="detail-item-value">{reportData.summary.total_scripts > 0 ? `v${reportData.scripts[0]?.version}` : "No scripts"}</span>
                      </div>
                    </div>
                  </div>

                  <div className="detail-section">
                    <div className="detail-section-header">Automation Script Stack</div>
                    <div className="detail-section-body">
                      {reportData.scripts.length === 0 ? (
                        <div className="text-muted" style={{ textAlign: "center", padding: "16px 0", fontSize: 13 }}>
                          No automation scripts compiled.
                        </div>
                      ) : (
                        reportData.scripts.slice(0, 3).map((scr: any) => (
                          <div key={scr.id} className="detail-item">
                            <span className="detail-item-label" style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                              {scr.script_name}
                            </span>
                            <span className="detail-item-value" style={{ display: "flex", gap: 6 }}>
                              <span className="badge badge--neutral" style={{ fontSize: 10 }}>v{scr.version}</span>
                              <span className="badge badge--info" style={{ fontSize: 10 }}>{scr.framework}</span>
                            </span>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>

                {/* Test Cases summary list */}
                <div className="data-table-wrapper">
                  <div className="data-table-header">
                    <div className="data-table-title">Report Test Cases ({reportData.testcases.length})</div>
                  </div>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Test Case Title</th>
                        <th>Category</th>
                        <th>Priority</th>
                        <th>Source</th>
                      </tr>
                    </thead>
                    <tbody>
                      {reportData.testcases.length === 0 ? (
                        <tr>
                          <td colSpan={4} style={{ textAlign: "center", color: "var(--text-muted)", padding: 24 }}>
                            No test cases generated for this report.
                          </td>
                        </tr>
                      ) : (
                        reportData.testcases.map((tc: any) => (
                          <tr key={tc.id} style={{ cursor: "default" }}>
                            <td>
                              <div className="table-page-title">{tc.title}</div>
                              <div className="text-muted" style={{ fontSize: 12, marginTop: 2 }}>{tc.expected_result}</div>
                            </td>
                            <td>
                              <span className="badge badge--neutral">{tc.category}</span>
                            </td>
                            <td>
                              <span className={`badge ${getPriorityClass(tc.priority)}`}>
                                {tc.priority}
                              </span>
                            </td>
                            <td>
                              <span className={`badge ${tc.source === "ai" ? "badge--info" : "badge--success"}`}>
                                {tc.source === "ai" ? "AI" : "Rules"}
                              </span>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
