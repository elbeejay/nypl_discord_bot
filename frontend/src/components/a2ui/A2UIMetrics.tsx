import React from 'react';
import { Activity, TrendingUp, TrendingDown, Minus, AlertTriangle, CheckCircle2, Info } from 'lucide-react';
import type { MetricCardData as A2UIMetricCardData, MetricItem } from '../../types/a2ui';

interface Props {
  data: A2UIMetricCardData;
}

export const A2UIMetrics: React.FC<Props> = ({ data }) => {
  const metrics = data.metrics || [];

  const getStatusClass = (status?: string) => {
    switch (status) {
      case 'positive': return 'status-positive';
      case 'negative':
      case 'critical':
      case 'error': return 'status-critical';
      case 'warning': return 'status-warning';
      case 'info': return 'status-info';
      default: return 'status-neutral';
    }
  };

  const getStatusIcon = (item: MetricItem) => {
    if (item.status === 'positive') return <CheckCircle2 size={13} />;
    if (item.status === 'warning') return <AlertTriangle size={13} />;
    if (item.status === 'critical' || item.status === 'error') return <AlertTriangle size={13} />;
    if (item.status === 'info') return <Info size={13} />;
    if (item.delta?.startsWith('+')) return <TrendingUp size={13} />;
    if (item.delta?.startsWith('-')) return <TrendingDown size={13} />;
    return <Minus size={13} />;
  };

  return (
    <div className="a2ui-card a2ui-metrics-container">
      <div className="a2ui-card-header">
        <div className="a2ui-badge-icon">
          <Activity size={16} className="text-nypl-red" />
        </div>
        <h4 className="a2ui-card-title">{data.title}</h4>
      </div>
      <div className="a2ui-metrics-grid">
        {metrics.map((item, idx) => (
          <div key={idx} className={`a2ui-metric-box ${getStatusClass(item.status)}`}>
            <div className="a2ui-metric-label">{item.label}</div>
            <div className="a2ui-metric-value">{item.value}</div>
            {item.delta && (
              <div className="a2ui-metric-delta">
                {getStatusIcon(item)}
                <span>{item.delta}</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
