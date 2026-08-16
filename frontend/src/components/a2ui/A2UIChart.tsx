import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  type ChartOptions,
} from 'chart.js';
import { Bar, Line, Pie, Doughnut } from 'react-chartjs-2';
import { BarChart3, PieChart as PieIcon, LineChart as LineIcon } from 'lucide-react';
import type { ChartData as A2UIChartData } from '../../types/a2ui';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

interface Props {
  data: A2UIChartData;
}

const NYPL_PALETTE = [
  '#D41B2C', // NYPL Red
  '#2563EB', // Blue
  '#B8860B', // Archival Gold
  '#10B981', // Forest Green
  '#8B5CF6', // Purple
  '#F59E0B', // Amber
  '#06B6D4', // Cyan
  '#EC4899', // Pink
];

export const A2UIChart: React.FC<Props> = ({ data }) => {
  const chartType = data.chart_type || 'bar';

  // Format datasets with NYPL colors if not explicitly set
  const formattedDatasets = (data.datasets || []).map((ds, idx) => {
    const isPieOrDoughnut = chartType === 'pie' || chartType === 'doughnut';
    return {
      label: ds.label || 'Data',
      data: ds.data,
      backgroundColor: ds.background_color || (isPieOrDoughnut ? NYPL_PALETTE.slice(0, data.labels.length) : NYPL_PALETTE[idx % NYPL_PALETTE.length]),
      borderColor: ds.border_color || (isPieOrDoughnut ? '#FFFFFF' : NYPL_PALETTE[idx % NYPL_PALETTE.length]),
      borderWidth: 1.5,
      borderRadius: chartType === 'bar' ? 6 : 0,
    };
  });

  const chartData = {
    labels: data.labels,
    datasets: formattedDatasets,
  };

  const legendPosition = (chartType === 'pie' || chartType === 'doughnut') ? 'right' : 'top';

  const options: ChartOptions<any> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: legendPosition,
        labels: {
          font: { family: 'Plus Jakarta Sans', size: 12, weight: 500 },
          boxWidth: 12,
          boxHeight: 12,
          usePointStyle: true,
        },
      },
      tooltip: {
        backgroundColor: '#18181B',
        titleFont: { family: 'Plus Jakarta Sans', size: 13, weight: 600 },
        bodyFont: { family: 'Plus Jakarta Sans', size: 12 },
        padding: 10,
        cornerRadius: 8,
      },
    },
    scales: (chartType === 'pie' || chartType === 'doughnut') ? undefined : {
      y: {
        beginAtZero: true,
        grid: { color: 'rgba(200, 200, 200, 0.2)' },
        ticks: { font: { family: 'Plus Jakarta Sans', size: 11 } }
      },
      x: {
        grid: { display: false },
        ticks: { font: { family: 'Plus Jakarta Sans', size: 11 } }
      }
    }
  };

  const getIcon = () => {
    if (chartType === 'pie' || chartType === 'doughnut') return <PieIcon size={16} className="text-nypl-red" />;
    if (chartType === 'line') return <LineIcon size={16} className="text-nypl-red" />;
    return <BarChart3 size={16} className="text-nypl-red" />;
  };

  return (
    <div className="a2ui-card a2ui-chart-container">
      <div className="a2ui-card-header">
        <div className="a2ui-badge-icon">{getIcon()}</div>
        <div>
          <h4 className="a2ui-card-title">{data.title}</h4>
          {data.subtitle && <p className="a2ui-card-subtitle">{data.subtitle}</p>}
        </div>
      </div>
      <div className="a2ui-chart-canvas-wrapper" style={{ height: '260px', width: '100%', position: 'relative' }}>
        {chartType === 'doughnut' && <Doughnut data={chartData} options={options} />}
        {chartType === 'pie' && <Pie data={chartData} options={options} />}
        {chartType === 'line' && <Line data={chartData} options={options} />}
        {chartType === 'bar' && <Bar data={chartData} options={options} />}
      </div>
    </div>
  );
};
