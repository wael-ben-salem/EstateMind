-- Schéma SQL pour la base de données Location Immobilière
-- Compatible Supabase (PostgreSQL)

-- Table principale unifiée - accueille tous les types de biens
CREATE TABLE IF NOT EXISTS location_listings (
  id TEXT PRIMARY KEY,
  source_site TEXT NOT NULL,
  source_url TEXT UNIQUE,
  property_category TEXT NOT NULL CHECK (property_category IN ('appartement', 'bureaux', 'locaux_com', 'maisons', 'villas')),
  titre TEXT,
  region TEXT,
  ville TEXT,
  quartier TEXT,
  adresse TEXT,
  latitude DECIMAL(10, 7),
  longitude DECIMAL(10, 7),
  
  type_bien TEXT,
  loyer DECIMAL(12, 2),
  loyer_text TEXT,
  loyer_m2 DECIMAL(10, 2),
  surface DECIMAL(10, 2),
  surface_terrain DECIMAL(10, 2),
  
  nombre_pieces INT,
  nombre_chambres INT,
  nombre_sdb INT,
  etage TEXT,
  
  description_courte TEXT,
  description_complete TEXT,
  equipements JSONB DEFAULT '[]',
  images JSONB DEFAULT '[]',
  
  meuble BOOLEAN DEFAULT FALSE,
  charges_incluses BOOLEAN,
  caution TEXT,
  conditions_location JSONB DEFAULT '{}',
  contact_info JSONB DEFAULT '{}',
  caracteristiques JSONB DEFAULT '{}',
  informations_supplementaires JSONB DEFAULT '{}',
  
  date_scraping TIMESTAMPTZ,
  scraped_by TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index pour performances
CREATE INDEX IF NOT EXISTS idx_location_category ON location_listings(property_category);
CREATE INDEX IF NOT EXISTS idx_location_ville ON location_listings(ville);
CREATE INDEX IF NOT EXISTS idx_location_region ON location_listings(region);
CREATE INDEX IF NOT EXISTS idx_location_loyer ON location_listings(loyer);
CREATE INDEX IF NOT EXISTS idx_location_surface ON location_listings(surface);
CREATE INDEX IF NOT EXISTS idx_location_source ON location_listings(source_site);
CREATE INDEX IF NOT EXISTS idx_location_created ON location_listings(created_at);

-- Trigger pour updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_location_updated ON location_listings;
CREATE TRIGGER trigger_location_updated
  BEFORE UPDATE ON location_listings
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- RLS (Row Level Security) - optionnel pour multi-utilisateurs
-- Décommentez si chaque utilisateur ne doit voir/modifier que ses données

-- ALTER TABLE location_listings ENABLE ROW LEVEL SECURITY;

-- CREATE POLICY "Users can insert own listings"
--   ON location_listings FOR INSERT
--   WITH CHECK (scraped_by = auth.uid()::text OR scraped_by IS NULL);

-- CREATE POLICY "Users can view all listings"
--   ON location_listings FOR SELECT
--   USING (true);
