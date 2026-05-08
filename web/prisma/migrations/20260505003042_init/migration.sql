-- CreateTable
CREATE TABLE "Listing" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "reference" TEXT,
    "url" TEXT,
    "source" TEXT,
    "agence" TEXT,
    "adresse" TEXT,
    "gouvernerat" TEXT,
    "delegation" TEXT,
    "ville" TEXT,
    "localite" TEXT,
    "codep" TEXT,
    "latitude" REAL,
    "longitude" REAL,
    "geo_precision" TEXT,
    "type" TEXT,
    "contrat" TEXT,
    "prix" REAL,
    "prix_original" REAL,
    "prix_m2" REAL,
    "prix_q75_contrat" REAL,
    "surface" REAL,
    "surface_original" REAL,
    "superficie_terrain" REAL,
    "pieces" INTEGER,
    "pieces_original" INTEGER,
    "etage" INTEGER,
    "etage_original" INTEGER,
    "annee_constr" INTEGER,
    "has_ascenseur" BOOLEAN,
    "has_balcon" BOOLEAN,
    "has_chaffage" BOOLEAN,
    "has_climatisation" BOOLEAN,
    "has_garage" BOOLEAN,
    "has_gardien" BOOLEAN,
    "has_jardin" BOOLEAN,
    "has_parking" BOOLEAN,
    "has_piscine" BOOLEAN,
    "has_terrasse" BOOLEAN,
    "cuisine" TEXT,
    "salle_de_bain" TEXT,
    "chauffage" TEXT,
    "climatisation" TEXT,
    "installations_sportives" TEXT,
    "bus" INTEGER,
    "railway" INTEGER,
    "ecole" INTEGER,
    "hopital" INTEGER,
    "pharmacie" INTEGER,
    "magasin" INTEGER,
    "marche" INTEGER,
    "restaurant" INTEGER,
    "standing" TEXT,
    "haut_standing" BOOLEAN,
    "bon_entourage" BOOLEAN,
    "bon_entourage_llm" TEXT,
    "tel" TEXT,
    "titre" TEXT,
    "description" TEXT,
    "desc_clean" TEXT,
    "carac_block" TEXT,
    "caracteristiques" TEXT,
    "contrat_carac" TEXT,
    "surface_carac" TEXT,
    "code_postal_carac" TEXT,
    "fonds" TEXT,
    "constructible" TEXT,
    "plein_air" TEXT,
    "service" TEXT,
    "images" TEXT,
    "other_data" TEXT,
    "date_publication" TEXT,
    "pub_year" INTEGER,
    "pub_month" INTEGER,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    "isUserCreated" BOOLEAN NOT NULL DEFAULT false,
    "ownerId" INTEGER,
    CONSTRAINT "Listing_ownerId_fkey" FOREIGN KEY ("ownerId") REFERENCES "User" ("id") ON DELETE SET NULL ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "User" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "email" TEXT NOT NULL,
    "passwordHash" TEXT,
    "name" TEXT,
    "role" TEXT NOT NULL DEFAULT 'buyer',
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CreateTable
CREATE TABLE "Account" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "userId" INTEGER NOT NULL,
    "type" TEXT NOT NULL,
    "provider" TEXT NOT NULL,
    "providerAccountId" TEXT NOT NULL,
    "refresh_token" TEXT,
    "access_token" TEXT,
    "expires_at" INTEGER,
    "token_type" TEXT,
    "scope" TEXT,
    "id_token" TEXT,
    "session_state" TEXT,
    CONSTRAINT "Account_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Session" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "sessionToken" TEXT NOT NULL,
    "userId" INTEGER NOT NULL,
    "expires" DATETIME NOT NULL,
    CONSTRAINT "Session_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "VerificationToken" (
    "identifier" TEXT NOT NULL,
    "token" TEXT NOT NULL,
    "expires" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "Favorite" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "userId" INTEGER NOT NULL,
    "listingId" INTEGER NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "Favorite_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "Favorite_listingId_fkey" FOREIGN KEY ("listingId") REFERENCES "Listing" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateIndex
CREATE INDEX "Listing_gouvernerat_idx" ON "Listing"("gouvernerat");

-- CreateIndex
CREATE INDEX "Listing_ville_idx" ON "Listing"("ville");

-- CreateIndex
CREATE INDEX "Listing_type_idx" ON "Listing"("type");

-- CreateIndex
CREATE INDEX "Listing_contrat_idx" ON "Listing"("contrat");

-- CreateIndex
CREATE INDEX "Listing_prix_idx" ON "Listing"("prix");

-- CreateIndex
CREATE INDEX "Listing_latitude_longitude_idx" ON "Listing"("latitude", "longitude");

-- CreateIndex
CREATE UNIQUE INDEX "User_email_key" ON "User"("email");

-- CreateIndex
CREATE UNIQUE INDEX "Account_provider_providerAccountId_key" ON "Account"("provider", "providerAccountId");

-- CreateIndex
CREATE UNIQUE INDEX "Session_sessionToken_key" ON "Session"("sessionToken");

-- CreateIndex
CREATE UNIQUE INDEX "VerificationToken_token_key" ON "VerificationToken"("token");

-- CreateIndex
CREATE UNIQUE INDEX "VerificationToken_identifier_token_key" ON "VerificationToken"("identifier", "token");

-- CreateIndex
CREATE UNIQUE INDEX "Favorite_userId_listingId_key" ON "Favorite"("userId", "listingId");
