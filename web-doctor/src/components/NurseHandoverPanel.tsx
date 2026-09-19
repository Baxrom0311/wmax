import React, { useCallback, useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  Zap,
  CheckCircle2,
  Stethoscope,
  Pill,
  Watch,
  Eye,
  RefreshCw,
} from "lucide-react";
import type { NurseHandoverSBAR, NurseChecklistItem } from "../lib/types";
import type { Lang } from "../i18n";

interface NurseHandoverPanelProps {
  handover: NurseHandoverSBAR;
  patientName: string;
  onRefresh?: () => void;
  lang: Lang;
}

const PRIORITY_CONFIG = {
  critical: { label: "SHOSHILINCH", color: "#dc2626", bg: "#fff1f2" },
  high: { label: "YUQORI", color: "#ea580c", bg: "#fff7ed" },
  medium: { label: "O'RTA", color: "#d97706", bg: "#fffbeb" },
  low: { label: "PAST", color: "#65a30d", bg: "#f7fee7" },
} as const;

const renderPriorityIcon = (priority: "critical" | "high" | "medium" | "low") => {
  switch (priority) {
    case "critical":
      return <AlertCircle size={12} style={{ marginRight: 4, verticalAlign: "middle" }} />;
    case "high":
      return <AlertTriangle size={12} style={{ marginRight: 4, verticalAlign: "middle" }} />;
    case "medium":
      return <Zap size={12} style={{ marginRight: 4, verticalAlign: "middle" }} />;
    case "low":
      return <CheckCircle2 size={12} style={{ marginRight: 4, verticalAlign: "middle" }} />;
  }
};

const renderCategoryIcon = (cat: NurseChecklistItem["category"]) => {
  switch (cat) {
    case "vitals":
      return <Stethoscope size={15} />;
    case "medication":
      return <Pill size={15} />;
    case "device":
      return <Watch size={15} />;
    case "observation":
      return <Eye size={15} />;
  }
};

const URGENCY_CONFIG = {
  critical: { label: "KRITIK SHOSHILINCH", color: "#dc2626", bg: "#fef2f2", border: "#fca5a5" },
  urgent: { label: "SHOSHILINCH", color: "#ea580c", bg: "#fff7ed", border: "#fdba74" },
  routine: { label: "ODATIY REJALI", color: "#16a34a", bg: "#f0fdf4", border: "#86efac" },
} as const;

export const NurseHandoverPanel: React.FC<NurseHandoverPanelProps> = ({
  handover,
  patientName,
  onRefresh,
  lang: _lang,
}) => {
  const [checklist, setChecklist] = useState<NurseChecklistItem[]>(handover.shift_checklist);
  const [activeSection, setActiveSection] = useState<"sbar" | "checklist">("sbar");
  const [refreshing, setRefreshing] = useState(false);

  const urgency = URGENCY_CONFIG[handover.clinical_urgency];
  const completedCount = checklist.filter((c) => c.completed).length;
  const totalCount = checklist.length;
  const progressPct = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  const toggleChecklistItem = useCallback((id: string) => {
    setChecklist((prev) =>
      prev.map((item) =>
        item.id === id ? { ...item, completed: !item.completed } : item
      )
    );
  }, []);

  const handleRefresh = useCallback(async () => {
    if (!onRefresh) return;
    setRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setRefreshing(false);
    }
  }, [onRefresh]);

  const sortedChecklist = [...checklist].sort((a, b) => {
    const order = { critical: 0, high: 1, medium: 2, low: 3 };
    return (order[a.priority] ?? 99) - (order[b.priority] ?? 99);
  });

  return (
    <div className="nurse-handover-panel">
      {/* Header */}
      <div className="nurse-handover-header" style={{ borderLeft: `4px solid ${urgency.color}`, background: urgency.bg }}>
        <div className="nurse-handover-header-top">
          <div className="nurse-handover-title-group">
            <span className="nurse-urgency-tag" style={{ color: urgency.color, background: urgency.border + "40" }}>
              {urgency.label}
            </span>
          </div>
          <div className="nurse-handover-actions">
            {onRefresh && (
              <button
                type="button"
                className="btn-nurse-refresh"
                onClick={handleRefresh}
                disabled={refreshing}
                style={{ display: "inline-flex", alignItems: "center", gap: 4 }}
              >
                <RefreshCw size={12} className={refreshing ? "spinner-rotate" : ""} />
                <span>{refreshing ? "Yangilanmoqda..." : "Yangilash"}</span>
              </button>
            )}
          </div>
        </div>
        <div className="nurse-handover-patient-line">
          <strong>{patientName}</strong>
          {handover.vital_flags && handover.vital_flags.length > 0 && (
            <div className="vital-flags-row">
              {handover.vital_flags.map((flag) => (
                <span key={flag} className="vital-flag-tag" style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                  <AlertTriangle size={11} />
                  <span>{flag}</span>
                </span>
              ))}
            </div>
          )}
        </div>
        <div className="nurse-progress-bar-container">
          <div className="nurse-progress-label">
            Vazifalar: <strong>{completedCount}/{totalCount}</strong>
          </div>
          <div className="nurse-progress-track">
            <div
              className={`nurse-progress-fill ${progressPct === 100 ? "completed" : ""}`}
              style={{ width: `${progressPct}%` }}
            />
          </div>
          <span className="nurse-progress-pct">{progressPct}%</span>
        </div>
      </div>

      {/* Tab Switcher */}
      <div className="nurse-tab-row">
        <button
          type="button"
          className={`nurse-tab-btn ${activeSection === "sbar" ? "active" : ""}`}
          onClick={() => setActiveSection("sbar")}
        >
          SBAR
        </button>
        <button
          type="button"
          className={`nurse-tab-btn ${activeSection === "checklist" ? "active" : ""}`}
          onClick={() => setActiveSection("checklist")}
        >
          Vazifalar ({completedCount}/{totalCount})
        </button>
      </div>

      {/* SBAR Content */}
      {activeSection === "sbar" && (
        <div className="nurse-sbar-content">
          <div className="sbar-block sbar-situation">
            <div className="sbar-label">
              <span className="sbar-letter">S</span>
              <span>Vaziyat</span>
            </div>
            <p className="sbar-text">{handover.situation}</p>
          </div>

          <div className="sbar-block sbar-background">
            <div className="sbar-label">
              <span className="sbar-letter">B</span>
              <span>Anamnez</span>
            </div>
            <p className="sbar-text">{handover.background}</p>
          </div>

          <div className="sbar-block sbar-assessment">
            <div className="sbar-label">
              <span className="sbar-letter">A</span>
              <span>Baholash</span>
            </div>
            <p className="sbar-text">{handover.assessment}</p>
          </div>

          <div className="sbar-block sbar-recommendation">
            <div className="sbar-label">
              <span className="sbar-letter">R</span>
              <span>Tavsiya</span>
            </div>
            <p className="sbar-text">{handover.recommendation}</p>
          </div>

          <div className="nurse-evidence-footer">
            <div className="evidence-citations">
              {handover.evidence_citations.map((c) => (
                <span key={c} className="evidence-tag">{c}</span>
              ))}
            </div>
            <div className="confidence-indicator">
              <span
                className="confidence-badge"
                style={{
                  color: handover.confidence_score >= 0.9 ? "#16a34a" : handover.confidence_score >= 0.7 ? "#d97706" : "#dc2626",
                }}
              >
                {Math.round(handover.confidence_score * 100)}%
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Checklist Content */}
      {activeSection === "checklist" && (
        <div className="nurse-checklist-content">
          {sortedChecklist.map((item) => {
            const priority = PRIORITY_CONFIG[item.priority];
            return (
              <label
                key={item.id}
                className={`nurse-checklist-item ${item.completed ? "completed" : ""}`}
                style={{
                  borderLeft: `3px solid ${item.completed ? "#16a34a" : priority.color}`,
                  background: item.completed ? "#f0fdf4" : priority.bg,
                }}
              >
                <input
                  type="checkbox"
                  checked={item.completed}
                  onChange={() => toggleChecklistItem(item.id)}
                  className="nurse-checkbox"
                />
                <span className="checklist-category-icon" style={{ display: "inline-flex", alignItems: "center" }}>
                  {renderCategoryIcon(item.category)}
                </span>
                <span className={`checklist-task-text ${item.completed ? "line-through" : ""}`}>
                  {item.task}
                </span>
                <span
                  className="checklist-priority-badge"
                  style={{ color: priority.color, background: priority.bg, display: "inline-flex", alignItems: "center", gap: 4 }}
                >
                  {renderPriorityIcon(item.priority)}
                  <span>{priority.label}</span>
                </span>
              </label>
            );
          })}

          {completedCount === totalCount && totalCount > 0 && (
            <div className="nurse-checklist-complete" style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}>
              <CheckCircle2 size={16} color="#16a34a" />
              <span>Barcha vazifalar bajarildi</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NurseHandoverPanel;
