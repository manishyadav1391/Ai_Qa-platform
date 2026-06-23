"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import api from "@/services/api";

interface PageData {
  id: number;
  title: string;
  url: string;
  status_code: number | null;
  depth: number | null;
  crawl_date: string | null;
  element_count: number;
  testcase_count: number;
  script_count: number;
  execution_count: number;
  last_execution_status: string | null;
  last_execution_date: string | null;
}

interface ProjectInfo {
  id: number;
  name: string;
  url: string;
}

interface CrawlStatus {
  crawl_run_id: number;
  status: string;
  pages_found: number;
  current_url: string | null;
  max_pages: number | null;
  started_at: string | null;
  completed_at: string | null;
  is_active: boolean;
}

export default function ProjectPagesPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id;

  const [project, setProject] = useState<ProjectInfo | null>(null);
  const [pages, setPages] = useState<PageData[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [singleCrawlUrl, setSingleCrawlUrl] = useState("");

  // Crawl state
  const [crawling, setCrawling] = useState(false);
  const [crawlRunId, setCrawlRunId] = useState<number | null>(null);
  const [crawlStatus, setCrawlStatus] = useState<CrawlStatus | null>(null);
  const [crawlMessage, setCrawlMessage] = useState("");
  const [stopping, setStopping] = useState(false);

  // Auth state
  const [authStatus, setAuthStatus] = useState<string>("none");
  const [authCookieCount, setAuthCookieCount] = useState(0);
  const [authCapturedAt, setAuthCapturedAt] = useState<string | null>(null);
  const [authBrowserOpen, setAuthBrowserOpen] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [authLoginUrl, setAuthLoginUrl] = useState("");

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const autoDismissRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    loadData();
    loadAuthStatus();
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
      if (autoDismissRef.current) clearTimeout(autoDismissRef.current);
    };
  }, []);

  async function loadData() {
    try {
      const [projectRes, pagesRes] = await Promise.all([
        api.get(`/projects/${projectId}`),
        api.get(`/pages/${projectId}`),
      ]);
      setProject(projectRes.data);
      setPages(pagesRes.data);
    } catch (err) {
      console.error("Failed to load project data", err);
    } finally {
      setLoading(false);
    }
  }

  // ── Auth session management ──────────────────────────────────
  async function loadAuthStatus() {
    try {
      const res = await api.get(`/auth/${projectId}/status`);
      setAuthStatus(res.data.auth_status || "none");
      setAuthCookieCount(res.data.cookie_count || 0);
      setAuthCapturedAt(res.data.captured_at || null);
      setAuthBrowserOpen(res.data.browser_open || false);
      setAuthLoginUrl(res.data.login_url || "");
    } catch (err) {
      console.error("Failed to load auth status", err);
    }
  }

  async function handleStartLoginBrowser() {
    setAuthLoading(true);
    try {
      const loginUrl = authLoginUrl || project?.url || "";
      await api.post(`/auth/${projectId}/start-session?login_url=${encodeURIComponent(loginUrl)}`);
      setAuthBrowserOpen(true);
    } catch (err) {
      console.error("Failed to start login browser", err);
    } finally {
      setAuthLoading(false);
    }
  }

  async function handleCaptureSession() {
    setAuthLoading(true);
    try {
      const res = await api.post(`/auth/${projectId}/capture-session`);
      if (res.data.error) {
        alert(res.data.error);
      } else {
        setAuthStatus("active");
        setAuthCookieCount(res.data.cookies_captured || 0);
        setAuthCapturedAt(res.data.captured_at || null);
        setAuthBrowserOpen(false);
      }
    } catch (err) {
      console.error("Failed to capture session", err);
    } finally {
      setAuthLoading(false);
    }
  }

  async function handleClearAuth() {
    try {
      await api.delete(`/auth/${projectId}/clear`);
      setAuthStatus("none");
      setAuthCookieCount(0);
      setAuthCapturedAt(null);
      setAuthBrowserOpen(false);
      setAuthLoginUrl("");
    } catch (err) {
      console.error("Failed to clear auth", err);
    }
  }

  // ── Single page crawl (synchronous) ──────────────────────────
  async function handleSingleCrawl() {
    setCrawling(true);
    setCrawlMessage("");
    setCrawlStatus(null);
    try {
      const urlParam = singleCrawlUrl ? `?url=${encodeURIComponent(singleCrawlUrl)}` : "";
      const res = await api.post(`/crawl/${projectId}${urlParam}`);
      setCrawlMessage(`Crawl complete — Page "${res.data.title}" saved`);
      const pagesRes = await api.get(`/pages/${projectId}`);
      setPages(pagesRes.data);
      setSingleCrawlUrl("");
    } catch (err) {
      console.error("Crawl failed", err);
      setCrawlMessage("error:Crawl failed. Check the server logs.");
    } finally {
      setCrawling(false);
    }
  }

  // ── Recursive crawl (background, with polling) ───────────────
  async function handleRecursiveCrawl() {
    setCrawling(true);
    setCrawlMessage("");
    setCrawlStatus(null);
    setStopping(false);

    try {
      const res = await api.post(`/crawl/test-recursive/${projectId}`);
      const data = res.data;

      if (data.error) {
        setCrawlMessage(`error:${data.error}`);
        setCrawling(false);
        return;
      }

      const runId = data.crawl_run_id;
      setCrawlRunId(runId);
      setCrawlStatus({
        crawl_run_id: runId,
        status: "running",
        pages_found: 0,
        current_url: project?.url || null,
        max_pages: data.max_pages || 50,
        started_at: new Date().toISOString(),
        completed_at: null,
        is_active: true,
      });

      // Start polling
      startPolling(runId);
    } catch (err) {
      console.error("Crawl failed", err);
      setCrawlMessage("error:Failed to start crawl. Check the server logs.");
      setCrawling(false);
    }
  }

  const startPolling = useCallback((runId: number) => {
    if (pollRef.current) clearInterval(pollRef.current);

    pollRef.current = setInterval(async () => {
      try {
        const res = await api.get(`/crawl/status/${runId}`);
        const status: CrawlStatus = res.data;
        setCrawlStatus(status);

        // Check if crawl is done
        if (["completed", "stopped", "failed"].includes(status.status)) {
          // Stop polling
          if (pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
          }

          setCrawling(false);
          setStopping(false);

          // Reload pages
          const pagesRes = await api.get(`/pages/${projectId}`);
          setPages(pagesRes.data);

          // Auto-dismiss progress panel after 8 seconds
          autoDismissRef.current = setTimeout(() => {
            setCrawlStatus(null);
            setCrawlRunId(null);
          }, 8000);
        }
      } catch (err) {
        console.error("Poll error", err);
      }
    }, 2000);
  }, [projectId]);

  // ── Stop crawl ───────────────────────────────────────────────
  async function handleStopCrawl() {
    if (!crawlRunId) return;
    setStopping(true);

    try {
      await api.post(`/crawl/stop/${crawlRunId}`);
    } catch (err) {
      console.error("Failed to stop crawl", err);
      setStopping(false);
    }
  }

  // ── Helpers ──────────────────────────────────────────────────
  const filtered = pages.filter(
    (p) =>
      (p.title || "").toLowerCase().includes(search.toLowerCase()) ||
      (p.url || "").toLowerCase().includes(search.toLowerCase())
  );

  const totalElements = pages.reduce((a, p) => a + p.element_count, 0);
  const totalTestcases = pages.reduce((a, p) => a + p.testcase_count, 0);
  const totalScripts = pages.reduce((a, p) => a + p.script_count, 0);
  const totalExecutions = pages.reduce((a, p) => a + p.execution_count, 0);

  function getStatusBadge(status: string | null) {
    if (!status) return <span className="badge badge--neutral">No runs</span>;
    if (status === "PASS")
      return (
        <span className="badge badge--success">
          <span className="badge-dot badge-dot--success" />
          Pass
        </span>
      );
    if (status === "FAIL")
      return (
        <span className="badge badge--danger">
          <span className="badge-dot badge-dot--danger" />
          Fail
        </span>
      );
    return (
      <span className="badge badge--warning">
        <span className="badge-dot badge-dot--warning" />
        {status}
      </span>
    );
  }

  function getStatusCodeClass(code: number | null) {
    if (!code) return "";
    if (code >= 200 && code < 300) return "status-200";
    if (code >= 300 && code < 400) return "status-301";
    return "status-404";
  }

  function formatDate(dateStr: string | null) {
    if (!dateStr) return "—";
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }

  function getElapsedTime(): string {
    if (!crawlStatus?.started_at) return "";
    const start = new Date(crawlStatus.started_at).getTime();
    const now = Date.now();
    const seconds = Math.floor((now - start) / 1000);
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  }

  function getCrawlStatusLabel(): string {
    if (!crawlStatus) return "";
    switch (crawlStatus.status) {
      case "running": return stopping ? "Stopping..." : "Crawling";
      case "completed": return "Completed";
      case "stopped": return "Stopped";
      case "failed": return "Failed";
      default: return crawlStatus.status;
    }
  }

  function getCrawlStatusClass(): string {
    if (!crawlStatus) return "";
    switch (crawlStatus.status) {
      case "running": return stopping ? "crawl-status--warning" : "crawl-status--running";
      case "completed": return "crawl-status--success";
      case "stopped": return "crawl-status--warning";
      case "failed": return "crawl-status--danger";
      default: return "";
    }
  }

  const progressPercent = crawlStatus
    ? Math.min(
        ((crawlStatus.pages_found || 0) / (crawlStatus.max_pages || 50)) * 100,
        100
      )
    : 0;

  return (
    <div>
      {/* Header */}
      <div className="page-header">
        <div className="breadcrumb">
          <Link href="/">Dashboard</Link>
          <span className="breadcrumb-sep">/</span>
          <Link href="/projects">Projects</Link>
          <span className="breadcrumb-sep">/</span>
          <span>
            {loading
              ? "Loading..."
              : project?.name || `Project #${projectId}`}
          </span>
        </div>

        <div className="page-header-row">
          <div>
            <h1 className="page-title">
              {loading ? "Loading..." : project?.name || "Project Pages"}
            </h1>
            <p className="page-subtitle">
              {loading
                ? "Fetching pages..."
                : `${pages.length} page${pages.length !== 1 ? "s" : ""} discovered · ${project?.url || ""}`}
            </p>
          </div>
          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            <div className="search-wrapper">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="search-icon"
              >
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <input
                id="page-search"
                type="text"
                className="search-input"
                placeholder="Search pages..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <input
              id="single-crawl-url"
              type="text"
              className="search-input"
              style={{ maxWidth: "200px", paddingLeft: "16px" }}
              placeholder="Target path (optional, e.g. /profile)"
              value={singleCrawlUrl}
              onChange={(e) => setSingleCrawlUrl(e.target.value)}
              disabled={crawling}
            />
            <button
              id="crawl-single-btn"
              className="btn btn-secondary"
              onClick={handleSingleCrawl}
              disabled={crawling}
            >
              {crawling && !crawlRunId ? "Crawling..." : "Crawl Page"}
            </button>
            <button
              id="crawl-recursive-btn"
              className="btn btn-primary"
              onClick={handleRecursiveCrawl}
              disabled={crawling}
            >
              {crawling && crawlRunId ? (
                <span className="spinner" />
              ) : (
                <>🕷️ Crawl Site</>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* ── Auth Session Panel ──────────────────────────────────── */}
      <div className={`auth-panel animate-in animate-in-1 ${authStatus === "active" ? "auth-panel--active" : ""}`}>
        <div className="auth-panel-header">
          <div className="auth-panel-left">
            <div className={`auth-status-dot ${authStatus === "active" ? "auth-status-dot--active" : ""}`} />
            <span className="auth-panel-title">🔐 Authentication</span>
            {authStatus === "active" && (
              <span className="badge badge--success" style={{ marginLeft: 8 }}>
                Session Active · {authCookieCount} cookies
              </span>
            )}
            {authStatus === "none" && (
              <span className="badge badge--neutral" style={{ marginLeft: 8 }}>
                No Session
              </span>
            )}
          </div>
          <div className="auth-panel-actions">
            {authStatus === "active" && (
              <button
                id="clear-auth-btn"
                className="btn btn-danger btn-sm"
                onClick={handleClearAuth}
              >
                ✕ Clear Session
              </button>
            )}
          </div>
        </div>

        {authStatus !== "active" && (
          <div className="auth-panel-body">
            <div className="auth-step-row">
              <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
                <label className="form-label" htmlFor="auth-login-url">Login URL (optional)</label>
                <input
                  id="auth-login-url"
                  type="text"
                  className="form-input"
                  placeholder={project?.url || "https://example.com/login"}
                  value={authLoginUrl}
                  onChange={(e) => setAuthLoginUrl(e.target.value)}
                />
              </div>
            </div>

            <div className="auth-step-row" style={{ marginTop: 12 }}>
              {!authBrowserOpen ? (
                <button
                  id="start-login-btn"
                  className="btn btn-primary"
                  onClick={handleStartLoginBrowser}
                  disabled={authLoading}
                >
                  {authLoading ? (
                    <><span className="spinner spinner--sm" /> Opening Browser...</>
                  ) : (
                    <>🌐 Open Login Browser</>
                  )}
                </button>
              ) : (
                <>
                  <div className="auth-waiting-message">
                    <span className="spinner spinner--sm" />
                    <span>Browser is open — log in manually, then click <strong>Capture Session</strong></span>
                  </div>
                  <button
                    id="capture-session-btn"
                    className="btn btn-success"
                    onClick={handleCaptureSession}
                    disabled={authLoading}
                  >
                    {authLoading ? (
                      <><span className="spinner spinner--sm" /> Capturing...</>
                    ) : (
                      <>✓ Capture Session</>
                    )}
                  </button>
                </>
              )}
            </div>

            <p className="auth-help-text">
              A browser window will open. Log in manually (handle CAPTCHA, MFA, etc.), then click "Capture Session" to save cookies for authenticated crawling.
            </p>
          </div>
        )}

        {authStatus === "active" && authCapturedAt && (
          <div className="auth-panel-footer">
            Captured {formatDate(authCapturedAt)}
            {authLoginUrl && <> · from <span className="mono" style={{ fontSize: 12 }}>{authLoginUrl}</span>  </>}
          </div>
        )}
      </div>

      {/* ── Crawl Progress Panel ──────────────────────────────── */}
      {crawlStatus && (
        <div className={`crawl-progress animate-in animate-in-1 ${getCrawlStatusClass()}`}>
          <div className="crawl-progress-header">
            <div className="crawl-progress-left">
              <div className={`crawl-status-dot ${crawlStatus.status === "running" ? "crawl-status-dot--pulse" : ""}`} />
              <span className="crawl-progress-label">{getCrawlStatusLabel()}</span>
              <span className="crawl-progress-time">{getElapsedTime()}</span>
            </div>
            <div className="crawl-progress-right">
              <span className="crawl-progress-count">
                <strong>{crawlStatus.pages_found || 0}</strong>
                <span className="text-muted"> / {crawlStatus.max_pages || 50} pages</span>
              </span>
              {crawlStatus.status === "running" && (
                <button
                  id="stop-crawl-btn"
                  className="btn btn-danger btn-sm"
                  onClick={handleStopCrawl}
                  disabled={stopping}
                >
                  {stopping ? (
                    <>
                      <span className="spinner spinner--sm" />
                      Stopping...
                    </>
                  ) : (
                    <>■ Stop Crawl</>
                  )}
                </button>
              )}
              {crawlStatus.status !== "running" && (
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => {
                    setCrawlStatus(null);
                    setCrawlRunId(null);
                    if (autoDismissRef.current) clearTimeout(autoDismissRef.current);
                  }}
                >
                  Dismiss
                </button>
              )}
            </div>
          </div>

          {/* Progress bar */}
          <div className="crawl-progress-bar-track">
            <div
              className={`crawl-progress-bar-fill ${crawlStatus.status === "running" ? "crawl-progress-bar-fill--active" : ""}`}
              style={{ width: `${progressPercent}%` }}
            />
          </div>

          {/* Current URL */}
          {crawlStatus.current_url && crawlStatus.status === "running" && (
            <div className="crawl-progress-url">
              <span className="text-muted">Scanning: </span>
              <span className="crawl-progress-url-value">{crawlStatus.current_url}</span>
            </div>
          )}

          {/* Completion message */}
          {crawlStatus.status === "completed" && (
            <div className="crawl-progress-message crawl-progress-message--success">
              Crawl complete — {crawlStatus.pages_found} page{crawlStatus.pages_found !== 1 ? "s" : ""} saved successfully
            </div>
          )}
          {crawlStatus.status === "stopped" && (
            <div className="crawl-progress-message crawl-progress-message--warning">
              Crawl stopped — {crawlStatus.pages_found} page{crawlStatus.pages_found !== 1 ? "s" : ""} saved before stop
            </div>
          )}
          {crawlStatus.status === "failed" && (
            <div className="crawl-progress-message crawl-progress-message--danger">
              Crawl failed — check server logs for details
            </div>
          )}
        </div>
      )}

      {/* Simple crawl message (for single page crawl) */}
      {crawlMessage && !crawlStatus && (
        <div
          className={`toast animate-in animate-in-1 ${crawlMessage.startsWith("error:") ? "toast--error" : "toast--success"}`}
        >
          {crawlMessage.replace("error:", "")}
          <button
            className="toast-close"
            onClick={() => setCrawlMessage("")}
          >
            ✕
          </button>
        </div>
      )}

      {/* Stats */}
      <div className="stats-grid">
        <div className="stat-card stat-card--purple animate-in animate-in-1">
          <div className="stat-label">Pages</div>
          <div className="stat-value">{loading ? "—" : pages.length}</div>
          <div className="stat-icon stat-icon--purple">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="20" height="20">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
          </div>
        </div>

        <div className="stat-card stat-card--blue animate-in animate-in-2">
          <div className="stat-label">Elements</div>
          <div className="stat-value">{loading ? "—" : totalElements}</div>
          <div className="stat-icon stat-icon--blue">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="20" height="20">
              <polyline points="16 18 22 12 16 6" />
              <polyline points="8 6 2 12 8 18" />
            </svg>
          </div>
        </div>

        <div className="stat-card stat-card--green animate-in animate-in-3">
          <div className="stat-label">Test Cases</div>
          <div className="stat-value">{loading ? "—" : totalTestcases}</div>
          <div className="stat-icon stat-icon--green">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="20" height="20">
              <path d="M9 11l3 3L22 4" />
              <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
            </svg>
          </div>
        </div>

        <div className="stat-card stat-card--orange animate-in animate-in-4">
          <div className="stat-label">Executions</div>
          <div className="stat-value">{loading ? "—" : totalExecutions}</div>
          <div className="stat-icon stat-icon--orange">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="20" height="20">
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
          </div>
        </div>
      </div>

      {/* Pages Table */}
      <div className="data-table-wrapper animate-in animate-in-5">
        <div className="data-table-header">
          <div className="data-table-title">
            Crawled Pages
            {!loading && filtered.length !== pages.length && (
              <span className="text-muted" style={{ fontWeight: 400, fontSize: 13, marginLeft: 8 }}>
                ({filtered.length} of {pages.length})
              </span>
            )}
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <span className="badge badge--info" style={{ cursor: "default" }}>
              {totalScripts} Scripts
            </span>
          </div>
        </div>

        {loading ? (
          <div>
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="skeleton-row">
                <div className="skeleton skeleton-cell" style={{ width: "25%", height: 16 }} />
                <div className="skeleton skeleton-cell" style={{ width: "35%", height: 14 }} />
                <div className="skeleton skeleton-cell" style={{ width: "8%", height: 14 }} />
                <div className="skeleton skeleton-cell" style={{ width: "10%", height: 14 }} />
                <div className="skeleton skeleton-cell" style={{ width: "12%", height: 24 }} />
              </div>
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">{search ? "🔍" : "🕷️"}</div>
            <div className="empty-state-title">
              {search ? "No Matching Pages" : "No Pages Crawled"}
            </div>
            <div className="empty-state-desc">
              {search
                ? `No pages match "${search}".`
                : "Click 'Crawl Site' above to discover and analyze pages for this project."}
            </div>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Page</th>
                <th>Status</th>
                <th>Depth</th>
                <th>Elements</th>
                <th>Tests</th>
                <th>Last Run</th>
                <th>Crawled</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((page) => (
                <tr
                  key={page.id}
                  onClick={() => router.push(`/page/${page.id}`)}
                  style={{ cursor: "pointer" }}
                >
                  <td>
                    <div className="table-page-title">
                      {page.title || "Untitled"}
                    </div>
                    <div className="table-page-url">{page.url}</div>
                  </td>
                  <td>
                    <span
                      className={`mono ${getStatusCodeClass(page.status_code)}`}
                      style={{ fontWeight: 600 }}
                    >
                      {page.status_code || "—"}
                    </span>
                  </td>
                  <td>
                    <span className="badge badge--neutral">
                      {page.depth ?? "—"}
                    </span>
                  </td>
                  <td>
                    <span className="text-secondary">
                      {page.element_count}
                    </span>
                  </td>
                  <td>
                    <span className="text-secondary">
                      {page.testcase_count}
                    </span>
                  </td>
                  <td>{getStatusBadge(page.last_execution_status)}</td>
                  <td>
                    <span className="text-muted" style={{ fontSize: 12 }}>
                      {formatDate(page.crawl_date)}
                    </span>
                  </td>
                  <td>
                    <span className="btn btn-secondary btn-sm">Open →</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}