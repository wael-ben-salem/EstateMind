import sharp from "sharp";
import { readFileSync, writeFileSync } from "fs";

const src = "C:/Users/21650/Desktop/DeepL/Logo.png";
const dst = "public/logo-transparent.png";

const { data, info } = await sharp(src)
  .ensureAlpha()
  .raw()
  .toBuffer({ resolveWithObject: true });

const pixels = new Uint8Array(data);
const threshold = 240; // pixels brighter than this in all channels → transparent

for (let i = 0; i < pixels.length; i += 4) {
  const r = pixels[i], g = pixels[i + 1], b = pixels[i + 2];
  if (r >= threshold && g >= threshold && b >= threshold) {
    pixels[i + 3] = 0; // set alpha to 0 (transparent)
  }
}

await sharp(Buffer.from(pixels), {
  raw: { width: info.width, height: info.height, channels: 4 },
})
  .png()
  .toFile(dst);

console.log(`Done → ${dst}  (${info.width}×${info.height})`);
