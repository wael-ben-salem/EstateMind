import bcrypt from "bcryptjs";
import { PrismaClient } from "../src/generated/prisma/index.js";

const prisma = new PrismaClient({
  datasources: { db: { url: "file:C:/Users/21650/Desktop/DeepL/web/prisma/dev.db" } },
});

const hash = await bcrypt.hash("admin2026", 10);
const user = await prisma.user.upsert({
  where: { email: "admin@estatemind.tn" },
  update: { role: "admin", passwordHash: hash, name: "Admin" },
  create: { email: "admin@estatemind.tn", name: "Admin", role: "admin", passwordHash: hash },
});
console.log("Admin user ready:", user.id, user.email, user.role);
await prisma.$disconnect();
