import React from 'react';
import { BookOpen, Building2, Sparkles, MapPin, Layers, UtensilsCrossed, Trees, Compass } from 'lucide-react';

interface Props {
  onSelectPrompt: (prompt: string, command: string) => void;
}

interface StarterCategory {
  id: string;
  command: string;
  title: string;
  description: string;
  prompt: string;
  icon: React.ElementType;
  badge: string;
  tags: string[];
}

const STARTER_CATEGORIES: StarterCategory[] = [
  {
    id: 'bridge',
    command: 'nypl',
    title: 'Brooklyn Bridge & East River Construction',
    description: 'Explore 19th-century public domain stereographs and photographs documenting caissons and towers.',
    prompt: 'Show me historical photographs of the Brooklyn Bridge under construction and details from NYPL collections.',
    icon: BookOpen,
    badge: 'NYPL Digital Archives',
    tags: ['1878 Photos', 'Stereographs', 'Engineering'],
  },
  {
    id: 'subways',
    command: 'nypl',
    title: 'IRT Subway & City Hall Station (1904)',
    description: 'View archival photographic prints of the opening of the first underground rapid transit lines in Manhattan.',
    prompt: 'Tell me about the 1904 opening of the NYC subway and show me historic pictures from the NYPL digital archives.',
    icon: Layers,
    badge: 'NYPL Digital Archives',
    tags: ['1904 IRT', 'City Hall Station', 'Transit'],
  },
  {
    id: 'discovery',
    command: 'nycdata',
    title: 'NYC Open Data Catalog Discovery',
    description: 'Autonomous catalog explorer searching thousands of municipal datasets (Wi-Fi kiosks, transit, permits).',
    prompt: 'Search the NYC Open Data catalog for LinkNYC Wi-Fi kiosks and summarize their deployment status in Queens.',
    icon: Compass,
    badge: 'Dynamic Discovery',
    tags: ['Catalog Search', 'LinkNYC 5G', 'Dynamic SODA'],
  },
  {
    id: 'noise311',
    command: 'nycdata',
    title: 'NYC 311 Urban Incident Breakdown',
    description: 'Live SODA query analyzing residential noise complaints, commercial violations, and borough trends.',
    prompt: 'Query NYC 311 for recent noise complaints in Manhattan and summarize the top complaint types with stats.',
    icon: Building2,
    badge: 'NYC Open Data',
    tags: ['311 SODA', 'Manhattan', 'Breakdown Chart'],
  },
  {
    id: 'inspections',
    command: 'nycdata',
    title: 'Restaurant Health Inspections & Grades',
    description: 'Search DOHMH health inspection scores, sanitary violations, and letter grade classifications.',
    prompt: 'Find restaurant inspection scores and grades for classic delis and diners in Manhattan.',
    icon: UtensilsCrossed,
    badge: 'NYC Open Data',
    tags: ['DOHMH Grades', 'Violations', 'Health Scores'],
  },
  {
    id: 'flagships',
    command: 'nypl',
    title: 'Rose Main Reading Room & Flagship Branches',
    description: 'Locate the Stephen A. Schwarzman Building, Schomburg Center, and Lincoln Center research collections.',
    prompt: 'Where is the Rose Main Reading Room located, and what are the main NYPL research centers in Manhattan?',
    icon: MapPin,
    badge: 'NYPL Research',
    tags: ['Schwarzman Bldg', 'Schomburg', 'Lincoln Center'],
  },
  {
    id: 'trees',
    command: 'nycdata',
    title: 'NYC Street Tree Census & Forestry',
    description: 'Analyze urban tree canopy distribution, most common species, and trunk health across neighborhoods.',
    prompt: 'What are the most common street trees in New York City according to the NYC Street Tree Census?',
    icon: Trees,
    badge: 'NYC Open Data',
    tags: ['Urban Forestry', 'Species', 'Green Canopy'],
  },
];

export const StarterCanvas: React.FC<Props> = ({ onSelectPrompt }) => {
  return (
    <div className="canvas-starter-container animate-fade-in">
      {/* Hero Welcome Masthead */}
      <div className="canvas-starter-hero">
        <div className="canvas-starter-lion-badge">
          <span role="img" aria-label="NYPL Lion" style={{ fontSize: '32px' }}>🦁</span>
        </div>
        <div className="canvas-starter-hero-text">
          <div className="canvas-starter-pill">
            <Sparkles size={13} className="text-nypl-red" />
            <span>Autonomous UI & Multi-Agent Research Canvas</span>
          </div>
          <h1 className="canvas-starter-title serif-heading">
            New York Public Library & Urban Intelligence
          </h1>
          <p className="canvas-starter-subtitle">
            Enter any inquiry above to generate a custom, dynamic interactive canvas powered by Gemini 3.5 Flash Lite, 
            the NYPL Digital Collections repository, and NYC SODA municipal datasets.
          </p>
        </div>
      </div>

      {/* Starter Exploration Cards Grid */}
      <div className="canvas-starter-grid">
        {STARTER_CATEGORIES.map((cat) => {
          const Icon = cat.icon;
          return (
            <div
              key={cat.id}
              className="canvas-starter-card"
              onClick={() => onSelectPrompt(cat.prompt, cat.command)}
            >
              <div className="canvas-starter-card-top">
                <div className="canvas-starter-icon-circle">
                  <Icon size={18} className="text-nypl-red" />
                </div>
                <span className="canvas-starter-badge">{cat.badge}</span>
              </div>

              <h3 className="canvas-starter-card-title serif-heading">{cat.title}</h3>
              <p className="canvas-starter-card-desc">{cat.description}</p>

              <div className="canvas-starter-tags">
                {cat.tags.map((t, idx) => (
                  <span key={idx} className="canvas-starter-tag-pill">{t}</span>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
