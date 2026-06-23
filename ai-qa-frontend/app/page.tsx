"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import api from "@/services/api";
import { Project } from "@/types/project";

export default function Home() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboard();
  }, []);

  async function fetchDashboard() {
    try {
      const response = await api.get("/projects");
      setProjects(response.data);
    } catch (err) {
      console.error("Failed to load projects", err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">
          Overview of your AI-powered QA testing platform
        </p>
      </div>

      {/* Stats */}
      <div className="stats-grid">
        <div className="stat-card stat-card--purple animate-in animate-in-1">
          <div className="stat-label">Total Projects</div>
          <div className="stat-value">
            {loading ? "—" : projects.length}
          </div>
          <div className="stat-icon stat-icon--purple">📁</div>
        </div>

        <div className="stat-card stat-card--blue animate-in animate-in-2">
          <div className="stat-label">Active</div>
          <div className="stat-value">
            {loading ? "—" : projects.length}
          </div>
          <div className="stat-icon stat-icon--blue">🔵</div>
        </div>

        <div className="stat-card stat-card--green animate-in animate-in-3">
          <div className="stat-label">Status</div>
          <div className="stat-value" style={{ fontSize: 22 }}>
            {loading ? "—" : "Healthy"}
          </div>
          <div className="stat-icon stat-icon--green">✓</div>
        </div>

        <div className="stat-card stat-card--orange animate-in animate-in-4">
          <div className="stat-label">Platform</div>
          <div className="stat-value" style={{ fontSize: 22 }}>
            {loading ? "—" : "Online"}
          </div>
          <div className="stat-icon stat-icon--orange">⚡</div>
        </div>
      </div>

      {/* Quick Access Projects */}
      <div className="data-table-wrapper animate-in animate-in-5">
        <div className="data-table-header">
          <div className="data-table-title">Recent Projects</div>
          <Link href="/projects" className="btn btn-secondary btn-sm">
            View All →
          </Link>
        </div>

        {loading ? (
          <div>
            {[1, 2, 3].map((i) => (
              <div key={i} className="skeleton-row">
                <div
                  className="skeleton skeleton-cell"
                  style={{ width: "30%", height: 16 }}
                />
                <div
                  className="skeleton skeleton-cell"
                  style={{ width: "50%", height: 14 }}
                />
                <div
                  className="skeleton skeleton-cell"
                  style={{ width: "15%", height: 14 }}
                />
              </div>
            ))}
          </div>
        ) : projects.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">🚀</div>
            <div className="empty-state-title">No Projects Yet</div>
            <div className="empty-state-desc">
              Create your first project to start crawling and generating AI test
              cases.
            </div>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Project</th>
                <th>URL</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((project) => (
                <tr key={project.id}>
                  <td>
                    <div className="table-page-title">{project.name}</div>
                  </td>
                  <td>
                    <div className="table-page-url">{project.url}</div>
                  </td>
                  <td>
                    <Link
                      href={`/projects/${project.id}`}
                      className="btn btn-secondary btn-sm"
                    >
                      Open →
                    </Link>
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
