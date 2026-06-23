"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import api from "@/services/api";
import { Project } from "@/types/project";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [createName, setCreateName] = useState("");
  const [createUrl, setCreateUrl] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchProjects();
  }, []);

  async function fetchProjects() {
    try {
      const response = await api.get("/projects");
      setProjects(response.data);
    } catch (err) {
      console.error("Failed to load projects", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate() {
    if (!createName.trim() || !createUrl.trim()) return;
    setCreating(true);
    try {
      await api.post("/projects", {
        name: createName.trim(),
        url: createUrl.trim(),
      });
      setCreateName("");
      setCreateUrl("");
      setShowCreate(false);
      await fetchProjects();
    } catch (err) {
      console.error("Failed to create project", err);
      alert("Failed to create project. Please try again.");
    } finally {
      setCreating(false);
    }
  }

  const filtered = projects.filter(
    (p) =>
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.url.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <div className="page-header">
        <div className="breadcrumb">
          <Link href="/">Dashboard</Link>
          <span className="breadcrumb-sep">/</span>
          <span>Projects</span>
        </div>
        <div className="page-header-row">
          <div>
            <h1 className="page-title">Projects</h1>
            <p className="page-subtitle">
              Manage your QA testing projects
            </p>
          </div>
          <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
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
                id="project-search"
                type="text"
                className="search-input"
                placeholder="Search projects..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <button
              id="create-project-btn"
              className="btn btn-primary"
              onClick={() => setShowCreate(true)}
            >
              + New Project
            </button>
          </div>
        </div>
      </div>

      {/* Create Project Modal */}
      {showCreate && (
        <div className="modal-overlay" onClick={() => setShowCreate(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Create New Project</h2>
              <button
                className="modal-close"
                onClick={() => setShowCreate(false)}
              >
                ✕
              </button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label" htmlFor="project-name">
                  Project Name
                </label>
                <input
                  id="project-name"
                  type="text"
                  className="form-input"
                  placeholder="e.g. My Application"
                  value={createName}
                  onChange={(e) => setCreateName(e.target.value)}
                  autoFocus
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="project-url">
                  Application URL
                </label>
                <input
                  id="project-url"
                  type="text"
                  className="form-input"
                  placeholder="e.g. https://example.com"
                  value={createUrl}
                  onChange={(e) => setCreateUrl(e.target.value)}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button
                className="btn btn-secondary"
                onClick={() => setShowCreate(false)}
              >
                Cancel
              </button>
              <button
                id="submit-create-project"
                className="btn btn-primary"
                onClick={handleCreate}
                disabled={creating || !createName.trim() || !createUrl.trim()}
              >
                {creating ? "Creating..." : "Create Project"}
              </button>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="projects-grid">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card" style={{ padding: 24 }}>
              <div
                className="skeleton"
                style={{ width: "60%", height: 20, marginBottom: 12 }}
              />
              <div
                className="skeleton"
                style={{ width: "80%", height: 14, marginBottom: 20 }}
              />
              <div style={{ display: "flex", gap: 12 }}>
                <div className="skeleton" style={{ width: 60, height: 14 }} />
                <div className="skeleton" style={{ width: 60, height: 14 }} />
              </div>
            </div>
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">
            {search ? "🔍" : "🚀"}
          </div>
          <div className="empty-state-title">
            {search ? "No Matching Projects" : "No Projects Yet"}
          </div>
          <div className="empty-state-desc">
            {search
              ? `No projects match "${search}". Try a different search.`
              : "Click '+ New Project' above to create your first project."}
          </div>
        </div>
      ) : (
        <div className="projects-grid">
          {filtered.map((project, index) => (
            <Link
              key={project.id}
              href={`/projects/${project.id}`}
              className={`project-card animate-in animate-in-${Math.min(index + 1, 5)}`}
            >
              <div className="project-card-name">{project.name}</div>
              <div className="project-card-url">{project.url}</div>
              <div className="project-card-stats">
                <div className="project-card-stat">
                  <span>ID:</span>
                  <span className="project-card-stat-value">
                    #{project.id}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}