import React from 'react';
import { Sparkles, CornerDownRight } from 'lucide-react';
import type { A2UIPayload, A2UIComponent } from '../../types/a2ui';
import { A2UIChart } from './A2UIChart';
import { A2UIMap } from './A2UIMap';
import { A2UIGallery } from './A2UIGallery';
import { A2UIMetrics } from './A2UIMetrics';
import { A2UITable } from './A2UITable';

interface Props {
  payload: A2UIPayload;
  onActionClick?: (promptText: string) => void;
}

export const A2UIRenderer: React.FC<Props> = ({ payload, onActionClick }) => {
  if (!payload || !payload.components || payload.components.length === 0) {
    return null;
  }

  const renderComponent = (comp: A2UIComponent) => {
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
    <div className="a2ui-container animate-fade-in">
      <div className="a2ui-badge-label">
        <Sparkles size={13} className="text-nypl-red animate-pulse-glow" />
        <span>Interactive A2UI Visualization</span>
      </div>

      <div className="a2ui-components-stack">
        {payload.components.map((comp) => (
          <div key={comp.id} className="a2ui-component-wrapper">
            {renderComponent(comp)}

            {/* Interactive Component Actions */}
            {comp.actions && comp.actions.length > 0 && (
              <div className="a2ui-actions-row">
                {comp.actions.map((act, idx) => (
                  <button
                    key={idx}
                    className="a2ui-action-chip"
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
                      } else if (onActionClick) {
                        onActionClick(act.payload);
                      }
                    }}
                  >
                    <CornerDownRight size={11} className="text-nypl-red" />
                    <span>{act.label}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
