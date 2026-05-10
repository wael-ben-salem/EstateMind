"use client";
import { useState } from "react";
import { ChevronLeft, ChevronRight, X, Expand, ImageOff } from "lucide-react";

const FALLBACK_PX = [29465759, 32465895, 27967576, 37284584, 14558088, 29679540];
const pxFallback = (idx: number) =>
  `https://images.pexels.com/photos/${FALLBACK_PX[idx % FALLBACK_PX.length]}/pexels-photo-${FALLBACK_PX[idx % FALLBACK_PX.length]}.jpeg?auto=compress&cs=tinysrgb&w=800&h=600`;

interface Props { images: string[]; title: string; }

export function ImageGallery({ images, title }: Props) {
  const [current, setCurrent] = useState(0);
  const [lightbox, setLightbox] = useState(false);

  const prev = () => setCurrent(i => (i - 1 + images.length) % images.length);
  const next = () => setCurrent(i => (i + 1) % images.length);

  if (images.length === 0) {
    return (
      <div className="rounded-2xl overflow-hidden flex items-center justify-center"
           style={{ height: "420px", background: "oklch(0.94 0.012 260)" }}>
        <div className="flex flex-col items-center gap-3 opacity-30">
          <ImageOff size={48} style={{ color: "var(--color-navy)" }} />
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="relative rounded-2xl overflow-hidden bg-sand" style={{ height: "420px" }}>
        <img src={images[current]} alt={title}
             onError={(e) => { e.currentTarget.src = pxFallback(current); e.currentTarget.onerror = null; }}
             className="w-full h-full object-cover" />

        {/* Nav arrows */}
        {images.length > 1 && (
          <>
            <button onClick={prev}
                    className="absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/80 backdrop-blur flex items-center justify-center shadow-md hover:bg-white transition-colors">
              <ChevronLeft size={18} style={{ color: "var(--color-navy)" }} />
            </button>
            <button onClick={next}
                    className="absolute right-14 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/80 backdrop-blur flex items-center justify-center shadow-md hover:bg-white transition-colors">
              <ChevronRight size={18} style={{ color: "var(--color-navy)" }} />
            </button>
          </>
        )}

        {/* Expand */}
        <button onClick={() => setLightbox(true)}
                className="absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/80 backdrop-blur flex items-center justify-center shadow-md hover:bg-white transition-colors">
          <Expand size={16} style={{ color: "var(--color-navy)" }} />
        </button>

        {/* Counter */}
        {images.length > 1 && (
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full text-xs font-medium"
               style={{ background: "oklch(0.10 0.035 45 / 0.65)", color: "white" }}>
            {current + 1} / {images.length}
          </div>
        )}
      </div>

      {/* Thumbnails */}
      {images.length > 1 && (
        <div className="flex gap-2 mt-3 overflow-x-auto pb-1">
          {images.map((img, i) => (
            <button key={i} onClick={() => setCurrent(i)}
                    className="flex-shrink-0 w-16 h-12 rounded-xl overflow-hidden border-2 transition-colors"
                    style={{ borderColor: i === current ? "var(--color-gold)" : "transparent" }}>
              <img src={img} alt=""
                   onError={(e) => { e.currentTarget.src = pxFallback(i); e.currentTarget.onerror = null; }}
                   className="w-full h-full object-cover" />
            </button>
          ))}
        </div>
      )}

      {/* Lightbox */}
      {lightbox && (
        <div className="fixed inset-0 z-50 flex items-center justify-center"
             style={{ background: "oklch(0.05 0.03 258 / 0.95)" }}
             onClick={() => setLightbox(false)}>
          <button onClick={() => setLightbox(false)}
                  className="absolute top-4 right-4 w-10 h-10 rounded-full bg-white/20 flex items-center justify-center text-white hover:bg-white/30 transition-colors">
            <X size={18} />
          </button>
          {images.length > 1 && (
            <>
              <button onClick={e => { e.stopPropagation(); prev(); }}
                      className="absolute left-4 w-12 h-12 rounded-full bg-white/20 flex items-center justify-center text-white hover:bg-white/30 transition-colors">
                <ChevronLeft size={22} />
              </button>
              <button onClick={e => { e.stopPropagation(); next(); }}
                      className="absolute right-4 w-12 h-12 rounded-full bg-white/20 flex items-center justify-center text-white hover:bg-white/30 transition-colors">
                <ChevronRight size={22} />
              </button>
            </>
          )}
          <img src={images[current]} alt={title}
               onError={(e) => { e.currentTarget.src = pxFallback(current); e.currentTarget.onerror = null; }}
               className="max-w-full max-h-full object-contain rounded-xl"
               style={{ maxWidth: "90vw", maxHeight: "85vh" }}
               onClick={e => e.stopPropagation()} />
        </div>
      )}
    </>
  );
}
