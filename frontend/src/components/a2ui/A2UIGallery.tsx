import React, { useState } from 'react';
import { Image as ImageIcon, ExternalLink, X, ZoomIn, Calendar, BookOpen } from 'lucide-react';
import type { PhotoGalleryData as A2UIPhotoGalleryData, PhotoItem } from '../../types/a2ui';

interface Props {
  data: A2UIPhotoGalleryData;
}

export const A2UIGallery: React.FC<Props> = ({ data }) => {
  const [selectedPhoto, setSelectedPhoto] = useState<PhotoItem | null>(null);
  const [failedImages, setFailedImages] = useState<Record<string, boolean>>({});
  const items = data.items || [];

  const handleImageError = (itemId: string) => {
    setFailedImages((prev) => ({ ...prev, [itemId]: true }));
  };

  return (
    <div className="a2ui-card a2ui-gallery-container">
      <div className="a2ui-card-header">
        <div className="a2ui-badge-icon">
          <ImageIcon size={16} className="text-nypl-red" />
        </div>
        <div>
          <h4 className="a2ui-card-title">{data.title}</h4>
          <p className="a2ui-card-subtitle">{items.length} historical item{items.length === 1 ? '' : 's'} from NYPL Digital Collections</p>
        </div>
      </div>

      <div className="a2ui-gallery-grid">
        {items.map((item, idx) => {
          const itemKey = item.id || `photo-${idx}`;
          const isFailed = failedImages[itemKey];

          return (
            <div
              key={itemKey}
              className="a2ui-gallery-card"
              onClick={() => setSelectedPhoto(item)}
            >
              <div className="a2ui-gallery-thumb-wrapper">
                {!isFailed ? (
                  <>
                    <img
                      src={item.thumbnail_url || item.image_url}
                      alt={item.title}
                      className="a2ui-gallery-img"
                      loading="lazy"
                      onError={() => handleImageError(itemKey)}
                    />
                    <div className="a2ui-gallery-overlay">
                      <ZoomIn size={20} color="#fff" />
                    </div>
                  </>
                ) : (
                  /* Archival Card Fallback if remote image is restricted */
                  <div className="a2ui-gallery-archival-fallback">
                    <div className="a2ui-fallback-lion">🦁</div>
                    <span className="a2ui-fallback-label">NYPL Archive Item</span>
                  </div>
                )}
              </div>
              <div className="a2ui-gallery-info">
                <div className="a2ui-gallery-item-title" title={item.title}>
                  {item.title}
                </div>
                {item.date && (
                  <div className="a2ui-gallery-date">
                    <Calendar size={11} />
                    <span>{item.date}</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Lightbox Modal */}
      {selectedPhoto && (
        <div className="a2ui-modal-backdrop animate-fade-in" onClick={() => setSelectedPhoto(null)}>
          <div className="a2ui-modal-content" onClick={(e) => e.stopPropagation()}>
            <button
              className="a2ui-modal-close"
              onClick={() => setSelectedPhoto(null)}
              aria-label="Close image modal"
            >
              <X size={20} />
            </button>
            <div className="a2ui-modal-image-container">
              <img
                src={selectedPhoto.image_url}
                alt={selectedPhoto.title}
                className="a2ui-modal-image"
                onError={(e) => {
                  (e.target as HTMLElement).style.display = 'none';
                }}
              />
            </div>
            <div className="a2ui-modal-details">
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
                <span className="nypl-tag-pill">NYPL Digital Collections</span>
                {selectedPhoto.date && (
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Circa {selectedPhoto.date}</span>
                )}
              </div>
              <h3 className="serif-heading" style={{ fontSize: '18px', marginBottom: '6px', color: 'var(--text-primary)' }}>
                {selectedPhoto.title}
              </h3>
              {selectedPhoto.caption && (
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '14px' }}>
                  {selectedPhoto.caption}
                </p>
              )}
              {(() => {
                if (!selectedPhoto.link) return null;
                try {
                  const parsed = new URL(selectedPhoto.link, window.location.origin);
                  if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') return null;
                  return (
                    <a
                      href={parsed.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="a2ui-btn-primary"
                      style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '13px' }}
                    >
                      <BookOpen size={14} />
                      <span>Open Item in NYPL Digital Collections</span>
                      <ExternalLink size={13} />
                    </a>
                  );
                } catch {
                  return null;
                }
              })()}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
