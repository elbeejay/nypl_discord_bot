import React from 'react';
import { Camera, Volume2, Utensils, Trees, Landmark } from 'lucide-react';

interface Props {
  onSelectPrompt: (prompt: string, command?: string) => void;
}

const STARTER_PROMPTS = [
  {
    title: 'Historic NYPL Archives',
    subtitle: 'Browse vintage prints and photographs',
    prompt: 'Show me historical photographs of the Brooklyn Bridge under construction and Manhattan subways from NYPL digital archives.',
    command: 'nypl',
    icon: Camera,
    color: '#D41B2C',
  },
  {
    title: '311 Noise & Quality of Life',
    subtitle: 'Analyze recent neighborhood 311 complaints',
    prompt: 'What are the top 311 noise complaints in Astoria, Queens and what categories are most reported?',
    command: 'nycdata',
    icon: Volume2,
    color: '#2563EB',
  },
  {
    title: 'Restaurant Health Grades',
    subtitle: 'Look up DOHMH inspection scores',
    prompt: 'Look up the latest health inspection grades and violation details for Katz\'s Delicatessen and Shake Shack.',
    command: 'nycdata',
    icon: Utensils,
    color: '#B8860B',
  },
  {
    title: 'Urban Forestry & Trees',
    subtitle: 'Explore street tree distributions',
    prompt: 'Find street trees census data for London Planetrees and Ginkgo trees in Brooklyn and Queens.',
    command: 'nycdata',
    icon: Trees,
    color: '#10B981',
  },
  {
    title: 'Library Branches & History',
    subtitle: 'Explore flagship research centers',
    prompt: 'Tell me about the Stephen A. Schwarzman Building and Schomburg Center for Research in Black Culture.',
    command: 'nypl',
    icon: Landmark,
    color: '#8B5CF6',
  },
];

export const PromptSuggestions: React.FC<Props> = ({ onSelectPrompt }) => {
  return (
    <div className="prompt-suggestions-container animate-fade-in">
      <div className="prompt-suggestions-header">
        <h3 className="serif-heading" style={{ fontSize: '20px', color: 'var(--text-primary)', marginBottom: '4px' }}>
          Explore NYC Heritage & Civic Open Data
        </h3>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          Select a sample inquiry below or ask any custom question with dynamic A2UI visualizations.
        </p>
      </div>

      <div className="prompt-suggestions-grid">
        {STARTER_PROMPTS.map((item, idx) => {
          const Icon = item.icon;
          return (
            <button
              key={idx}
              className="prompt-suggestion-card"
              onClick={() => onSelectPrompt(item.prompt, item.command)}
            >
              <div className="prompt-card-icon-wrapper" style={{ color: item.color }}>
                <Icon size={18} />
              </div>
              <div className="prompt-card-text">
                <div className="prompt-card-title">{item.title}</div>
                <div className="prompt-card-sub">{item.subtitle}</div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
