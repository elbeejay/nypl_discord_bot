import React from 'react';
import { CornerDownRight, Sparkles, Compass } from 'lucide-react';
import type { ChatMessage, A2UIComponent } from '../../types/a2ui';
import { EditorialSummaryCard } from './EditorialSummaryCard';
import { A2UIChart } from '../a2ui/A2UIChart';
import { A2UIMap } from '../a2ui/A2UIMap';
import { A2UIGallery } from '../a2ui/A2UIGallery';
import { A2UIMetrics } from '../a2ui/A2UIMetrics';
import { A2UITable } from '../a2ui/A2UITable';

interface Props {
  userQuery?: string;
  responseMessage: ChatMessage;
  onActionClick: (promptText: string) => void;
}

export const CanvasGrid: React.FC<Props> = ({
  userQuery,
  responseMessage,
  onActionClick,
}) => {
  const a2uiPayload = responseMessage.a2ui;
  const components = a2uiPayload?.components || [];

  // Separate components by visual hierarchy
  const metricCards = components.filter((c) => c.type === 'metric_card');
  const galleries = components.filter((c) => c.type === 'photo_gallery');
  const maps = components.filter((c) => c.type === 'map');
  const charts = components.filter((c) => c.type === 'chart');
  const tables = components.filter((c) => c.type === 'data_table');

  // Extract all contextual action chips across components
  const allActions = components.flatMap((c) => c.actions || []);

  const renderComponentWidget = (comp: A2UIComponent) => {
    switch (comp.type) {
      case 'chart':
        return <A2UIChart key={comp.id} data={comp.data} />;
      case 'map':
        return <A2UIMap key={comp.id} data={comp.data} />;
      case 'photo_gallery':
        return <A2UIGallery key={comp.id} data={comp.data} />;
      case 'metric_card':
        return <A2UIMetrics key={comp.id} data={comp.data} />;
      case 'data_table':
        return <A2UITable key={comp.id} data={comp.data} />;
      default:
        return null;
    }
  };

  return (
    <div className="canvas-grid-layout animate-fade-in">
      {/* 1. Top Section: Key Metrics Row (if present) */}
      {metricCards.length > 0 && (
        <div className="canvas-section-metrics">
          {metricCards.map((m) => renderComponentWidget(m))}
        </div>
      )}

      {/* 2. Primary Showcase: 2-Column Split or Featured Layout */}
      <div className="canvas-primary-row">
        {/* Left Column: Editorial Summary Dossier */}
        <div className="canvas-col-editorial">
          <EditorialSummaryCard
            userQuery={userQuery}
            responseMessage={responseMessage}
          />
        </div>

        {/* Right Column: Visual Showcase (Map, Chart, or Photo Gallery) */}
        {(galleries.length > 0 || maps.length > 0 || charts.length > 0) && (
          <div className="canvas-col-visuals">
            {galleries.map((g) => (
              <div key={g.id} className="canvas-widget-item">
                {renderComponentWidget(g)}
              </div>
            ))}

            {maps.map((m) => (
              <div key={m.id} className="canvas-widget-item">
                {renderComponentWidget(m)}
              </div>
            ))}

            {charts.map((c) => (
              <div key={c.id} className="canvas-widget-item">
                {renderComponentWidget(c)}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 3. Full-Width Data Tables (if dataset records present) */}
      {tables.length > 0 && (
        <div className="canvas-section-tables">
          {tables.map((t) => (
            <div key={t.id} className="canvas-widget-item">
              {renderComponentWidget(t)}
            </div>
          ))}
        </div>
      )}

      {/* 4. Dynamic Contextual Action Chips & Follow-Up Bar */}
      <div className="canvas-followups-bar">
        <div className="canvas-followups-label">
          <Sparkles size={13} className="text-nypl-red" />
          <span>Exploratory Follow-ups:</span>
        </div>
        <div className="canvas-followups-chips">
          {allActions.length > 0 ? (
            allActions.map((act, idx) => (
              <button
                key={idx}
                className="canvas-action-chip"
                onClick={() => {
                  if (act.action_type === 'link') {
                    try {
                      const url = new URL(act.payload, window.location.origin);
                      if (url.protocol === 'http:' || url.protocol === 'https:') {
                        window.open(url.href, '_blank', 'noopener,noreferrer');
                      }
                    } catch {
                      // Ignore malformed or invalid URLs
                    }
                  } else {
                    onActionClick(act.payload);
                  }
                }}
              >
                <CornerDownRight size={11} className="text-nypl-red" />
                <span>{act.label}</span>
              </button>
            ))
          ) : (
            <>
              <button
                className="canvas-action-chip"
                onClick={() => onActionClick(`Tell me more historical details and related records about ${userQuery || 'this topic'}`)}
              >
                <Compass size={11} className="text-nypl-red" />
                <span>Dig Deeper into Archives</span>
              </button>
              <button
                className="canvas-action-chip"
                onClick={() => onActionClick('Show me related NYC 311 and civic statistics for this neighborhood')}
              >
                <CornerDownRight size={11} className="text-nypl-red" />
                <span>Compare Civic Data</span>
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
